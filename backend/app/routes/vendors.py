from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from ..database import get_db
from ..models_db import Vendor, Transaction, TransactionType, AccountCode, AccountType
from ..dependencies import get_current_user, get_current_admin_user
from ..models.user import UserResponse
from ..utils.audit import log_action

router = APIRouter(prefix="/vendors", tags=["vendors"])

# Schemas
class VendorBase(BaseModel):
    name: str
    category: Optional[str] = None
    contact_person: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    tax_id: Optional[str] = None
    opening_balance: Optional[float] = 0.0

class VendorCreate(VendorBase):
    pass

class VendorUpdate(VendorBase):
    pass

class VendorResponse(VendorBase):
    id: int
    current_balance: float
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

@router.get("/", response_model=List[VendorResponse])
async def list_vendors(
    category: Optional[str] = None,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(Vendor).where(Vendor.society_id == current_user.society_id)
    if category:
        query = query.where(Vendor.category == category)
    
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/", response_model=VendorResponse, status_code=status.HTTP_201_CREATED)
async def create_vendor(
    vendor: VendorCreate,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    new_vendor = Vendor(
        society_id=current_user.society_id,
        **vendor.dict(exclude_unset=True),
        current_balance=vendor.opening_balance or 0.0
    )
    db.add(new_vendor)
    await db.commit()
    await db.refresh(new_vendor)
    
    await log_action(
        db=db,
        society_id=current_user.society_id,
        user_id=int(current_user.id),
        action_type="create",
        entity_type="vendor",
        entity_id=new_vendor.id,
        new_values=vendor.dict()
    )
    return new_vendor

@router.get("/{vendor_id}/ledger")
async def get_vendor_ledger(
    vendor_id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get Vendor Ledger (Bill vs Payments)
    """
    vendor_res = await db.execute(select(Vendor).where(Vendor.id == vendor_id))
    vendor = vendor_res.scalar_one_or_none()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    # Get Transactions linked to this vendor
    # Vendor Bill (Expense): Credit AP (2100) -> Credit Vendor Ledger
    # Vendor Payment: Debit AP (2100) -> Debit Vendor Ledger
    
    tx_res = await db.execute(
        select(Transaction).where(
            and_(
                Transaction.vendor_id == vendor_id,
                Transaction.society_id == current_user.society_id
            )
        ).order_by(Transaction.date)
    )
    transactions = tx_res.scalars().all()
    
    ledger = []
    balance = vendor.opening_balance
    
    # Add OB
    ledger.append({
        "date": vendor.created_at.date(), # Approximate
        "description": "Opening Balance",
        "type": "OB",
        "debit": 0,
        "credit": 0,
        "balance": balance
    })
    
    total_debit = 0
    total_credit = 0

    for tx in transactions:
        # Logic: 
        # If Expense (Bill Received): We OWE more. Credit Vendor.
        # If Payment/Liability Clearance: We OWE less. Debit Vendor.
        
        # In current design:
        # Expenses are 'debit' to Expense Account, 'credit' to AP/Bank.
        # If credited to AP, it increases Vendor Balance (Credit).
        
        # Simplified:
        # If Transaction Type 'expense' AND linked to 'AP' (or just Bill Entry): Credit
        # If Transaction linked to 'Bank/Cash' (Payment): Debit
        
        # However, Transaction model stores 'amount'.
        # We need to look at 'credit_amount' vs 'debit_amount' on the AP side?
        # NO, Transaction row usually represents the PRIMARY leg.
        # Let's trust 'type':
        # Expense Entry -> Vendor Bill -> Credit Vendor (Payable increases)
        # Expense Payment? No, that clears AP.
        
        # Let's assume:
        # 1. Vendor Bill Entry: Type=Expense, Account=ExpenseHead, Credit=AP(2100).
        # We need to capture this.
        
        # 2. Payment to Vendor: Type=Expense (or Liability), Account=AP(2100), Credit=Bank.
        
        is_bill = tx.type == TransactionType.EXPENSE and tx.account_code != '2100' 
        # (It's a bill against an expense head, e.g. Water Charges)
        
        is_payment = tx.account_code == '2100' or (tx.category and 'Payment' in tx.category)
        
        dr = 0
        cr = 0
        
        if is_bill:
            # Bill Received. Credit Vendor.
            cr = tx.amount
            balance += cr
        else:
            # Payment Made. Debit Vendor.
            dr = tx.amount
            balance -= dr
            
        total_debit += dr
        total_credit += cr
        
        ledger.append({
            "date": tx.date,
            "description": tx.description,
            "type": "BILL" if is_bill else "PAYMENT",
            "debit": dr,
            "credit": cr,
            "balance": balance
        })
        
    return {
        "vendor": vendor.name,
        "entries": ledger,
        "closing_balance": balance,
        "total_bill_amount": total_credit,
        "total_paid_amount": total_debit
    }

@router.post("/bill")
async def record_vendor_bill(
    vendor_id: int,
    amount: float,
    expense_head_code: str, # e.g., 5110 Water
    description: str,
    bill_date: str,
    bill_number: Optional[str] = None,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Record a Vendor Bill (Journal Entry)
    Dr. Expense Account (e.g., Water Transaction)
    Cr. Accounts Payable (2100)
    Link to Vendor
    """
    # 1. Get Vendor
    vendor = await db.get(Vendor, vendor_id)
    if not vendor: raise HTTPException(404, "Vendor not found")
    
    # 2. Get Expense Head
    exp_ac = await db.execute(select(AccountCode).where(AccountCode.code == expense_head_code))
    exp_head = exp_ac.scalar_one_or_none()
    if not exp_head: raise HTTPException(404, "Expense Head not found")
    
    # 3. Get/Create AP Account (2100)
    ap_res = await db.execute(select(AccountCode).where(AccountCode.code == '2100'))
    ap_ac = ap_res.scalar_one_or_none()
    if not ap_ac:
        ap_ac = AccountCode(
            society_id=current_user.society_id,
            code="2100", 
            name="Accounts Payable", 
            type=AccountType.LIABILITY,
            current_balance=0.0
        )
        db.add(ap_ac)
        await db.flush()
        
    # 4. Create Transaction (The Expense Leg)
    # This records the expense in the system so report shows "Water Charges".
    # Payment Method = 'credit' (Accounts Payable)
    
    from datetime import datetime
    date_obj = datetime.strptime(bill_date, '%Y-%m-%d').date()
    
    # Document Number?
    doc_num = f"BILL-{vendor_id}-{datetime.now().strftime('%Y%m%d%H%M')}"
    
    tx = Transaction(
        society_id=current_user.society_id,
        document_number=doc_num,
        type=TransactionType.EXPENSE,
        category=exp_head.name, # "Water Charges"
        account_code=expense_head_code,
        amount=amount,
        debit_amount=amount, # Expense Dr
        credit_amount=0.0,
        description=f"Bill from {vendor.name}: {description}",
        date=date_obj,
        added_by=int(current_user.id),
        vendor_id=vendor_id,
        payment_method='credit'
    )
    db.add(tx)
    
    # Update Balances
    # 1. Expense Head Dr
    exp_head.current_balance += amount # Debit increases expense
    
    # 2. AP Account Cr
    ap_ac.current_balance += amount # Credit increases Liability
    
    # 3. Vendor Balance Cr
    vendor.current_balance += amount
    
    await db.commit()
    return {"message": "Bill Recorded", "vendor_balance": vendor.current_balance}
