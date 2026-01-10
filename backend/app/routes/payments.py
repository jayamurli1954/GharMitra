"""
Payment Collection & Reconciliation API
Handles bill payments, receipts, reconciliation, and reminders
"""
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, or_, desc
from typing import List, Optional
from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import UUID
import io

from ..database import get_db
from ..models_db import (
    User,
    Society,
    Transaction,
    AccountCode,
    Payment,
    PaymentReminder,
    PaymentMode,
    PaymentStatus,
    MaintenanceBill,
    Flat,
    BillStatus
)
from ..schemas.payment import (
    PaymentRecordRequest,
    PaymentResponse,
    PaymentHistoryResponse,
    ReconciliationSummary,
    OverdueBillsResponse,
    OverdueBill,
    PaymentReminderRequest,
    PaymentReminderResponse,
    PaymentReceiptData
)
from ..dependencies import get_current_user
from ..models.user import UserResponse
from ..utils.audit import log_action
from ..utils.export_utils import PDFExporter

router = APIRouter(prefix="/payments", tags=["payments"])


async def generate_receipt_number(db: AsyncSession, society_id: int) -> str:
    """Generate sequential receipt voucher number: RV-0001, RV-0002, etc."""
    from app.utils.document_numbering import generate_receipt_voucher_number
    return await generate_receipt_voucher_number(db, society_id)


