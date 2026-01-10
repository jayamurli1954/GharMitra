"""
Payment Gateway API Routes
Handles online payment processing via Razorpay
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from typing import Optional, List
from datetime import datetime, timedelta
from uuid import UUID
import json
import logging

from ..database import get_db
from ..models_db import (
    User,
    Society,
    Transaction,
    AccountCode,
    OnlinePayment,
    OnlinePaymentStatus,
    PaymentGateway,
    OnlinePaymentMethod,
    PaymentLink,
    Payment,
    PaymentMode,
    PaymentStatus,
    MaintenanceBill,
    Flat
)
from ..dependencies import get_current_user
from ..models.user import UserResponse
from ..utils.audit import log_action
from ..config import settings

# Optional import - only if Razorpay is available
try:
    from ..services.razorpay_service import razorpay_service
    RAZORPAY_SERVICE_AVAILABLE = razorpay_service is not None
except ImportError:
    RAZORPAY_SERVICE_AVAILABLE = False
    razorpay_service = None

router = APIRouter(prefix="/payment-gateway", tags=["payment-gateway"])
logger = logging.getLogger(__name__)


@router.post("/create-order")
async def create_payment_order(
    bill_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a Razorpay order for a maintenance bill
    
    This is Step 1 of the payment flow:
    1. Frontend calls this endpoint
    2. Backend creates Razorpay order
    3. Frontend opens Razorpay checkout with order_id
    4. User completes payment
    5. Frontend calls verify-payment
    """
    if not settings.RAZORPAY_ENABLED or not RAZORPAY_SERVICE_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Online payment is currently unavailable. Razorpay is not configured or installed."
        )
    
    # Step 1: Get bill details
    result = await db.execute(
        select(MaintenanceBill, Flat, User, Society)
        .join(Flat, MaintenanceBill.flat_id == Flat.id)
        .join(User, Flat.primary_member_id == User.id)
        .join(Society, MaintenanceBill.society_id == Society.id)
        .where(
            and_(
                MaintenanceBill.id == bill_id,
                MaintenanceBill.society_id == current_user.society_id
            )
        )
    )
    bill_data = result.first()
    
    if not bill_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bill not found"
        )
    
    bill, flat, member, society = bill_data
    
    # Check if bill is already paid
    if bill.is_paid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This bill is already paid"
        )
    
    # Step 2: Calculate amounts
    bill_amount = float(bill.total_amount) - float(bill.paid_amount or 0)
    
    # Calculate convenience fee
    if settings.RAZORPAY_CONVENIENCE_FEE_BEARER == "member":
        convenience_fee = razorpay_service.calculate_convenience_fee(
            bill_amount,
            settings.RAZORPAY_CONVENIENCE_FEE_PERCENTAGE
        )
    elif settings.RAZORPAY_CONVENIENCE_FEE_BEARER == "shared":
        convenience_fee = razorpay_service.calculate_convenience_fee(
            bill_amount,
            settings.RAZORPAY_CONVENIENCE_FEE_PERCENTAGE / 2
        )
    else:  # society
        convenience_fee = 0.0
    
    total_amount = bill_amount + convenience_fee
    
    # Step 3: Check if order already exists and is pending
    result = await db.execute(
        select(OnlinePayment).where(
            and_(
                OnlinePayment.bill_id == bill_id,
                OnlinePayment.status.in_([
                    OnlinePaymentStatus.CREATED,
                    OnlinePaymentStatus.PENDING,
                    OnlinePaymentStatus.PROCESSING
                ])
            )
        ).order_by(desc(OnlinePayment.created_at)).limit(1)
    )
    existing_payment = result.scalar_one_or_none()
    
    if existing_payment and existing_payment.expires_at and existing_payment.expires_at > datetime.utcnow():
        # Return existing order
        return {
            "order_id": existing_payment.razorpay_order_id,
            "amount": float(existing_payment.total_amount),
            "currency": existing_payment.currency,
            "bill_id": str(bill_id),
            "bill_number": bill.bill_number,
            "bill_amount": bill_amount,
            "convenience_fee": float(existing_payment.convenience_fee),
            "total_amount": float(existing_payment.total_amount),
            "member_name": member.name,
            "member_email": member.email,
            "member_phone": member.phone,
            "society_name": society.name,
            "key_id": settings.RAZORPAY_KEY_ID
        }
    
    # Step 4: Create Razorpay order
    try:
        order = razorpay_service.create_order(
            amount=total_amount,
            receipt=f"bill_{bill_id}",
            notes={
                "bill_id": str(bill_id),
                "bill_number": bill.bill_number,
                "society_id": str(current_user.society_id),
                "flat_id": str(flat.id),
                "member_id": str(member.id),
                "bill_amount": str(bill_amount),
                "convenience_fee": str(convenience_fee)
            }
        )
    except Exception as e:
        logger.error(f"Razorpay order creation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create payment order: {str(e)}"
        )
    
    # Step 5: Save to database
    online_payment = OnlinePayment(
        society_id=current_user.society_id,
        bill_id=bill_id,
        flat_id=flat.id,
        member_id=member.id,
        gateway=PaymentGateway.RAZORPAY,
        razorpay_order_id=order['id'],
        amount=bill_amount,
        currency='INR',
        convenience_fee=convenience_fee,
        total_amount=total_amount,
        status=OnlinePaymentStatus.CREATED,
        customer_name=member.name,
        customer_email=member.email,
        customer_phone=member.phone,
        expires_at=datetime.utcnow() + timedelta(minutes=30),  # 30 min expiry
        notes={
            "razorpay_order": order
        }
    )
    
    db.add(online_payment)
    await db.commit()
    await db.refresh(online_payment)
    
    # Log action
    await log_action(
        db=db,
        society_id=current_user.society_id,
        user_id=int(current_user.id),
        action_type="create",
        entity_type="online_payment",
        entity_id=str(online_payment.id),
        new_values={
            "order_id": order['id'],
            "amount": total_amount,
            "bill_number": bill.bill_number
        }
    )
    
    # Step 6: Return order details for frontend
    return {
        "order_id": order['id'],
        "amount": total_amount,
        "currency": "INR",
        "bill_id": str(bill_id),
        "bill_number": bill.bill_number,
        "bill_amount": bill_amount,
        "convenience_fee": convenience_fee,
        "total_amount": total_amount,
        "member_name": member.name,
        "member_email": member.email,
        "member_phone": member.phone,
        "society_name": society.name,
        "key_id": settings.RAZORPAY_KEY_ID
    }


