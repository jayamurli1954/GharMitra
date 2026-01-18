"""Transactions API routes"""
from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import List, Optional
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete, and_

from app.database import get_db
from app.models.transaction import (
    TransactionCreate, 
    TransactionUpdate, 
    TransactionResponse,
    ReceiptCreate,
    PaymentCreate
)
from app.models.user import UserResponse
from app.models_db import (
    Transaction, 
    AccountCode, 
    SocietySettings, 
    JournalEntry, 
    Society, 
    VoucherType, 
    TransactionType,
    MaintenanceBill,
    Payment,
    BillStatus,
    PaymentMode,
    PaymentStatus,
    Member,
    Flat
)
from app.dependencies import get_current_user, get_current_admin_user
from app.utils.audit import log_action
import html
from app.utils.document_numbering import (
    generate_transaction_document_number, 
    generate_journal_entry_number,
    generate_receipt_voucher_number,
    generate_payment_voucher_number
)
from app.utils.permissions import check_permission
from fastapi import Request
from fastapi.responses import StreamingResponse
from app.utils.export_utils import PDFExporter

router = APIRouter()


async def get_bank_account_code_from_settings(society_id: int, db: AsyncSession) -> Optional[str]:
    """
    Get the bank account code from society settings.
    Returns the account_code of the primary bank account, or the first bank account if no primary is set.
    Returns None if no bank accounts are configured or linked.
    """
    result = await db.execute(
        select(SocietySettings).where(SocietySettings.society_id == society_id)
    )
    settings = result.scalar_one_or_none()
    
    if not settings or not settings.bank_accounts:
        return None
    
    # Parse bank_accounts (stored as JSON string or list)
    bank_accounts = settings.bank_accounts
    if isinstance(bank_accounts, str):
        try:
            import json
            bank_accounts = json.loads(bank_accounts)
        except json.JSONDecodeError:
            return None
    
    if not isinstance(bank_accounts, list) or len(bank_accounts) == 0:
        return None
    
    # Find primary bank account first
    for account in bank_accounts:
        if isinstance(account, dict) and account.get('is_primary') and account.get('account_code'):
            return account.get('account_code')
    
    # If no primary, return first bank account with account_code
    for account in bank_accounts:
        if isinstance(account, dict) and account.get('account_code'):
            return account.get('account_code')
    
    return None