@router.post("", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def record_payment(
    payment_data: PaymentRecordRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Record a payment against a maintenance bill
    
    Actions:
    1. Validate bill exists and is unpaid/partially paid
    2. Create payment record
    3. Update bill payment status
    4. Create accounting transaction (Dr. Bank/Cash, Cr. Receivables)
    5. Generate receipt number
    """
    # Step 1: Get and validate bill
    result = await db.execute(
        select(MaintenanceBill, Flat, User)
        .join(Flat, MaintenanceBill.flat_id == Flat.id)
        .join(User, Flat.primary_member_id == User.id)
        .where(
            and_(
                MaintenanceBill.id == payment_data.bill_id,
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
    
    bill, flat, member = bill_data
    
    # Check if bill is already fully paid
    result = await db.execute(
        select(func.coalesce(func.sum(Payment.amount), 0))
        .where(
            and_(
                Payment.bill_id == bill.id,
                Payment.status == PaymentStatus.COMPLETED
            )
        )
    )
    total_paid = Decimal(str(result.scalar() or 0.0))
    
    remaining_amount = Decimal(str(bill.total_amount)) - total_paid
    
    if remaining_amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bill is already fully paid"
        )
    
    # Check if payment amount exceeds remaining
    payment_amount = Decimal(str(payment_data.amount))
    if payment_amount > remaining_amount + Decimal("0.01"): # Small tolerance for floating point
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment amount (₹{payment_amount}) exceeds remaining amount (₹{remaining_amount})"
        )
    
    # Step 2: Generate receipt number
    receipt_number = await generate_receipt_number(db, current_user.society_id)
    
    # Step 3: Create payment record
    is_partial = payment_data.amount < remaining_amount - 0.01
    
    new_payment = Payment(
        society_id=current_user.society_id,
        bill_id=bill.id,
        flat_id=flat.id,
        member_id=member.id,
        receipt_number=receipt_number,
        payment_date=payment_data.payment_date,
        payment_mode=PaymentMode(payment_data.payment_mode),
        amount=payment_data.amount,
        transaction_reference=payment_data.transaction_reference,
        bank_name=payment_data.bank_name,
        remarks=payment_data.remarks,
        status=PaymentStatus.COMPLETED,
        late_fee_charged=payment_data.late_fee_charged,
        is_partial_payment=is_partial,
        created_by=UUID(current_user.id),
        recorded_by=UUID(current_user.id)
    )
    
    db.add(new_payment)
    await db.flush()  # Get the ID
    
    # Step 4: Update bill status
    total_paid_now = total_paid + payment_amount
    
    if total_paid_now >= Decimal(str(bill.total_amount)) - Decimal("0.01"):
        # Fully paid
        bill.is_paid = True
        bill.status = BillStatus.PAID  # Update status to PAID
        bill.paid_amount = float(bill.total_amount)
        bill.paid_date = payment_data.payment_date
    else:
        # Partially paid
        bill.paid_amount = float(total_paid_now)
        # Status remains UNPAID for partial payments
    
    # Step 5: Create accounting transaction
    # Dr. Bank/Cash (Asset increases)
    # Cr. Accounts Receivable (Asset decreases)
    
    # Determine account based on payment mode
    if payment_data.payment_mode == 'cash':
        debit_account_code = '1010'  # Cash in Hand (corrected from 1200)
    else:
        # Get bank account code from settings
        from app.routes.transactions import get_bank_account_code_from_settings
        debit_account_code = await get_bank_account_code_from_settings(current_user.society_id, db)
        if not debit_account_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No bank account linked in settings. Please link a bank account to an account code in Settings."
            )
    
    # Get account heads
    result = await db.execute(
        select(AccountCode)
        .where(
            and_(
                AccountCode.society_id == current_user.society_id,
                or_(
                    AccountCode.code == debit_account_code,
                    AccountCode.code == '1100'  # Accounts Receivable
                )
            )
        )
    )
    accounts = {acc.code: acc for acc in result.scalars().all()}
    
    if debit_account_code not in accounts or '1100' not in accounts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Required account heads not found. Please set up chart of accounts."
        )
    
    debit_account = accounts[debit_account_code]
    credit_account = accounts['1100']
    
    # Create debit transaction (increase cash/bank)
    debit_txn = Transaction(
        society_id=current_user.society_id,
        account_code=debit_account.code,  # Corrected to account_code column
        account_name=debit_account.name,
        type='income',  # Cash/Bank increases
        amount=float(payment_amount),
        debit_amount=float(payment_amount),
        credit_amount=0.0,
        date=payment_data.payment_date,
        description=f"Payment received - {receipt_number} - {flat.flat_number}",
        payment_method=payment_data.payment_mode,
        added_by=int(current_user.id),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(debit_txn)
    
    # Update account balance
    debit_account.current_balance = float(Decimal(str(debit_account.current_balance or 0.0)) + payment_amount)
    
    # Create credit transaction (decrease receivables) - Include flat_id for sub-ledger tracking
    credit_txn = Transaction(
        society_id=current_user.society_id,
        account_code=credit_account.code,
        account_name=credit_account.name,
        type='expense',  # Receivables decrease (credit)
        amount=float(payment_amount),
        debit_amount=0.0,
        credit_amount=float(payment_amount),
        date=payment_data.payment_date,
        description=f"Payment received - {receipt_number} - Flat: {flat.flat_number}",
        payment_method=payment_data.payment_mode,
        added_by=int(current_user.id),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    # Store flat info in description for sub-ledger tracking (1100 Maintenance Dues Receivable)
    # Note: Transaction model doesn't have flat_id column, so we use description for now
    db.add(credit_txn)
    
    # Update account balance
    credit_account.current_balance = float(Decimal(str(credit_account.current_balance or 0.0)) - payment_amount)
    
    # Link payment to transaction
    new_payment.transaction_id = debit_txn.id
    
    await db.commit()
    await db.refresh(new_payment)
    
    # Log action
    await log_action(
        db=db,
        society_id=current_user.society_id,
        user_id=int(current_user.id),
        action_type="create",
        entity_type="payment",
        entity_id=str(new_payment.id),
        new_values={
            "receipt_number": receipt_number,
            "amount": payment_data.amount,
            "payment_mode": payment_data.payment_mode,
            "flat": flat.flat_number
        }
    )
    
    return PaymentResponse(
        id=new_payment.id,
        society_id=new_payment.society_id,
        bill_id=new_payment.bill_id,
        flat_id=new_payment.flat_id,
        member_id=new_payment.member_id,
        receipt_number=new_payment.receipt_number,
        payment_date=new_payment.payment_date,
        payment_mode=new_payment.payment_mode.value,
        amount=float(new_payment.amount),
        transaction_reference=new_payment.transaction_reference,
        bank_name=new_payment.bank_name,
        remarks=new_payment.remarks,
        status=new_payment.status.value,
        late_fee_charged=float(new_payment.late_fee_charged),
        is_partial_payment=new_payment.is_partial_payment,
        receipt_generated=new_payment.receipt_generated,
        receipt_file_url=new_payment.receipt_file_url,
        created_at=new_payment.created_at,
        flat_number=flat.flat_number,
        member_name=member.name,
        bill_amount=float(bill.total_amount)
    )


@router.get("/bill/{bill_id}", response_model=List[PaymentResponse])
async def get_bill_payments(
    bill_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all payments for a specific bill"""
    result = await db.execute(
        select(Payment, Flat, User)
        .join(Flat, Payment.flat_id == Flat.id)
        .join(User, Payment.member_id == User.id)
        .where(
            and_(
                Payment.bill_id == bill_id,
                Payment.society_id == current_user.society_id
            )
        )
        .order_by(desc(Payment.payment_date))
    )
    
    payments = []
    for payment, flat, member in result.all():
        payments.append(PaymentResponse(
            id=payment.id,
            society_id=payment.society_id,
            bill_id=payment.bill_id,
            flat_id=payment.flat_id,
            member_id=payment.member_id,
            receipt_number=payment.receipt_number,
            payment_date=payment.payment_date,
            payment_mode=payment.payment_mode.value,
            amount=float(payment.amount),
            transaction_reference=payment.transaction_reference,
            bank_name=payment.bank_name,
            remarks=payment.remarks,
            status=payment.status.value,
            late_fee_charged=float(payment.late_fee_charged),
            is_partial_payment=payment.is_partial_payment,
            receipt_generated=payment.receipt_generated,
            receipt_file_url=payment.receipt_file_url,
            created_at=payment.created_at,
            flat_number=flat.flat_number,
            member_name=member.name
        ))
    
    return payments


@router.get("/flat/{flat_id}/history", response_model=PaymentHistoryResponse)
async def get_flat_payment_history(
    flat_id: UUID,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get payment history for a flat"""
    query = select(Payment, Flat, User).join(
        Flat, Payment.flat_id == Flat.id
    ).join(
        User, Payment.member_id == User.id
    ).where(
        and_(
            Payment.flat_id == flat_id,
            Payment.society_id == current_user.society_id
        )
    )
    
    if start_date:
        query = query.where(Payment.payment_date >= start_date)
    if end_date:
        query = query.where(Payment.payment_date <= end_date)
    
    query = query.order_by(desc(Payment.payment_date))
    
    result = await db.execute(query)
    
    payments = []
    total_amount = 0
    payment_modes = {}
    
    for payment, flat, member in result.all():
        payments.append(PaymentResponse(
            id=payment.id,
            society_id=payment.society_id,
            bill_id=payment.bill_id,
            flat_id=payment.flat_id,
            member_id=payment.member_id,
            receipt_number=payment.receipt_number,
            payment_date=payment.payment_date,
            payment_mode=payment.payment_mode.value,
            amount=float(payment.amount),
            transaction_reference=payment.transaction_reference,
            bank_name=payment.bank_name,
            remarks=payment.remarks,
            status=payment.status.value,
            late_fee_charged=float(payment.late_fee_charged),
            is_partial_payment=payment.is_partial_payment,
            receipt_generated=payment.receipt_generated,
            receipt_file_url=payment.receipt_file_url,
            created_at=payment.created_at,
            flat_number=flat.flat_number,
            member_name=member.name
        ))
        
        total_amount += float(payment.amount)
        mode = payment.payment_mode.value
        payment_modes[mode] = payment_modes.get(mode, 0) + float(payment.amount)
    
    return PaymentHistoryResponse(
        payments=payments,
        summary={
            "total_payments": len(payments),
            "total_amount": total_amount,
            "payment_modes_breakdown": payment_modes,
            "period": {
                "start": str(start_date) if start_date else "All time",
                "end": str(end_date) if end_date else "Present"
            }
        }
    )


@router.get("/reconciliation", response_model=ReconciliationSummary)
async def get_reconciliation_summary(
    start_date: date,
    end_date: date,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get bank reconciliation summary for a period
    Shows bills generated vs payments received
    """
    # Bills generated in period
    bills_result = await db.execute(
        select(
            func.count(MaintenanceBill.id).label('count'),
            func.coalesce(func.sum(MaintenanceBill.total_amount), 0).label('amount')
        )
        .where(
            and_(
                MaintenanceBill.society_id == current_user.society_id,
                MaintenanceBill.bill_date >= start_date,
                MaintenanceBill.bill_date <= end_date
            )
        )
    )
    bills_data = bills_result.first()
    
    # Payments received in period
    payments_result = await db.execute(
        select(
            func.count(Payment.id).label('count'),
            func.coalesce(func.sum(Payment.amount), 0).label('amount')
        )
        .where(
            and_(
                Payment.society_id == current_user.society_id,
                Payment.payment_date >= start_date,
                Payment.payment_date <= end_date,
                Payment.status == PaymentStatus.COMPLETED
            )
        )
    )
    payments_data = payments_result.first()
    
    # Outstanding bills (unpaid or partially paid)
    from ..models_db import BillStatus
    outstanding_result = await db.execute(
        select(
            func.count(MaintenanceBill.id).label('count'),
            func.coalesce(func.sum(MaintenanceBill.total_amount), 0).label('amount')
        )
        .where(
            and_(
                MaintenanceBill.society_id == current_user.society_id,
                MaintenanceBill.status == BillStatus.UNPAID,
                MaintenanceBill.created_at >= start_date,
                MaintenanceBill.created_at <= end_date
            )
        )
    )
    outstanding_data = outstanding_result.first()
    
    # Overdue bills
    overdue_result = await db.execute(
        select(
            func.count(MaintenanceBill.id).label('count'),
            func.coalesce(func.sum(MaintenanceBill.total_amount), 0).label('amount')
        )
        .where(
            and_(
                MaintenanceBill.society_id == current_user.society_id,
                MaintenanceBill.status == BillStatus.UNPAID,
                MaintenanceBill.due_date < date.today()
            )
        )
    )
    overdue_data = overdue_result.first()
    
    # Payment by mode
    payment_modes_result = await db.execute(
        select(
            Payment.payment_mode,
            func.sum(Payment.amount).label('total')
        )
        .where(
            and_(
                Payment.society_id == current_user.society_id,
                Payment.payment_date >= start_date,
                Payment.payment_date <= end_date,
                Payment.status == PaymentStatus.COMPLETED
            )
        )
        .group_by(Payment.payment_mode)
    )
    
    payment_by_mode = {
        row.payment_mode.value: float(row.total)
        for row in payment_modes_result.all()
    }
    
    # Calculate collection rate
    total_bills_amount = float(bills_data.amount if bills_data else 0)
    total_payments_amount = float(payments_data.amount if payments_data else 0)
    collection_rate = (total_payments_amount / total_bills_amount * 100) if total_bills_amount > 0 else 0
    
    # Average collection days (simplified calculation)
    # TODO: Implement proper average days calculation
    average_collection_days = 15.0  # Placeholder
    
    return ReconciliationSummary(
        period_start=start_date,
        period_end=end_date,
        total_bills_generated=bills_data.count if bills_data else 0,
        total_bills_amount=total_bills_amount,
        total_payments_received=payments_data.count if payments_data else 0,
        total_payments_amount=total_payments_amount,
        total_outstanding_bills=outstanding_data.count if outstanding_data else 0,
        total_outstanding_amount=float(outstanding_data.amount if outstanding_data else 0),
        total_overdue_bills=overdue_data.count if overdue_data else 0,
        total_overdue_amount=float(overdue_data.amount if overdue_data else 0),
        payment_by_mode=payment_by_mode,
        collection_rate=collection_rate,
        average_collection_days=average_collection_days
    )


@router.get("/overdue", response_model=OverdueBillsResponse)
async def get_overdue_bills(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all overdue bills"""
    today = date.today()
    
    result = await db.execute(
        select(MaintenanceBill, Flat, User)
        .join(Flat, MaintenanceBill.flat_id == Flat.id)
        .join(User, Flat.primary_member_id == User.id)
        .where(
            and_(
                MaintenanceBill.society_id == current_user.society_id,
                MaintenanceBill.is_paid == False,
                MaintenanceBill.due_date < today
            )
        )
        .order_by(MaintenanceBill.due_date.asc())
    )
    
    overdue_bills = []
    total_amount = 0
    oldest_overdue = 0
    
    for bill, flat, member in result.all():
        days_overdue = (today - bill.due_date).days
        oldest_overdue = max(oldest_overdue, days_overdue)
        outstanding = float(bill.total_amount) - float(bill.paid_amount or 0)
        total_amount += outstanding
        
        # Get last reminder
        reminder_result = await db.execute(
            select(PaymentReminder.reminder_date)
            .where(PaymentReminder.bill_id == bill.id)
            .order_by(desc(PaymentReminder.reminder_date))
            .limit(1)
        )
        last_reminder = reminder_result.scalar_one_or_none()
        
        overdue_bills.append(OverdueBill(
            bill_id=bill.id,
            bill_number=bill.bill_number,
            flat_number=flat.flat_number,
            member_name=member.name,
            bill_date=bill.bill_date,
            due_date=bill.due_date,
            amount=outstanding,
            days_overdue=days_overdue,
            last_reminder_sent=last_reminder,
            member_phone=member.phone,
            member_email=member.email
        ))
    
    return OverdueBillsResponse(
        overdue_bills=overdue_bills,
        summary={
            "total_count": len(overdue_bills),
            "total_amount": total_amount,
            "oldest_overdue_days": oldest_overdue
        }
    )


@router.post("/reminders/send", response_model=PaymentReminderResponse)
async def send_payment_reminders(
    reminder_data: PaymentReminderRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Send payment reminders for overdue bills
    TODO: Integrate with email/SMS service
    """
    reminders_sent = 0
    failed = 0
    details = []
    
    for bill_id in reminder_data.bill_ids:
        # Get bill details
        result = await db.execute(
            select(MaintenanceBill, Flat, User)
            .join(Flat, MaintenanceBill.flat_id == Flat.id)
            .join(User, Flat.primary_member_id == User.id)
            .where(
                and_(
                    MaintenanceBill.id == bill_id,
                    MaintenanceBill.society_id == current_user.society_id
                )
            )
        )
        bill_data = result.first()
        
        if not bill_data:
            failed += 1
            details.append({
                "bill_id": str(bill_id),
                "status": "failed",
                "reason": "Bill not found"
            })
            continue
        
        bill, flat, member = bill_data
        
        days_overdue = (date.today() - bill.due_date).days
        
        # Create reminder record
        reminder = PaymentReminder(
            society_id=current_user.society_id,
            bill_id=bill.id,
            flat_id=flat.id,
            member_id=member.id,
            reminder_date=date.today(),
            reminder_type=reminder_data.reminder_type,
            days_overdue=days_overdue,
            amount_due=float(bill.total_amount) - float(bill.paid_amount or 0),
            sent=True,  # Would be False until actual delivery
            sent_at=datetime.utcnow(),
            delivery_status='pending',  # Would update based on service response
            subject=f"Payment Reminder - Bill #{bill.bill_number}",
            message=reminder_data.custom_message or f"Your maintenance bill for {flat.flat_number} is overdue by {days_overdue} days.",
            created_by=UUID(current_user.id)
        )
        
        db.add(reminder)
        reminders_sent += 1
        
        details.append({
            "bill_id": str(bill_id),
            "flat_number": flat.flat_number,
            "member_name": member.name,
            "days_overdue": days_overdue,
            "status": "sent",
            "delivery_status": "pending"
        })
    
    await db.commit()
    
    return PaymentReminderResponse(
        success=True,
        reminders_sent=reminders_sent,
        failed=failed,
        details=details
    )


@router.get("/{payment_id}/receipt/pdf")
async def download_payment_receipt(
    payment_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate and download payment receipt PDF"""
    # Get payment with related data
    result = await db.execute(
        select(Payment, MaintenanceBill, Flat, User, Society)
        .join(MaintenanceBill, Payment.bill_id == MaintenanceBill.id)
        .join(Flat, Payment.flat_id == Flat.id)
        .join(User, Payment.member_id == User.id)
        .join(Society, Payment.society_id == Society.id)
        .where(
            and_(
                Payment.id == payment_id,
                Payment.society_id == current_user.society_id
            )
        )
    )
    payment_data = result.first()
    
    if not payment_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    payment, bill, flat, member, society = payment_data
    
    # Generate PDF
    pdf_exporter = PDFExporter()
    pdf_buffer = pdf_exporter.create_payment_receipt_pdf(
        receipt_number=payment.receipt_number,
        payment_date=payment.payment_date,
        payment_mode=payment.payment_mode.value,
        amount=float(payment.amount),
        late_fee=float(payment.late_fee_charged),
        transaction_reference=payment.transaction_reference,
        bill_number=bill.bill_number,
        bill_date=bill.bill_date,
        billing_period=f"{bill.billing_month}/{bill.billing_year}",
        member_name=member.name,
        flat_number=flat.flat_number,
        society_name=society.name,
        society_address=society.address,
        maintenance_amount=float(bill.maintenance_charges or 0),
        sinking_fund=float(bill.sinking_fund or 0),
        other_charges=float(bill.other_charges or 0)
    )
    
    return Response(
        content=pdf_buffer.getvalue(),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=Receipt_{payment.receipt_number.replace('/', '_')}.pdf"
        }
    )