@router.post("/verify-payment")
async def verify_and_record_payment(
    razorpay_order_id: str,
    razorpay_payment_id: str,
    razorpay_signature: str,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Verify payment signature and record payment
    
    This is Step 2 of the payment flow (after user pays):
    1. Frontend receives payment success from Razorpay
    2. Frontend calls this endpoint with payment details
    3. Backend verifies signature (CRITICAL for security!)
    4. Backend records payment in system
    5. Backend updates bill status
    6. Backend creates accounting entries
    """
    # Step 1: Get online payment record
    result = await db.execute(
        select(OnlinePayment).where(
            and_(
                OnlinePayment.razorpay_order_id == razorpay_order_id,
                OnlinePayment.society_id == current_user.society_id
            )
        )
    )
    online_payment = result.scalar_one_or_none()
    
    if not online_payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment order not found"
        )
    
    # Check if already processed
    if online_payment.status == OnlinePaymentStatus.SUCCESS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment already processed"
        )
    
    # Step 2: Verify signature (CRITICAL!)
    is_valid = razorpay_service.verify_payment_signature(
        razorpay_order_id,
        razorpay_payment_id,
        razorpay_signature
    )
    
    if not is_valid:
        # Invalid signature - potential fraud!
        online_payment.status = OnlinePaymentStatus.FAILED
        online_payment.error_description = "Invalid payment signature"
        await db.commit()
        
        logger.warning(f"Invalid payment signature for order: {razorpay_order_id}")
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payment signature"
        )
    
    # Step 3: Fetch payment details from Razorpay
    try:
        payment_details = razorpay_service.fetch_payment(razorpay_payment_id)
    except Exception as e:
        logger.error(f"Failed to fetch payment details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify payment"
        )
    
    # Step 4: Update online payment record
    online_payment.razorpay_payment_id = razorpay_payment_id
    online_payment.razorpay_signature = razorpay_signature
    online_payment.status = OnlinePaymentStatus.SUCCESS
    online_payment.payment_completed_at = datetime.utcnow()
    online_payment.gateway_response = payment_details
    
    # Extract payment method
    if payment_details.get('method'):
        try:
            online_payment.payment_method = OnlinePaymentMethod(payment_details['method'])
        except:
            pass
    
    online_payment.payment_method_details = {
        "method": payment_details.get('method'),
        "bank": payment_details.get('bank'),
        "wallet": payment_details.get('wallet'),
        "vpa": payment_details.get('vpa'),
        "card_id": payment_details.get('card_id'),
        "email": payment_details.get('email'),
        "contact": payment_details.get('contact')
    }
    
    # Step 5: Record payment in our payment system
    # (Reusing existing payment recording logic)
    
    # Get bill
    result = await db.execute(
        select(MaintenanceBill, Flat).join(
            Flat, MaintenanceBill.flat_id == Flat.id
        ).where(MaintenanceBill.id == online_payment.bill_id)
    )
    bill_data = result.first()
    
    if not bill_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bill not found"
        )
    
    bill, flat = bill_data
    
    # Generate receipt number (using existing logic from payments.py)
    from ..routes.payments import generate_receipt_number
    receipt_number = await generate_receipt_number(db, current_user.society_id)
    
    # Create payment record
    payment = Payment(
        society_id=current_user.society_id,
        bill_id=bill.id,
        flat_id=flat.id,
        member_id=online_payment.member_id,
        receipt_number=receipt_number,
        payment_date=datetime.utcnow().date(),
        payment_mode=PaymentMode.ONLINE,  # Online payment
        amount=float(online_payment.amount),  # Bill amount only (not convenience fee)
        transaction_reference=razorpay_payment_id,
        remarks=f"Online payment via Razorpay. Payment ID: {razorpay_payment_id}",
        status=PaymentStatus.COMPLETED,
        late_fee_charged=0,
        is_partial_payment=False,
        created_by=online_payment.member_id,
        recorded_by=online_payment.member_id  # Self-payment
    )
    
    db.add(payment)
    await db.flush()
    
    # Link online payment to payment record
    online_payment.payment_id = payment.id
    
    # Step 6: Update bill status
    bill.is_paid = True
    bill.status = BillStatus.PAID  # Update status to PAID
    bill.paid_amount = bill.total_amount
    bill.paid_date = datetime.utcnow().date()
    
    # Step 7: Create accounting transactions
    # Dr. Bank Account (online payments go to bank)
    # Cr. Accounts Receivable
    
    result = await db.execute(
        select(AccountCode).where(
            and_(
                AccountCode.society_id == current_user.society_id,
                AccountCode.code.in_(['1210', '1100'])  # Bank, Receivables
            )
        )
    )
    accounts = {acc.code: acc for acc in result.scalars().all()}
    
    if '1210' in accounts and '1100' in accounts:
        bank_account = accounts['1210']
        receivables_account = accounts['1100']
        
        # Debit: Bank Account (asset increases)
        debit_txn = Transaction(
            society_id=current_user.society_id,
            account_head_id=bank_account.id,
            account_name=bank_account.name,
            type='income',
            amount=float(online_payment.amount),
            date=datetime.utcnow().date(),
            description=f"Online payment received - {receipt_number} - {flat.flat_number}",
            reference_type='online_payment',
            reference_id=str(online_payment.id),
            created_by_id=online_payment.member_id
        )
        db.add(debit_txn)
        bank_account.current_balance = float(bank_account.current_balance or 0) + float(online_payment.amount)
        
        # Credit: Receivables (asset decreases)
        credit_txn = Transaction(
            society_id=current_user.society_id,
            account_head_id=receivables_account.id,
            account_name=receivables_account.name,
            type='expense',
            amount=float(online_payment.amount),
            date=datetime.utcnow().date(),
            description=f"Online payment received - {receipt_number} - {flat.flat_number}",
            reference_type='online_payment',
            reference_id=str(online_payment.id),
            created_by_id=online_payment.member_id
        )
        db.add(credit_txn)
        receivables_account.current_balance = float(receivables_account.current_balance or 0) - float(online_payment.amount)
        
        payment.transaction_id = debit_txn.id
    
    await db.commit()
    await db.refresh(payment)
    await db.refresh(online_payment)
    
    # Log action
    await log_action(
        db=db,
        society_id=current_user.society_id,
        user_id=int(current_user.id),
        action_type="online_payment_success",
        entity_type="payment",
        entity_id=str(payment.id),
        new_values={
            "receipt_number": receipt_number,
            "amount": float(online_payment.amount),
            "payment_id": razorpay_payment_id,
            "method": payment_details.get('method')
        }
    )
    
    # Step 8: Return success response
    return {
        "success": True,
        "message": "Payment verified and recorded successfully",
        "payment_id": str(payment.id),
        "receipt_number": receipt_number,
        "amount": float(online_payment.amount),
        "convenience_fee": float(online_payment.convenience_fee),
        "total_paid": float(online_payment.total_amount),
        "payment_method": payment_details.get('method'),
        "razorpay_payment_id": razorpay_payment_id
    }


@router.post("/webhook")
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Razorpay Webhook Handler
    
    Handles payment status updates from Razorpay
    This is called automatically by Razorpay when payment status changes
    
    IMPORTANT: Configure this URL in Razorpay Dashboard:
    https://your-domain.com/api/payment-gateway/webhook
    """
    # Get raw body
    body = await request.body()
    body_str = body.decode('utf-8')
    
    # Verify webhook signature
    if not x_razorpay_signature:
        logger.warning("Webhook received without signature")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing signature"
        )
    
    is_valid = razorpay_service.verify_webhook_signature(body_str, x_razorpay_signature)
    
    if not is_valid:
        logger.warning("Invalid webhook signature")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid signature"
        )
    
    # Parse webhook data
    try:
        webhook_data = json.loads(body_str)
        event = webhook_data.get('event')
        payload = webhook_data.get('payload', {}).get('payment', {}).get('entity', {})
        
        logger.info(f"Webhook received: {event}")
        
        # Handle payment.captured event
        if event == 'payment.captured':
            razorpay_payment_id = payload.get('id')
            razorpay_order_id = payload.get('order_id')
            
            if not razorpay_order_id:
                return {"status": "ok", "message": "No order_id in payload"}
            
            # Get online payment record
            result = await db.execute(
                select(OnlinePayment).where(
                    OnlinePayment.razorpay_order_id == razorpay_order_id
                )
            )
            online_payment = result.scalar_one_or_none()
            
            if online_payment:
                # Mark webhook received
                online_payment.webhook_received = True
                online_payment.webhook_received_at = datetime.utcnow()
                online_payment.webhook_data = webhook_data
                
                # If not already processed, update status
                if online_payment.status != OnlinePaymentStatus.SUCCESS:
                    online_payment.status = OnlinePaymentStatus.PROCESSING
                    online_payment.razorpay_payment_id = razorpay_payment_id
                
                await db.commit()
        
        # Handle payment.failed event
        elif event == 'payment.failed':
            razorpay_order_id = payload.get('order_id')
            
            if razorpay_order_id:
                result = await db.execute(
                    select(OnlinePayment).where(
                        OnlinePayment.razorpay_order_id == razorpay_order_id
                    )
                )
                online_payment = result.scalar_one_or_none()
                
                if online_payment and online_payment.status != OnlinePaymentStatus.SUCCESS:
                    online_payment.status = OnlinePaymentStatus.FAILED
                    online_payment.error_code = payload.get('error_code')
                    online_payment.error_description = payload.get('error_description')
                    online_payment.webhook_received = True
                    online_payment.webhook_received_at = datetime.utcnow()
                    online_payment.webhook_data = webhook_data
                    
                    await db.commit()
        
        return {"status": "ok", "message": "Webhook processed"}
        
    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}")
        return {"status": "error", "message": str(e)}


@router.get("/payment-status/{online_payment_id}")
async def get_payment_status(
    online_payment_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get status of an online payment"""
    result = await db.execute(
        select(OnlinePayment).where(
            and_(
                OnlinePayment.id == online_payment_id,
                OnlinePayment.society_id == current_user.society_id
            )
        )
    )
    online_payment = result.scalar_one_or_none()
    
    if not online_payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    return {
        "id": str(online_payment.id),
        "status": online_payment.status.value,
        "amount": float(online_payment.total_amount),
        "payment_method": online_payment.payment_method.value if online_payment.payment_method else None,
        "created_at": online_payment.created_at.isoformat(),
        "completed_at": online_payment.payment_completed_at.isoformat() if online_payment.payment_completed_at else None,
        "razorpay_payment_id": online_payment.razorpay_payment_id,
        "receipt_number": online_payment.payment.receipt_number if online_payment.payment else None
    }