@router.get("/", response_model=List[TransactionResponse])
async def list_transactions(
    type: Optional[str] = Query(None, description="Filter by type: income or expense"),
    from_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    to_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    account_code: Optional[str] = Query(None, description="Filter by account code"),
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: Optional[int] = Query(100, ge=1, le=1000, description="Maximum number of results"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all transactions with optional filters (filtered by user's society)"""
    # PRD: Filter by society_id for multi-tenancy
    query = select(Transaction).where(Transaction.society_id == current_user.society_id).order_by(Transaction.date.desc())

    if type:
        if type not in ["income", "expense"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Type must be 'income' or 'expense'"
            )
        query = query.where(Transaction.type == type)

    if from_date:
        query = query.where(Transaction.date >= from_date)

    if to_date:
        query = query.where(Transaction.date <= to_date)

    if account_code:
        query = query.where(Transaction.account_code == account_code)

    if category:
        query = query.where(Transaction.category == category)

    query = query.limit(limit)

    # Get transactions with journal entry information for voucher numbers
    from sqlalchemy.orm import selectinload
    query = query.options(selectinload(Transaction.journal_entry))
    result = await db.execute(query)
    transactions = result.scalars().all()

    return [
        TransactionResponse(
            id=str(transaction.id),
            document_number=transaction.document_number,
            voucher_number=transaction.journal_entry.entry_number if transaction.journal_entry else None,
            type=transaction.type.value if hasattr(transaction.type, 'value') else transaction.type,
            category=transaction.category,
            description=transaction.description,
            amount=transaction.amount,
            quantity=getattr(transaction, 'quantity', None),
            unit_price=getattr(transaction, 'unit_price', None),
            date=transaction.date,
            expense_month=transaction.expense_month,
            journal_entry_id=transaction.journal_entry_id,
            account_code=transaction.account_code,
            added_by=str(transaction.added_by),
            created_at=transaction.created_at,
            updated_at=transaction.updated_at
        )
        for transaction in transactions
    ]


@router.post("/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    transaction_data: TransactionCreate,
    request: Request,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new transaction (automatically assigned to user's society)"""
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Received transaction data: {transaction_data.model_dump()}")
    # Check permission - auditors cannot create transactions
    user_id_int = int(current_user.id)
    has_permission = await check_permission(
        user_id=user_id_int,
        permission_code="transactions.create",
        db=db
    )
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to create transactions. Auditors can only view transactions."
        )
    
    # Parse transaction date from string format
    transaction_date = date.today()
    if transaction_data.date:
        # Parse date string (could be YYYY-MM-DD or DD/MM/YYYY)
        try:
            # Try YYYY-MM-DD first
            transaction_date = datetime.strptime(transaction_data.date, '%Y-%m-%d').date()
        except ValueError:
            # Try DD/MM/YYYY
            try:
                transaction_date = datetime.strptime(transaction_data.date, '%d/%m/%Y').date()
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid date format. Use YYYY-MM-DD or DD/MM/YYYY"
                )
    
    # Use expense_month from data, or default to current Month, Year string
    expense_month = transaction_data.expense_month if transaction_data.expense_month else transaction_date.strftime("%B, %Y")

    # Validate transaction date against date lock settings
    if transaction_data.date:
        # Get society settings for date lock configuration
        settings_result = await db.execute(
            select(SocietySettings).where(
                SocietySettings.society_id == current_user.society_id
            )
        )
        settings = settings_result.scalar_one_or_none()
        
        # Default: date lock enabled, allow current month ± 1 month
        date_lock_enabled = settings.transaction_date_lock_enabled if settings else True
        date_lock_months = settings.transaction_date_lock_months if settings else 1
        
        if date_lock_enabled:
            today = date.today()
            # Calculate allowed date range
            from datetime import timedelta
            from calendar import monthrange
            
            # Get first day of current month
            first_day_current = date(today.year, today.month, 1)
            # Get last day of current month
            last_day_current = date(today.year, today.month, monthrange(today.year, today.month)[1])
            
            # Calculate allowed range: current month ± date_lock_months
            if date_lock_months > 0:
                # Calculate previous month (date_lock_months months back)
                prev_year = today.year
                prev_month = today.month - date_lock_months
                while prev_month <= 0:
                    prev_month += 12
                    prev_year -= 1
                first_day_prev = date(prev_year, prev_month, 1)
                
                # Calculate next month (date_lock_months months forward)
                next_year = today.year
                next_month = today.month + date_lock_months
                while next_month > 12:
                    next_month -= 12
                    next_year += 1
                last_day_next = date(next_year, next_month, monthrange(next_year, next_month)[1])
                
                # Check if transaction date is within allowed range
                if transaction_date < first_day_prev or transaction_date > last_day_next:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Transaction date must be within current month ± {date_lock_months} month(s). Allowed range: {first_day_prev.strftime('%d/%m/%Y')} to {last_day_next.strftime('%d/%m/%Y')}"
                    )
            else:
                # If date_lock_months is 0, only allow current month
                if transaction_date < first_day_current or transaction_date > last_day_current:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Transaction date must be within current month. Allowed range: {first_day_current.strftime('%d/%m/%Y')} to {last_day_current.strftime('%d/%m/%Y')}"
                    )
    
    # PRD: Filter account code by society_id for multi-tenancy
    if transaction_data.account_code:
        result = await db.execute(
            select(AccountCode).where(
                AccountCode.code == transaction_data.account_code,
                AccountCode.society_id == current_user.society_id
            )
        )
        account_code_obj = result.scalar_one_or_none()
        if not account_code_obj:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Account code {transaction_data.account_code} not found"
            )

    # Convert current_user.id (string) to integer for database
    try:
        added_by_user_id = int(current_user.id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID"
        )

    # Determine debit/credit for the expense/income account
    debit_amount = transaction_data.debit_amount if transaction_data.debit_amount is not None else 0.0
    credit_amount = transaction_data.credit_amount if transaction_data.credit_amount is not None else 0.0
    
    # If debit/credit not provided, infer from transaction type
    if debit_amount == 0 and credit_amount == 0:
        if transaction_data.account_code:
            result = await db.execute(
                select(AccountCode).where(
                    AccountCode.code == transaction_data.account_code,
                    AccountCode.society_id == current_user.society_id
                )
            )
            account = result.scalar_one_or_none()
            if account:
                # For income accounts: credit (income increases credit)
                # For expense accounts: debit (expense increases debit)
                # For asset accounts: debit (asset increases debit)
                # For liability accounts: credit (liability increases credit)
                if account.type == 'income':
                    credit_amount = transaction_data.amount
                elif account.type == 'expense':
                    debit_amount = transaction_data.amount
                elif account.type == 'asset':
                    debit_amount = transaction_data.amount
                elif account.type == 'liability':
                    credit_amount = transaction_data.amount
                else:
                    # Default: income = credit, expense = debit
                    if transaction_data.type == 'income':
                        credit_amount = transaction_data.amount
                    else:
                        debit_amount = transaction_data.amount
            else:
                # Default based on transaction type
                if transaction_data.type == 'income':
                    credit_amount = transaction_data.amount
                else:
                    debit_amount = transaction_data.amount
        else:
            # Default based on transaction type
            if transaction_data.type == 'income':
                credit_amount = transaction_data.amount
            else:
                debit_amount = transaction_data.amount
    
    # Determine the second leg of the transaction (cash/bank account)
    # This is required for proper double-entry bookkeeping
    second_account_code = None
    second_debit_amount = 0.0
    second_credit_amount = 0.0
    
    if transaction_data.payment_method == 'cash':
        second_account_code = '1010'  # Cash in Hand
        if transaction_data.type == 'expense':
            # Expense paid by cash: Debit Expense, Credit Cash
            second_credit_amount = transaction_data.amount
        else:  # income
            # Income received by cash: Debit Cash, Credit Income
            second_debit_amount = transaction_data.amount
    elif transaction_data.payment_method == 'bank':
        # Get bank account code
        second_account_code = transaction_data.bank_account_code
        if not second_account_code:
            second_account_code = await get_bank_account_code_from_settings(current_user.society_id, db)
        if not second_account_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No bank account linked in settings. Please link a bank account to an account code in Settings."
            )
        if transaction_data.type == 'expense':
            # Expense paid by bank: Debit Expense, Credit Bank
            second_credit_amount = transaction_data.amount
        else:  # income
            # Income received by bank: Debit Bank, Credit Income
            second_debit_amount = transaction_data.amount
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment method must be 'cash' or 'bank' for proper double-entry bookkeeping"
        )
    
    # CRITICAL VALIDATION: Verify double-entry principle - Total Debit MUST equal Total Credit
    total_debit = debit_amount + second_debit_amount
    total_credit = credit_amount + second_credit_amount
    
    if abs(total_debit - total_credit) > 0.01:  # Allow small floating point differences
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Double-entry validation failed: Total Debit (₹{total_debit:.2f}) must equal Total Credit (₹{total_credit:.2f}). "
                   f"Difference: ₹{abs(total_debit - total_credit):.2f}. "
                   f"Transaction cannot be posted. Please ensure both legs of the transaction are properly recorded."
        )
    
    # Verify both accounts exist
    if transaction_data.account_code:
        result = await db.execute(
            select(AccountCode).where(
                AccountCode.code == transaction_data.account_code,
                AccountCode.society_id == current_user.society_id
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Account code {transaction_data.account_code} not found"
            )
    
    result = await db.execute(
        select(AccountCode).where(
            AccountCode.code == second_account_code,
            AccountCode.society_id == current_user.society_id
        )
    )
    second_account = result.scalar_one_or_none()
    if not second_account:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Account code {second_account_code} not found"
        )
    
    # Generate ONE voucher number for Quick Entry (both transactions reference the same QV number)
    qv_number = await generate_transaction_document_number(
        db=db,
        society_id=current_user.society_id,
        transaction_date=transaction_date,
        payment_method=transaction_data.payment_method
    )
    
    # Create a Journal Entry to group these two transactions (for audit and reversal support)
    # Use the QV number as the journal entry number for Quick Entry
    journal_entry = JournalEntry(
        society_id=current_user.society_id,
        entry_number=qv_number,  # Use QV number as JV number for Quick Entry
        date=transaction_date,
        expense_month=expense_month,
        description=transaction_data.description,
        total_debit=transaction_data.amount,
        total_credit=transaction_data.amount,
        is_balanced=True,
        added_by=added_by_user_id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(journal_entry)
    await db.flush()

    # Create BOTH transaction records for proper double-entry bookkeeping
    # Both transactions reference the same QV number (no individual document numbers)
    # First transaction: Expense/Income account
    new_transaction = Transaction(
        society_id=current_user.society_id,
        document_number=None,  # No individual document number - references the QV/JV number
        type=transaction_data.type,
        category=transaction_data.category,
        description=transaction_data.description,
        amount=transaction_data.amount,
        quantity=transaction_data.quantity,
        unit_price=transaction_data.unit_price,
        date=transaction_date,
        expense_month=expense_month,
        account_code=transaction_data.account_code,
        debit_amount=debit_amount,
        credit_amount=credit_amount,
        payment_method=transaction_data.payment_method,
        journal_entry_id=journal_entry.id,
        added_by=added_by_user_id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    # Second transaction: Cash/Bank account
    second_transaction = Transaction(
        society_id=current_user.society_id,
        document_number=None,  # No individual document number - references the QV/JV number
        type=transaction_data.type,
        category=transaction_data.category,
        description=f"{transaction_data.description} ({'Cash' if transaction_data.payment_method == 'cash' else 'Bank'})",
        amount=transaction_data.amount,
        date=transaction_date,
        expense_month=expense_month,
        account_code=second_account_code,
        debit_amount=second_debit_amount,
        credit_amount=second_credit_amount,
        payment_method=transaction_data.payment_method,
        journal_entry_id=journal_entry.id,
        added_by=added_by_user_id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    # Add both transactions to session
    db.add(new_transaction)
    db.add(second_transaction)
    
    # Commit both transactions together (atomic operation)
    try:
        await db.commit()
        await db.refresh(new_transaction)
        await db.refresh(second_transaction)
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating transaction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create transaction: {str(e)}"
        )
    
    # Update account balances for double-entry bookkeeping (AFTER both transactions are saved)
    # Update the expense/income account balance
    transaction_amount = Decimal(str(transaction_data.amount))
    
    if transaction_data.account_code:
        account_result = await db.execute(
            select(AccountCode).where(
                AccountCode.code == transaction_data.account_code,
                AccountCode.society_id == current_user.society_id
            )
        )
        account = account_result.scalar_one_or_none()
        if account:
            current_bal = Decimal(str(account.current_balance or 0.0))
            if transaction_data.type == 'expense':
                # Debit increases expense (debit balance)
                account.current_balance = float((current_bal + transaction_amount).quantize(Decimal("0.01")))
            else:  # income
                # Credit increases income (credit balance, shown as negative for income accounts)
                account.current_balance = float((current_bal - transaction_amount).quantize(Decimal("0.01")))
            db.add(account)
    
    # Update the cash/bank account balance
    second_bal = Decimal(str(second_account.current_balance or 0.0))
    if transaction_data.type == 'expense':
        # Expense: Credit reduces cash/bank
        second_account.current_balance = float((second_bal - transaction_amount).quantize(Decimal("0.01")))
    else:  # income
        # Income: Debit increases cash/bank
        second_account.current_balance = float((second_bal + transaction_amount).quantize(Decimal("0.01")))
    db.add(second_account)
    
    # Commit the balance updates
    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating account balances: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update account balances: {str(e)}"
        )
    
    # Log audit trail
    try:
        user_id_int = int(current_user.id)
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        await log_action(
            db=db,
            society_id=current_user.society_id,
            user_id=user_id_int,
            action_type="create",
            entity_type="transaction",
            entity_id=new_transaction.id,
            new_values={
                "type": new_transaction.type,
                "category": new_transaction.category,
                "amount": float(new_transaction.amount),
                "date": new_transaction.date.isoformat() if new_transaction.date else None,
                "account_code": new_transaction.account_code,
                "description": new_transaction.description
            },
            ip_address=ip_address,
            user_agent=user_agent
        )
    except Exception as e:
        # Don't fail transaction creation if audit logging fails
        print(f"Error logging audit trail: {e}")

    # Get voucher number from journal entry
    voucher_number = None
    if new_transaction.journal_entry_id:
        voucher_number = journal_entry.entry_number
    
    return TransactionResponse(
        id=str(new_transaction.id),
        document_number=new_transaction.document_number,
        voucher_number=voucher_number,
        type=new_transaction.type.value if hasattr(new_transaction.type, 'value') else new_transaction.type,
        category=new_transaction.category,
        description=new_transaction.description,
        amount=new_transaction.amount,
        quantity=getattr(new_transaction, 'quantity', None),
        unit_price=getattr(new_transaction, 'unit_price', None),
        date=new_transaction.date,
        expense_month=new_transaction.expense_month,
        journal_entry_id=new_transaction.journal_entry_id,
        account_code=new_transaction.account_code,
        added_by=str(new_transaction.added_by),
        created_at=new_transaction.created_at,
        updated_at=new_transaction.updated_at
    )


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific transaction by ID"""
    try:
        transaction_id_int = int(transaction_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid transaction ID"
        )

    # PRD: Filter by society_id for multi-tenancy
    result = await db.execute(
        select(Transaction).where(
            Transaction.id == transaction_id_int,
            Transaction.society_id == current_user.society_id
        )
    )
    transaction = result.scalar_one_or_none()

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )

    # Get voucher number from journal entry
    voucher_number = None
    if transaction.journal_entry_id:
        journal_result = await db.execute(
            select(JournalEntry).where(JournalEntry.id == transaction.journal_entry_id)
        )
        journal_entry = journal_result.scalar_one_or_none()
        if journal_entry:
            voucher_number = journal_entry.entry_number
    
    return TransactionResponse(
        id=str(transaction.id),
        document_number=transaction.document_number,
        voucher_number=voucher_number,
        type=transaction.type.value,  # Convert enum to string value
        category=transaction.category,
        description=transaction.description,
        amount=transaction.amount,
        quantity=getattr(transaction, 'quantity', None),
        unit_price=getattr(transaction, 'unit_price', None),
        date=transaction.date,
        expense_month=transaction.expense_month,
        account_code=transaction.account_code,
        journal_entry_id=transaction.journal_entry_id,
        added_by=str(transaction.added_by),
        created_at=transaction.created_at,
        updated_at=transaction.updated_at
    )


@router.put("/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(
    transaction_id: str,
    transaction_data: TransactionUpdate,
    request: Request,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a transaction"""
    # Check permission - auditors cannot edit transactions
    user_id_int = int(current_user.id)
    has_permission = await check_permission(
        user_id=user_id_int,
        permission_code="transactions.edit",
        db=db
    )
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to edit transactions. Auditors can only view transactions."
        )
    try:
        transaction_id_int = int(transaction_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid transaction ID"
        )

    # Get transaction (PRD: Filter by society_id for multi-tenancy)
    result = await db.execute(
        select(Transaction).where(
            Transaction.id == transaction_id_int,
            Transaction.society_id == current_user.society_id
        )
    )
    transaction = result.scalar_one_or_none()

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )

    # Get update data (only fields that were provided)
    update_data = transaction_data.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )

    # Convert date string to date object if date is being updated
    if "date" in update_data and update_data["date"]:
        date_value = update_data["date"]
        if isinstance(date_value, str):
            # Try to parse the date string
            try:
                # Try YYYY-MM-DD format first
                try:
                    update_data["date"] = datetime.strptime(date_value, '%Y-%m-%d').date()
                except ValueError:
                    # Try DD/MM/YYYY format
                    update_data["date"] = datetime.strptime(date_value, '%d/%m/%Y').date()
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid date format: {date_value}. Use YYYY-MM-DD or DD/MM/YYYY"
                )
        elif isinstance(date_value, date):
            # Already a date object, use as-is
            update_data["date"] = date_value

    # If account_code is being updated, validate it
    if "account_code" in update_data and update_data["account_code"]:
        result = await db.execute(
            select(AccountCode).where(AccountCode.code == update_data["account_code"])
        )
        account_code_obj = result.scalar_one_or_none()
        if not account_code_obj:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Account code {update_data['account_code']} not found"
            )

    # Store old values for audit trail
    old_values = {
        "type": transaction.type,
        "category": transaction.category,
        "amount": float(transaction.amount),
        "date": transaction.date.isoformat() if transaction.date else None,
        "account_code": transaction.account_code,
        "description": transaction.description
    }
    
    # Update fields
    for field, value in update_data.items():
        setattr(transaction, field, value)

    transaction.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(transaction)
    
    # Log audit trail
    try:
        user_id_int = int(current_user.id)
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        await log_action(
            db=db,
            society_id=current_user.society_id,
            user_id=user_id_int,
            action_type="update",
            entity_type="transaction",
            entity_id=transaction.id,
            old_values=old_values,
            new_values={
                "type": transaction.type,
                "category": transaction.category,
                "amount": float(transaction.amount),
                "date": transaction.date.isoformat() if transaction.date else None,
                "account_code": transaction.account_code,
                "description": transaction.description
            },
            ip_address=ip_address,
            user_agent=user_agent
        )
    except Exception as e:
        print(f"Error logging audit trail: {e}")

    # Get voucher number from journal entry
    voucher_number = None
    if transaction.journal_entry_id:
        journal_result = await db.execute(
            select(JournalEntry).where(JournalEntry.id == transaction.journal_entry_id)
        )
        journal_entry = journal_result.scalar_one_or_none()
        if journal_entry:
            voucher_number = journal_entry.entry_number

    return TransactionResponse(
        id=str(transaction.id),
        document_number=transaction.document_number,
        voucher_number=voucher_number,
        type=transaction.type.value,  # Convert enum to string value
        category=transaction.category,
        description=transaction.description,
        amount=transaction.amount,
        quantity=getattr(transaction, 'quantity', None),
        unit_price=getattr(transaction, 'unit_price', None),
        date=transaction.date,
        expense_month=transaction.expense_month,
        account_code=transaction.account_code,
        journal_entry_id=transaction.journal_entry_id,
        added_by=str(transaction.added_by),
        created_at=transaction.created_at,
        updated_at=transaction.updated_at
    )


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(
    transaction_id: str,
    request: Request,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a transaction"""
    # Check permission - auditors cannot delete transactions
    user_id_int = int(current_user.id)
    has_permission = await check_permission(
        user_id=user_id_int,
        permission_code="transactions.delete",
        db=db
    )
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete transactions. Auditors can only view transactions."
        )
    try:
        transaction_id_int = int(transaction_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid transaction ID"
        )

    # Get transaction before deletion for audit trail
    result = await db.execute(
        select(Transaction).where(
            Transaction.id == transaction_id_int,
            Transaction.society_id == current_user.society_id
        )
    )
    transaction = result.scalar_one_or_none()

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )

    # Store transaction data for audit trail before deletion
    deleted_values = {
        "type": transaction.type,
        "category": transaction.category,
        "amount": float(transaction.amount),
        "date": transaction.date.isoformat() if transaction.date else None,
        "account_code": transaction.account_code,
        "description": transaction.description
    }
    
    # Reverse account balance updates before deleting
    transaction_type = transaction.type.value if hasattr(transaction.type, 'value') else transaction.type
    
    # Reverse cash/bank account updates
    if transaction.payment_method == 'cash' and transaction_type == 'expense':
        # Reverse: increase Cash in Hand balance
        cash_account_result = await db.execute(
            select(AccountCode).where(
                AccountCode.code == '1010',
                AccountCode.society_id == current_user.society_id
            )
        )
        cash_account = cash_account_result.scalar_one_or_none()
        if cash_account:
            cash_account.current_balance += transaction.amount
            db.add(cash_account)  # Explicitly add to session
    
    elif transaction.payment_method == 'bank' and transaction_type == 'expense':
        # Reverse: increase Bank balance
        bank_account_code = await get_bank_account_code_from_settings(current_user.society_id, db)
        if bank_account_code:
            bank_account_result = await db.execute(
                select(AccountCode).where(
                    AccountCode.code == bank_account_code,
                    AccountCode.society_id == current_user.society_id
                )
            )
            bank_account = bank_account_result.scalar_one_or_none()
            if bank_account:
                bank_account.current_balance += transaction.amount
                db.add(bank_account)  # Explicitly add to session
    
    elif transaction.payment_method == 'cash' and transaction_type == 'income':
        # Reverse: decrease Cash in Hand balance
        cash_account_result = await db.execute(
            select(AccountCode).where(
                AccountCode.code == '1010',
                AccountCode.society_id == current_user.society_id
            )
        )
        cash_account = cash_account_result.scalar_one_or_none()
        if cash_account:
            cash_account.current_balance -= transaction.amount
            db.add(cash_account)  # Explicitly add to session
    
    elif transaction.payment_method == 'bank' and transaction_type == 'income':
        # Reverse: decrease Bank balance
        bank_account_code = await get_bank_account_code_from_settings(current_user.society_id, db)
        if bank_account_code:
            bank_account_result = await db.execute(
                select(AccountCode).where(
                    AccountCode.code == bank_account_code,
                    AccountCode.society_id == current_user.society_id
                )
            )
            bank_account = bank_account_result.scalar_one_or_none()
            if bank_account:
                bank_account.current_balance -= transaction.amount
                db.add(bank_account)  # Explicitly add to session
    
    # Reverse the expense/income account balance
    if transaction.account_code:
        account_result = await db.execute(
            select(AccountCode).where(
                AccountCode.code == transaction.account_code,
                AccountCode.society_id == current_user.society_id
            )
        )
        account = account_result.scalar_one_or_none()
        if account:
            if transaction_type == 'expense':
                # Reverse: decrease expense balance
                account.current_balance -= transaction.amount
            else:  # income
                # Reverse: increase income balance
                account.current_balance += transaction.amount
            db.add(account)  # Explicitly add to session

    await db.delete(transaction)
    await db.commit()
    
    # Log audit trail
    try:
        user_id_int = int(current_user.id)
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        await log_action(
            db=db,
            society_id=current_user.society_id,
            user_id=user_id_int,
            action_type="delete",
            entity_type="transaction",
            entity_id=transaction_id_int,
            old_values=deleted_values,
            ip_address=ip_address,
            user_agent=user_agent,
        )
    except Exception as e:
        print(f"Error logging audit trail: {e}")

    return None


@router.get("/statistics/summary")
async def get_transaction_summary(
    from_date: Optional[date] = Query(None, description="Start date"),
    to_date: Optional[date] = Query(None, description="End date"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get transaction summary statistics"""
    # Build base query with date filters
    conditions = []
    if from_date:
        conditions.append(Transaction.date >= from_date)
    if to_date:
        conditions.append(Transaction.date <= to_date)

    # Get income totals
    income_query = select(
        func.coalesce(func.sum(Transaction.amount), 0).label("total"),
        func.count(Transaction.id).label("count")
    ).where(Transaction.type == "income")

    if conditions:
        income_query = income_query.where(and_(*conditions))

    income_result = await db.execute(income_query)
    income_stats = income_result.one()

    # Get expense totals
    expense_query = select(
        func.coalesce(func.sum(Transaction.amount), 0).label("total"),
        func.count(Transaction.id).label("count")
    ).where(Transaction.type == "expense")

    if conditions:
        expense_query = expense_query.where(and_(*conditions))

    expense_result = await db.execute(expense_query)
    expense_stats = expense_result.one()

    # Format results
    total_income = float(income_stats.total)
    total_expense = float(expense_stats.total)

    summary = {
        "total_income": total_income,
        "total_expense": total_expense,
        "income_count": income_stats.count,
        "expense_count": expense_stats.count,
        "net_balance": total_income - total_expense
    }

    return summary


@router.get("/categories/list")
async def list_categories(
    type: Optional[str] = Query(None, description="Filter by type: income or expense"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get list of unique categories used in transactions"""
    # Build query for distinct categories
    query = select(Transaction.category).distinct()

    if type:
        if type not in ["income", "expense"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Type must be 'income' or 'expense'"
            )
        query = query.where(Transaction.type == type)

    # Get distinct categories
    result = await db.execute(query)
    categories = [row[0] for row in result.all() if row[0] is not None]

    return {"categories": sorted(categories)}


@router.post("/{txn_id}/reverse")
async def reverse_transaction(
    txn_id: int,
    reason: Optional[str] = Query(None, description="Reason for reversal"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Reverse a transaction. 
    If linked to a JournalEntry, reverse the whole JournalEntry.
    """
    # 1. Fetch transaction
    result = await db.execute(
        select(Transaction).where(
            Transaction.id == txn_id,
            Transaction.society_id == current_user.society_id
        )
    )
    transaction = result.scalar_one_or_none()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
        
    # 2. If it has a journal_entry_id, reverse the whole group
    if transaction.journal_entry_id:
        from app.routes.journal import reverse_journal_entry
        return await reverse_journal_entry(
            entry_id=transaction.journal_entry_id,
            reason=reason,
            current_user=current_user,
            db=db
        )
    else:
        # Fallback for old transactions without JournalEntry link
        # Find transactions with same document number prefix? 
        # For simplicity, we only allow reversing ones with links or we just reverse this one (not recommended for audit)
        raise HTTPException(
            status_code=400, 
            detail="This transaction is old and not linked to a journal group. Please use Journal Voucher for manual reversal."
        )
@router.get("/vouchers/{journal_entry_id}/pdf")
async def get_voucher_pdf(
    journal_entry_id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate professional PDF for any voucher/journal entry"""
    from sqlalchemy.orm import selectinload
    
    # 1. Fetch Journal Entry with all transactions
    result = await db.execute(
        select(JournalEntry).where(
            JournalEntry.id == journal_entry_id,
            JournalEntry.society_id == current_user.society_id
        ).options(selectinload(JournalEntry.entries))
    )
    jv = result.scalar_one_or_none()
    
    if not jv:
        raise HTTPException(status_code=404, detail="Journal Entry not found")
        
    # 2. Get Society Info
    result = await db.execute(select(Society).where(Society.id == current_user.society_id))
    society = result.scalar_one_or_none()
    
    # 3. Get Flat/Member info if available
    flat_id = None
    for entry in jv.entries:
        if entry.flat_id:
            flat_id = entry.flat_id
            break
            
    member_name = jv.received_from if jv.received_from else "Walk-in Member / General"
    flat_number = "N/A"
    
    if flat_id:
        # Get Flat
        flat_result = await db.execute(select(Flat).where(Flat.id == flat_id))
        flat_obj = flat_result.scalar_one_or_none()
        if flat_obj:
            flat_number = flat_obj.flat_number
            # Get Primary Member name only if jv.received_from is NOT set
            if not jv.received_from:
                member_result = await db.execute(
                    select(Member).where(
                        Member.flat_id == flat_id,
                        Member.society_id == current_user.society_id,
                        Member.is_primary == True
                    )
                )
                member_obj = member_result.scalar_one_or_none()
                if member_obj:
                    member_name = member_obj.name
                
    # 4. Prepare data for PDF
    from app.utils.number_to_words import number_to_words
    
    entries_data = []
    for entry in jv.entries:
        # Get account name
        acct_result = await db.execute(
            select(AccountCode).where(
                AccountCode.code == entry.account_code,
                AccountCode.society_id == current_user.society_id
            )
        )
        acct = acct_result.scalar_one_or_none()
        entries_data.append({
            "account_code": entry.account_code,
            "account_name": html.escape(acct.name) if acct else "Unknown Account",
            "debit": float(entry.debit_amount),
            "credit": float(entry.credit_amount)
        })
        
    voucher_data = {
        "voucher_number": jv.entry_number,
        "date": jv.date.strftime("%d %b %Y"),
        "voucher_type": jv.voucher_type.value if jv.voucher_type else "Journal",
        "description": html.escape(jv.description),
        "total_debit": float(jv.total_debit or 0),
        "total_credit": float(jv.total_credit or 0),
        "entries": entries_data,
        "reference": html.escape(jv.entries[0].document_number) if jv.entries and jv.entries[0].document_number else "N/A",
        "member_name": html.escape(member_name),
        "flat_number": html.escape(flat_number),
        "amount_in_words": number_to_words(float(jv.total_debit or 0))
    }
    
    society_info = {
        "name": html.escape(society.name) if society else "Our Society",
        "address": html.escape(society.address) if society and society.address else "",
        "email": html.escape(society.email) if society and society.email else "",
        "pan_no": html.escape(society.pan_no) if society and society.pan_no else "",
        "bank_name": html.escape(society.bank_name) if society and society.bank_name else "",
        "bank_account_number": html.escape(society.bank_account_number) if society and society.bank_account_number else "",
        "bank_ifsc_code": html.escape(society.bank_ifsc_code) if society and society.bank_ifsc_code else "",
        "logo_url": society.logo_url if society else ""
    }
    
    # 5. Generate PDF using the utility function
    try:
        pdf_buffer = PDFExporter.create_voucher_pdf(voucher_data, society_info)
    except Exception as e:
        import traceback
        with open("pdf_error.log", "a") as f:
            f.write(f"\n--- PDF Error at {datetime.now()} ---\n")
            f.write(f"Voucher: {jv.entry_number}\n")
            f.write(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"PDF Generation Error: {str(e)}")
    
    filename = f"Voucher_{jv.entry_number}.pdf"
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.post("/receipts", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_receipt(
    data: ReceiptCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a Receipt Voucher (Income)"""
    # 1. Parse date
    try:
        txn_date = datetime.strptime(data.date, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    # 2. Generate RV Number
    rv_number = await generate_receipt_voucher_number(db, current_user.society_id)
    
    # 3. Get Accounts
    result = await db.execute(select(AccountCode).where(AccountCode.code == data.account_code, AccountCode.society_id == current_user.society_id))
    income_acct = result.scalar_one_or_none()
    
    source_code = data.bank_account_code if data.payment_method == 'bank' else '1010'
    if data.payment_method == 'bank' and not data.bank_account_code:
        source_code = await get_bank_account_code_from_settings(current_user.society_id, db)
        
    result = await db.execute(select(AccountCode).where(AccountCode.code == source_code, AccountCode.society_id == current_user.society_id))
    asset_acct = result.scalar_one_or_none()
    
    if not income_acct or not asset_acct:
        raise HTTPException(status_code=400, detail="Invalid account codes")

    # 4. Create Journal Entry
    full_description = f"{data.description} (Ref: {data.reference})" if data.reference else data.description
    jv = JournalEntry(
        society_id=current_user.society_id,
        entry_number=rv_number,
        date=txn_date,
        description=full_description,
        received_from=data.received_from,
        voucher_type=VoucherType.RECEIPT,
        total_debit=Decimal(str(data.amount)),
        total_credit=Decimal(str(data.amount)),
        is_balanced=True,
        expense_month=data.expense_month if data.expense_month else txn_date.strftime("%B, %Y"),
        added_by=int(current_user.id)
    )
    db.add(jv)
    await db.flush()

    # 5. Create Transactions
    # Debit Bank/Cash (Asset increases)
    t1 = Transaction(
        society_id=current_user.society_id,
        type=TransactionType.INCOME,
        category="Receipt",
        account_code=asset_acct.code,
        amount=data.amount,
        debit_amount=data.amount,
        credit_amount=0,
        quantity=data.quantity,
        unit_price=data.unit_price,
        description=full_description,
        date=txn_date,
        journal_entry_id=jv.id,
        payment_method=data.payment_method,
        flat_id=int(data.flat_id) if data.flat_id else None,
        added_by=int(current_user.id)
    )
    # Credit Income/Dues (Income increases or Liability decreases)
    t2 = Transaction(
        society_id=current_user.society_id,
        type=TransactionType.INCOME,
        category="Receipt",
        account_code=income_acct.code,
        amount=data.amount,
        debit_amount=0,
        credit_amount=data.amount,
        quantity=data.quantity,
        unit_price=data.unit_price,
        description=f"{full_description} (Flat: {data.flat_id})" if data.flat_id else full_description,
        date=txn_date,
        journal_entry_id=jv.id,
        payment_method=data.payment_method,
        flat_id=int(data.flat_id) if data.flat_id else None,  # Store flat_id for proper tracking
        expense_month=data.expense_month if data.expense_month else txn_date.strftime("%B, %Y"),
        added_by=int(current_user.id)
    )
    db.add_all([t1, t2])

    # 6. Update Balances
    asset_acct.current_balance += Decimal(str(data.amount))
    income_acct.current_balance -= Decimal(str(data.amount))
    
    db.add_all([asset_acct, income_acct])

    # 7. Auto-allocation for Maintenance Dues (1100)
    if data.flat_id and data.account_code == '1100':
        await db.flush() # Ensure transactions have IDs
        flat_id_int = int(data.flat_id)
        
        # Try to find the primary member for this flat
        result = await db.execute(
            select(Member.user_id).where(
                Member.flat_id == flat_id_int,
                Member.society_id == current_user.society_id,
                Member.is_primary == True
            )
        )
        payer_user_id = result.scalar_one_or_none()
        if not payer_user_id:
            payer_user_id = int(current_user.id) # Fallback

        remaining_amount = Decimal(str(data.amount))
        
        # Fetch unpaid bills for this flat, oldest first
        result = await db.execute(
            select(MaintenanceBill)
            .where(
                MaintenanceBill.flat_id == flat_id_int,
                MaintenanceBill.society_id == current_user.society_id,
                MaintenanceBill.status == BillStatus.UNPAID
            )
            .order_by(MaintenanceBill.year.asc(), MaintenanceBill.month.asc())
        )
        unpaid_bills = result.scalars().all()
        
        for bill in unpaid_bills:
            if remaining_amount <= 0:
                break
            
            # Calculate actual balance for THIS bill (monthly charges only)
            result = await db.execute(
                select(func.sum(Payment.amount)).where(Payment.bill_id == bill.id)
            )
            already_paid = result.scalar() or 0
            bill_balance = Decimal(str(bill.amount)) - Decimal(str(already_paid))
            
            if bill_balance <= 0:
                bill.status = BillStatus.PAID
                continue

            p_amount = min(bill_balance, remaining_amount)
            
            # Create Payment record in billing module
            payment_rec = Payment(
                society_id=current_user.society_id,
                bill_id=bill.id,
                flat_id=flat_id_int,
                member_id=payer_user_id,
                receipt_number=rv_number,  # Use the same RV number for all allocations from this receipt
                payment_date=txn_date,
                payment_mode=PaymentMode.CASH if data.payment_method == 'cash' else PaymentMode.BANK_TRANSFER,
                amount=p_amount,
                remarks=f"Auto-allocated from Receipt Voucher {rv_number}",
                status=PaymentStatus.COMPLETED,
                transaction_id=t2.id, # Link to the credit transaction
                created_by=int(current_user.id),
                recorded_by=int(current_user.id)
            )
            db.add(payment_rec)
            
            remaining_amount -= p_amount
            
            # Update bill status if fully paid
            if p_amount >= bill_balance:
                bill.status = BillStatus.PAID
                bill.paid_date = txn_date

    await db.commit()
    await db.refresh(t1)

    return TransactionResponse(
        id=str(t1.id),
        voucher_number=rv_number,
        type="income",
        category="Receipt",
        description=t1.description,
        amount=t1.amount,
        quantity=data.quantity,
        unit_price=data.unit_price,
        date=t1.date,
        journal_entry_id=jv.id,
        account_code=t1.account_code,
        added_by=str(t1.added_by),
        created_at=t1.created_at,
        updated_at=t1.updated_at
    )


@router.post("/payments", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    data: PaymentCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a Payment Voucher (Expense)"""
    try:
        txn_date = datetime.strptime(data.date, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    pv_number = await generate_payment_voucher_number(db, current_user.society_id)
    
    result = await db.execute(select(AccountCode).where(AccountCode.code == data.account_code, AccountCode.society_id == current_user.society_id))
    expense_acct = result.scalar_one_or_none()
    
    dest_code = data.bank_account_code if data.payment_method == 'bank' else '1010'
    if data.payment_method == 'bank' and not data.bank_account_code:
        dest_code = await get_bank_account_code_from_settings(current_user.society_id, db)
        
    result = await db.execute(select(AccountCode).where(AccountCode.code == dest_code, AccountCode.society_id == current_user.society_id))
    asset_acct = result.scalar_one_or_none()
    
    if not expense_acct or not asset_acct:
        raise HTTPException(status_code=400, detail="Invalid account codes")

    full_description = f"{data.description} (Ref: {data.reference})" if data.reference else data.description
    jv = JournalEntry(
        society_id=current_user.society_id,
        entry_number=pv_number,
        date=txn_date,
        description=full_description,
        voucher_type=VoucherType.PAYMENT,
        total_debit=Decimal(str(data.amount)),
        total_credit=Decimal(str(data.amount)),
        is_balanced=True,
        expense_month=data.expense_month if data.expense_month else txn_date.strftime("%B, %Y"),
        added_by=int(current_user.id)
    )
    db.add(jv)
    await db.flush()

    # Debit Expense
    t1 = Transaction(
        society_id=current_user.society_id,
        type=TransactionType.EXPENSE,
        category="Payment",
        account_code=expense_acct.code,
        amount=data.amount,
        debit_amount=data.amount,
        credit_amount=0,
        quantity=data.quantity,
        unit_price=data.unit_price,
        description=full_description,
        date=txn_date,
        journal_entry_id=jv.id,
        payment_method=data.payment_method,
        flat_id=int(data.flat_id) if data.flat_id else None,
        added_by=int(current_user.id)
    )
    # Credit Bank/Cash
    t2 = Transaction(
        society_id=current_user.society_id,
        type=TransactionType.EXPENSE,
        category="Payment",
        account_code=asset_acct.code,
        amount=data.amount,
        debit_amount=0,
        credit_amount=data.amount,
        quantity=data.quantity,
        unit_price=data.unit_price,
        description=full_description,
        date=txn_date,
        journal_entry_id=jv.id,
        payment_method=data.payment_method,
        flat_id=int(data.flat_id) if data.flat_id else None,
        added_by=int(current_user.id)
    )
    db.add_all([t1, t2])

    expense_acct.current_balance += Decimal(str(data.amount))
    asset_acct.current_balance -= Decimal(str(data.amount))
    
    db.add_all([expense_acct, asset_acct])
    await db.commit()
    await db.refresh(t1)

    return TransactionResponse(
        id=str(t1.id),
        voucher_number=pv_number,
        type="expense",
        category="Payment",
        description=t1.description,
        amount=t1.amount,
        quantity=data.quantity,
        unit_price=data.unit_price,
        date=t1.date,
        journal_entry_id=jv.id,
        account_code=t1.account_code,
        added_by=str(t1.added_by),
        created_at=t1.created_at,
        updated_at=t1.updated_at
    )