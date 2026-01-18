"""Journal Entry API routes for double-entry bookkeeping"""
from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import List, Optional
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models.journal import JournalEntryCreate, JournalEntryResponse, TrialBalanceResponse, TrialBalanceItem, JournalEntryLine
from app.models.user import UserResponse
from app.models_db import JournalEntry, Transaction, AccountCode, VoucherType
from app.dependencies import get_current_user, get_current_accountant_user
from app.utils.document_numbering import generate_journal_entry_number

router = APIRouter()


@router.post("/", response_model=JournalEntryResponse, status_code=status.HTTP_201_CREATED)
async def create_journal_entry(
    entry_data: JournalEntryCreate,
    current_user: UserResponse = Depends(get_current_accountant_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a journal entry with double-entry bookkeeping validation
    
    Rules:
    - Total debits must equal total credits
    - At least 2 entries required (one debit, one credit)
    - Each line must have either debit OR credit (not both, not neither)
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Validate entries list
    if not entry_data.entries or len(entry_data.entries) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least 2 entries are required (one debit, one credit)"
        )
    
    # Validate and convert each entry to JournalEntryLine
    validated_entries = []
    for idx, entry in enumerate(entry_data.entries):
        try:
            # If it's already a dict, convert it to JournalEntryLine
            if isinstance(entry, dict):
                validated_entry = JournalEntryLine(**entry)
            else:
                # If it's already a JournalEntryLine, use it directly
                validated_entry = JournalEntryLine(
                    account_code=entry.account_code,
                    debit_amount=entry.debit_amount,
                    credit_amount=entry.credit_amount,
                    description=getattr(entry, 'description', None)
                )
            validated_entries.append(validated_entry)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid entry at index {idx}: {str(e)}"
            )
    
    # Validate each entry line
    for entry in validated_entries:
        if entry.debit_amount > 0 and entry.credit_amount > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A line cannot have both debit and credit amounts"
            )
        if entry.debit_amount == 0 and entry.credit_amount == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A line must have either debit or credit amount"
            )
    
    # Calculate totals
    total_debit = sum(Decimal(str(entry.debit_amount)) for entry in validated_entries)
    total_credit = sum(Decimal(str(entry.credit_amount)) for entry in validated_entries)
    
    # Verify balance
    if abs(total_debit - total_credit) > Decimal("0.01"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Journal entry is not balanced. Total Debit: {total_debit}, Total Credit: {total_credit}. Debit and Credit must be equal."
        )
    
    # Ensure at least one debit and one credit
    has_debit = any(entry.debit_amount > 0 for entry in validated_entries)
    has_credit = any(entry.credit_amount > 0 for entry in validated_entries)
    
    if not has_debit or not has_credit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Journal entry must have at least one debit and one credit entry"
        )
    
    # Use today's date if not provided
    today = entry_data.date if entry_data.date is not None else date.today()
    
    # Use expense_month from data, or default to current Month, Year string
    expense_month = entry_data.expense_month if entry_data.expense_month else today.strftime("%B, %Y")
    
    # Generate entry number using utility function
    entry_number = await generate_journal_entry_number(
        db=db,
        society_id=current_user.society_id,
        entry_date=today
    )
    
    # Verify account codes exist
    account_codes_to_check = {entry.account_code for entry in validated_entries}
    result = await db.execute(
        select(AccountCode).where(
            AccountCode.code.in_(account_codes_to_check),
            AccountCode.society_id == current_user.society_id
        )
    )
    existing_codes = {ac.code for ac in result.scalars().all()}
    missing_codes = account_codes_to_check - existing_codes
    
    if missing_codes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Account codes not found: {', '.join(missing_codes)}"
        )
    
    try:
        # Create journal entry
        new_entry = JournalEntry(
            society_id=current_user.society_id,
            entry_number=entry_number,
            date=today,
            expense_month=expense_month,
            description=entry_data.description,
            total_debit=float(total_debit.quantize(Decimal("0.01"))),
            total_credit=float(total_credit.quantize(Decimal("0.01"))),
            is_balanced=True,  # Already validated
            added_by=int(current_user.id),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(new_entry)
        await db.flush()  # Get the ID
        
        # Create transaction entries for each line and update account balances
        transaction_entries = []
        accounts_to_update = {}  # Track accounts to update balances
        
        for line in validated_entries:
            # Determine transaction type based on account type
            result = await db.execute(
                select(AccountCode).where(
                    AccountCode.code == line.account_code,
                    AccountCode.society_id == current_user.society_id
                )
            )
            account = result.scalar_one()
            
            # Store account for balance update (avoid duplicate queries)
            if line.account_code not in accounts_to_update:
                accounts_to_update[line.account_code] = account
            
            # Determine type: income/expense accounts affect income/expense, assets/liabilities affect balance sheet
            if account.type in ['income', 'expense']:
                txn_type = 'income' if account.type == 'income' else 'expense'
            else:
                # For assets/liabilities, use a default type
                txn_type = 'expense' if line.debit_amount > 0 else 'income'
            
            transaction = Transaction(
                society_id=current_user.society_id,
                type=txn_type,
                category=account.name,
                account_code=line.account_code,
                amount=float((Decimal(str(line.debit_amount)) or Decimal(str(line.credit_amount))).quantize(Decimal("0.01"))),
                debit_amount=float(Decimal(str(line.debit_amount)).quantize(Decimal("0.01"))),
                credit_amount=float(Decimal(str(line.credit_amount)).quantize(Decimal("0.01"))),
                description=line.description or entry_data.description,
                date=today,
                expense_month=expense_month,
                journal_entry_id=new_entry.id,
                added_by=int(current_user.id),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            transaction_entries.append(transaction)
        
        # Update account balances based on debit/credit amounts
        for line in validated_entries:
            account = accounts_to_update[line.account_code]
            
            # Update balance based on account type and debit/credit
            # Asset and Expense: Debit increases (positive), Credit decreases (negative)
            # Liability, Capital, Income: Credit increases (negative), Debit decreases (positive)
            
            current_bal = Decimal(str(account.current_balance or 0.0))
            line_debit = Decimal(str(line.debit_amount or 0.0))
            line_credit = Decimal(str(line.credit_amount or 0.0))
            
            if account.type in ['asset', 'expense']:
                # Asset/Expense accounts: debit increases balance, credit decreases
                account.current_balance = float((current_bal + line_debit - line_credit).quantize(Decimal("0.01")))
            else:  # liability, capital, income
                # Liability/Capital/Income accounts: credit increases (negative balance), debit decreases
                account.current_balance = float((current_bal + line_debit - line_credit).quantize(Decimal("0.01")))
            
            db.add(account)  # Mark account for update
        
        db.add_all(transaction_entries)
        await db.commit()
        await db.refresh(new_entry)
        
        logger.info(f"Created journal entry {entry_number} with {len(transaction_entries)} transactions")
        
        # Get transaction entries for response
        result = await db.execute(
            select(Transaction).where(Transaction.journal_entry_id == new_entry.id)
        )
        entries = result.scalars().all()
        
        return JournalEntryResponse(
            id=str(new_entry.id),
            entry_number=new_entry.entry_number,
            date=new_entry.date,
            expense_month=new_entry.expense_month,
            description=new_entry.description,
            total_debit=new_entry.total_debit,
            total_credit=new_entry.total_credit,
            is_balanced=new_entry.is_balanced,
            added_by=str(new_entry.added_by),
            created_at=new_entry.created_at,
            updated_at=new_entry.updated_at,
            entries=[
                {
                    "id": str(t.id),
                    "account_code": t.account_code,
                    "debit_amount": t.debit_amount,
                    "credit_amount": t.credit_amount,
                    "description": t.description,
                }
                for t in entries
            ]
        )
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating journal entry: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create journal entry: {str(e)}"
        )


@router.get("/", response_model=List[JournalEntryResponse])
async def list_journal_entries(
    from_date: Optional[date] = Query(None, description="Start date"),
    to_date: Optional[date] = Query(None, description="End date"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all journal entries (filtered by date range if provided)"""
    query = select(JournalEntry).where(JournalEntry.society_id == current_user.society_id)
    
    if from_date:
        query = query.where(JournalEntry.date >= from_date)
    if to_date:
        query = query.where(JournalEntry.date <= to_date)
    
    query = query.order_by(JournalEntry.date.desc(), JournalEntry.entry_number.desc())
    
    result = await db.execute(query)
    entries = result.scalars().all()
    
    response_list = []
    for entry in entries:
        # Get transaction entries
        result = await db.execute(
            select(Transaction).where(Transaction.journal_entry_id == entry.id)
        )
        transactions = result.scalars().all()
        
        response_list.append(JournalEntryResponse(
            id=str(entry.id),
            entry_number=entry.entry_number,
            date=entry.date,
            expense_month=entry.expense_month,
            description=entry.description,
            total_debit=entry.total_debit,
            total_credit=entry.total_credit,
            is_balanced=entry.is_balanced,
            added_by=str(entry.added_by),
            created_at=entry.created_at,
            updated_at=entry.updated_at,
            entries=[
                {
                    "id": str(t.id),
                    "account_code": t.account_code,
                    "debit_amount": t.debit_amount,
                    "credit_amount": t.credit_amount,
                    "description": t.description,
                }
                for t in transactions
            ]
        ))
    
    return response_list


@router.get("/{entry_id}", response_model=JournalEntryResponse)
async def get_journal_entry(
    entry_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific journal entry"""
    try:
        entry_id_int = int(entry_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid journal entry ID"
        )
    
    result = await db.execute(
        select(JournalEntry).where(
            JournalEntry.id == entry_id_int,
            JournalEntry.society_id == current_user.society_id
        )
    )
    entry = result.scalar_one_or_none()
    
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Journal entry not found"
        )
    
    # Get transaction entries
    result = await db.execute(
        select(Transaction).where(Transaction.journal_entry_id == entry.id)
    )
    transactions = result.scalars().all()
    
    return JournalEntryResponse(
        id=str(entry.id),
        entry_number=entry.entry_number,
        date=entry.date,
        expense_month=entry.expense_month,
        description=entry.description,
        total_debit=entry.total_debit,
        total_credit=entry.total_credit,
        is_balanced=entry.is_balanced,
        added_by=str(entry.added_by),
        created_at=entry.created_at,
        updated_at=entry.updated_at,
        entries=[
            {
                "id": str(t.id),
                "account_code": t.account_code,
                "debit_amount": t.debit_amount,
                "credit_amount": t.credit_amount,
                "description": t.description,
            }
            for t in transactions
        ]
    )


@router.post("/{entry_id}/reverse", response_model=JournalEntryResponse)
async def reverse_journal_entry(
    entry_id: int,
    reason: Optional[str] = Query(None, description="Reason for reversal"),
    current_user: UserResponse = Depends(get_current_accountant_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Reverse a journal entry by creating a new one with opposite debits/credits.
    Deletion is not allowed to maintain an audit trail.
    """
    # 1. Fetch original entry
    result = await db.execute(
        select(JournalEntry).where(
            JournalEntry.id == entry_id,
            JournalEntry.society_id == current_user.society_id
        )
    )
    original = result.scalar_one_or_none()
    if not original:
        raise HTTPException(status_code=404, detail="Original journal entry not found")

    # 2. Get its transactions
    result = await db.execute(
        select(Transaction).where(Transaction.journal_entry_id == original.id)
    )
    original_txns = result.scalars().all()

    # 3. Create reversal entry
    reversal_date = date.today()
    
    # Custom Numbering: Append "-R" to original number
    base_num = original.entry_number
    # Remove existing -R suffix if present to avoid -R-R
    if base_num.endswith("-R"):
        base_num = base_num[:-2]
    
    candidate_num = f"{base_num}-R"
    
    # Check for existence of candidate_num (and increment if needed: -R2, -R3...)
    # We do a simple loop to find a free suffix
    suffix_idx = 1
    while True:
        entry_check = await db.execute(
            select(JournalEntry).where(
                JournalEntry.entry_number == candidate_num,
                JournalEntry.society_id == current_user.society_id
            )
        )
        if not entry_check.scalar_one_or_none():
            break
        # If exists, try next index
        suffix_idx += 1
        candidate_num = f"{base_num}-R{suffix_idx}"
    
    entry_number = candidate_num
    
    desc_prefix = f"REVERSAL of {original.entry_number}"
    if reason:
        full_description = f"{desc_prefix}: {reason} (Original: {original.description})"
    else:
        full_description = f"{desc_prefix}: {original.description}"

    new_entry = JournalEntry(
        society_id=current_user.society_id,
        entry_number=entry_number,
        date=reversal_date,
        expense_month=original.expense_month,
        description=full_description,
        total_debit=original.total_credit,
        total_credit=original.total_debit,
        is_balanced=original.is_balanced,
        voucher_type=VoucherType.JOURNAL,
        original_entry_id=original.id,
        added_by=int(current_user.id),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(new_entry)
    await db.flush()

    # Mark original as reversed
    original.is_reversed = True
    original.reversal_entry_id = new_entry.id
    db.add(original)

    # 4. Create reversed transactions and update balances
    new_txns = []
    for t in original_txns:
        # Swap debit and credit
        new_debit = t.credit_amount
        new_credit = t.debit_amount
        
        # Fetch account to update balance
        result_acc = await db.execute(
            select(AccountCode).where(
                AccountCode.code == t.account_code,
                AccountCode.society_id == current_user.society_id
            )
        )
        account = result_acc.scalar_one()
        
        # Update balance
        current_bal = Decimal(str(account.current_balance or 0.0))
        account.current_balance = float((current_bal + Decimal(str(new_debit)) - Decimal(str(new_credit))).quantize(Decimal("0.01")))
        db.add(account)
        
        # Reversal txn type (opposite of original)
        txn_type = 'expense' if new_debit > 0 else 'income'
        
        new_txn = Transaction(
            society_id=current_user.society_id,
            type=txn_type,
            category=account.name,
            account_code=t.account_code,
            amount=t.amount,
            debit_amount=new_debit,
            credit_amount=new_credit,
            description=f"REVERSAL: {t.description}",
            date=today,
            expense_month=t.expense_month,
            journal_entry_id=new_entry.id,
            added_by=int(current_user.id),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        new_txns.append(new_txn)
        
        # Mark original transaction as reversed
        t.is_reversed = True
        db.add(t)
    
    db.add_all(new_txns)
    await db.commit()
    await db.refresh(new_entry)

    # Return as response
    return JournalEntryResponse(
        id=str(new_entry.id),
        entry_number=new_entry.entry_number,
        date=new_entry.date,
        expense_month=new_entry.expense_month,
        description=new_entry.description,
        total_debit=new_entry.total_debit,
        total_credit=new_entry.total_credit,
        is_balanced=new_entry.is_balanced,
        added_by=str(new_entry.added_by),
        created_at=new_entry.created_at,
        updated_at=new_entry.updated_at,
        entries=[
            {
                "id": str(nt.id),
                "account_code": nt.account_code,
                "debit_amount": nt.debit_amount,
                "credit_amount": nt.credit_amount,
                "description": nt.description,
            }
            for nt in new_txns
        ]
    )
