"""Accounting API routes - Chart of Accounts"""
from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
import json
from pathlib import Path

from app.database import get_db
from app.models.accounting import AccountCode, AccountCodeResponse, AccountCodeUpdate, OpeningBalanceUpdate, BalanceSheetValidation
from app.models.user import UserResponse
from app.models_db import AccountCode as AccountCodeDB, Transaction, AccountType
from app.dependencies import get_current_user, get_current_admin_user

router = APIRouter()


def load_chart_of_accounts():
    """Load chart of accounts from JSON file"""
    json_path = Path(__file__).parent.parent / 'chart_of_accounts.json'
    if json_path.exists():
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


# Pre-configured chart of accounts (fallback if JSON not found)
CHART_OF_ACCOUNTS_FALLBACK = [
    # Minimal fallback - should use JSON file instead
    {"code": "1000", "name": "Bank Account - Main", "type": "asset", "description": "Primary bank account"},
    {"code": "1001", "name": "Bank Account - Savings", "type": "asset", "description": "Savings account"},
    {"code": "1010", "name": "Cash in Hand", "type": "asset", "description": "Physical cash"},
    {"code": "1020", "name": "Fixed Deposits", "type": "asset", "description": "Fixed deposit investments"},
    {"code": "1100", "name": "Maintenance Dues Receivable", "type": "asset", "description": "Outstanding maintenance from members"},
    {"code": "1200", "name": "Other Receivables", "type": "asset", "description": "Other amounts to be received"},
    {"code": "1500", "name": "Common Area Assets", "type": "asset", "description": "Furniture, equipment in common areas"},
    {"code": "1510", "name": "Generator", "type": "asset", "description": "Generator equipment"},
    {"code": "1520", "name": "Water Pumps & Motors", "type": "asset", "description": "Water supply equipment"},
    {"code": "1530", "name": "Security Equipment", "type": "asset", "description": "CCTV, intercom systems"},

    # LIABILITIES (2000-2999)
    {"code": "2000", "name": "Advance Maintenance Received", "type": "liability", "description": "Advance payments from members"},
    {"code": "2100", "name": "Security Deposits", "type": "liability", "description": "Refundable deposits from members"},
    {"code": "2200", "name": "Electricity Bill Payable", "type": "liability", "description": "Outstanding electricity bills"},
    {"code": "2210", "name": "Water Bill Payable", "type": "liability", "description": "Outstanding water bills"},
    {"code": "2220", "name": "Salary Payable", "type": "liability", "description": "Outstanding staff salaries"},
    {"code": "2300", "name": "Other Payables", "type": "liability", "description": "Other amounts to be paid"},

    # CAPITAL/RESERVES (3000-3999)
    {"code": "3001", "name": "Owner's Equity / Capital Fund", "type": "capital", "description": "Owner's equity to balance assets and liabilities"},
    {"code": "3000", "name": "Sinking Fund", "type": "capital", "description": "Reserve fund for major repairs"},
    {"code": "3010", "name": "Corpus Fund", "type": "capital", "description": "Long-term capital fund"},
    {"code": "3020", "name": "Emergency Fund", "type": "capital", "description": "Fund for immediate emergency expenses"},
    {"code": "3100", "name": "Retained Surplus", "type": "capital", "description": "Accumulated surplus from previous years"},

    # INCOME (4000-4999)
    {"code": "4000", "name": "Maintenance Charges", "type": "income", "description": "Monthly maintenance from members"},
    {"code": "4010", "name": "Water Charges", "type": "income", "description": "Water charges collected"},
    {"code": "4020", "name": "Parking Fees", "type": "income", "description": "Parking slot fees"},
    {"code": "4030", "name": "Amenity Charges", "type": "income", "description": "Charges for amenity usage"},
    {"code": "4040", "name": "Late Payment Fees", "type": "income", "description": "Penalty on late payments"},
    {"code": "4050", "name": "Interest Income", "type": "income", "description": "Interest from bank deposits"},
    {"code": "4100", "name": "Rental Income - Common Area", "type": "income", "description": "Rent from common area usage"},
    {"code": "4200", "name": "Other Income", "type": "income", "description": "Miscellaneous income"},

    # EXPENSES (5000-5999)
    # Staff & Security
    {"code": "5000", "name": "Watchman Salary", "type": "expense", "description": "Security guard salaries"},
    {"code": "5010", "name": "Housekeeping Salary", "type": "expense", "description": "Cleaning staff salaries"},
    {"code": "5020", "name": "Manager Salary", "type": "expense", "description": "Society manager salary"},
    {"code": "5030", "name": "Other Staff Salary", "type": "expense", "description": "Other staff payments"},

    # Utilities
    {"code": "5100", "name": "Electricity Charges - Common Area", "type": "expense", "description": "Common area electricity"},
    {"code": "5110", "name": "Water Charges - Tanker", "type": "expense", "description": "Water tanker charges"},
    {"code": "5120", "name": "Water Charges - Government", "type": "expense", "description": "Municipal water charges"},
    {"code": "5130", "name": "Generator Fuel", "type": "expense", "description": "Diesel/fuel for generator"},

    # Repairs & Maintenance
    {"code": "5200", "name": "Building Repairs", "type": "expense", "description": "Building maintenance and repairs"},
    {"code": "5210", "name": "Plumbing Repairs", "type": "expense", "description": "Plumbing work"},
    {"code": "5220", "name": "Electrical Repairs", "type": "expense", "description": "Electrical maintenance"},
    {"code": "5230", "name": "Painting Work", "type": "expense", "description": "Painting and whitewashing"},
    {"code": "5240", "name": "Lift Maintenance", "type": "expense", "description": "Elevator servicing and repairs"},
    {"code": "5250", "name": "Generator Maintenance", "type": "expense", "description": "Generator servicing"},
    {"code": "5260", "name": "Water Pump Repairs", "type": "expense", "description": "Pump maintenance"},

    # AMCs & Contracts
    {"code": "5300", "name": "Lift AMC", "type": "expense", "description": "Annual maintenance contract for lift"},
    {"code": "5310", "name": "Generator AMC", "type": "expense", "description": "Generator annual maintenance"},
    {"code": "5320", "name": "Fire Safety AMC", "type": "expense", "description": "Fire equipment maintenance"},
    {"code": "5330", "name": "Water Pump AMC", "type": "expense", "description": "Water pump maintenance contract"},
    {"code": "5340", "name": "CCTV AMC", "type": "expense", "description": "Security camera maintenance"},

    # Services
    {"code": "5400", "name": "Pest Control", "type": "expense", "description": "Pest control services"},
    {"code": "5410", "name": "Garbage Collection", "type": "expense", "description": "Waste disposal charges"},
    {"code": "5420", "name": "Cleaning Services", "type": "expense", "description": "Professional cleaning"},
    {"code": "5430", "name": "Gardening & Landscaping", "type": "expense", "description": "Garden maintenance"},
    {"code": "5440", "name": "Security Services", "type": "expense", "description": "Professional security services"},

    # Insurance & Legal
    {"code": "5500", "name": "Building Insurance", "type": "expense", "description": "Property insurance premium"},
    {"code": "5510", "name": "Legal Fees", "type": "expense", "description": "Legal consultation charges"},
    {"code": "5520", "name": "Audit Fees", "type": "expense", "description": "Auditor fees"},

    # Administrative
    {"code": "5600", "name": "Office Supplies", "type": "expense", "description": "Stationery and supplies"},
    {"code": "5610", "name": "Printing & Copying", "type": "expense", "description": "Printing expenses"},
    {"code": "5620", "name": "Internet & Phone", "type": "expense", "description": "Communication charges"},
    {"code": "5630", "name": "Bank Charges", "type": "expense", "description": "Bank transaction fees"},
    {"code": "5640", "name": "Software Subscriptions", "type": "expense", "description": "Accounting software, etc."},

    # Miscellaneous
    {"code": "5900", "name": "Festival Celebrations", "type": "expense", "description": "Community event expenses"},
    {"code": "5910", "name": "Welfare Activities", "type": "expense", "description": "Social welfare programs"},
    {"code": "5990", "name": "Other Expenses", "type": "expense", "description": "Miscellaneous expenses"},
]


@router.post("/initialize-chart-of-accounts", status_code=status.HTTP_201_CREATED)
async def initialize_chart_of_accounts(
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Initialize the chart of accounts with pre-configured account codes (admin only)"""
    # Check if already initialized for this society
    result = await db.execute(
        select(func.count(AccountCodeDB.id)).where(AccountCodeDB.society_id == current_user.society_id)
    )
    count = result.scalar()

    if count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Chart of accounts already initialized with {count} accounts. Delete existing accounts first if you want to reinitialize."
        )

    # Load chart of accounts from JSON file
    chart_of_accounts = load_chart_of_accounts()
    if not chart_of_accounts:
        # Fallback to hardcoded list if JSON not found
        chart_of_accounts = CHART_OF_ACCOUNTS_FALLBACK
    
    # Insert all account codes
    accounts_to_insert = []
    for account in chart_of_accounts:
        # Convert string type to AccountType enum
        account_type = AccountType(account["type"])
        account_obj = AccountCodeDB(
            society_id=current_user.society_id,
            code=account["code"],
            name=account["name"],
            type=account_type,
            description=account["description"],
            opening_balance=0.0,
            current_balance=0.0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        accounts_to_insert.append(account_obj)

    db.add_all(accounts_to_insert)
    await db.commit()

    return {
        "message": "Chart of accounts initialized successfully",
        "accounts_created": len(accounts_to_insert)
    }


@router.get("/accounts", response_model=List[AccountCodeResponse])
async def list_account_codes(
    type: Optional[str] = None,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all account codes (optionally filter by type)"""
    query = select(AccountCodeDB).where(AccountCodeDB.society_id == current_user.society_id).order_by(AccountCodeDB.code)

    if type:
        if type not in ["asset", "liability", "capital", "income", "expense"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Type must be one of: asset, liability, capital, income, expense"
            )
        # Convert string to AccountType enum for comparison
        account_type_enum = AccountType(type)
        query = query.where(AccountCodeDB.type == account_type_enum)

    result = await db.execute(query)
    accounts = result.scalars().all()

    return [
        AccountCodeResponse(
            id=str(account.id),
            code=account.code,
            name=account.name,
            type=account.type.value if hasattr(account.type, 'value') else str(account.type),
            description=account.description,
            opening_balance=account.opening_balance,
            current_balance=account.current_balance,
            is_fixed_expense=account.is_fixed_expense,
            created_at=account.created_at,
            updated_at=account.updated_at
        )
        for account in accounts
    ]


@router.post("/accounts", response_model=AccountCodeResponse, status_code=status.HTTP_201_CREATED)
async def create_account_code(
    account_data: AccountCode,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new account code (admin only)"""
    # Check if code already exists for this society
    result = await db.execute(
        select(AccountCodeDB).where(
            AccountCodeDB.code == account_data.code,
            AccountCodeDB.society_id == current_user.society_id
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Account code {account_data.code} already exists"
        )

    new_account = AccountCodeDB(
        society_id=current_user.society_id,
        code=account_data.code,
        name=account_data.name,
        type=account_data.type,
        description=account_data.description,
        opening_balance=account_data.opening_balance,
        current_balance=account_data.opening_balance,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    db.add(new_account)
    await db.commit()
    await db.refresh(new_account)

    return AccountCodeResponse(
        id=str(new_account.id),
        code=new_account.code,
        name=new_account.name,
        type=new_account.type.value if hasattr(new_account.type, 'value') else str(new_account.type),
        description=new_account.description,
        opening_balance=new_account.opening_balance,
        current_balance=new_account.current_balance,
        is_fixed_expense=new_account.is_fixed_expense,
        created_at=new_account.created_at,
        updated_at=new_account.updated_at
    )


@router.get("/accounts/{code}", response_model=AccountCodeResponse)
async def get_account_code(
    code: str,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific account code"""
    result = await db.execute(
        select(AccountCodeDB).where(
            AccountCodeDB.code == code,
            AccountCodeDB.society_id == current_user.society_id
        )
    )
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account code {code} not found"
        )

    return AccountCodeResponse(
        id=str(account.id),
        code=account.code,
        name=account.name,
        type=account.type.value if hasattr(account.type, 'value') else str(account.type),
        description=account.description,
        opening_balance=account.opening_balance,
        current_balance=account.current_balance,
        is_fixed_expense=account.is_fixed_expense,
        created_at=account.created_at,
        updated_at=account.updated_at
    )


@router.patch("/accounts/{code}", response_model=AccountCodeResponse)
async def update_account_code(
    code: str,
    update_data: AccountCodeUpdate,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Update an account code (name, description, etc.) - admin only"""
    result = await db.execute(
        select(AccountCodeDB).where(
            AccountCodeDB.code == code,
            AccountCodeDB.society_id == current_user.society_id
        )
    )
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account code {code} not found"
        )

    # Update fields if provided
    update_dict = update_data.model_dump(exclude_unset=True)
    if 'name' in update_dict and update_dict['name']:
        account.name = update_dict['name']
    if 'description' in update_dict:
        account.description = update_dict['description']
    if 'is_fixed_expense' in update_dict:
        account.is_fixed_expense = update_dict['is_fixed_expense']
    
    account.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(account)

    return AccountCodeResponse(
        id=str(account.id),
        code=account.code,
        name=account.name,
        type=account.type.value if hasattr(account.type, 'value') else str(account.type),
        description=account.description,
        opening_balance=account.opening_balance,
        current_balance=account.current_balance,
        is_fixed_expense=account.is_fixed_expense,
        created_at=account.created_at,
        updated_at=account.updated_at
    )


@router.delete("/accounts/{code}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account_code(
    code: str,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete an account code (admin only)"""
    # Check if account code is used in any transactions for this society
    result = await db.execute(
        select(func.count(Transaction.id)).where(
            Transaction.account_code == code,
            Transaction.society_id == current_user.society_id
        )
    )
    transaction_count = result.scalar()

    if transaction_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete account code {code}. It is used in {transaction_count} transactions."
        )

    # Delete account code
    result = await db.execute(
        delete(AccountCodeDB).where(
            AccountCodeDB.code == code,
            AccountCodeDB.society_id == current_user.society_id
        )
    )
    await db.commit()

    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account code {code} not found"
        )

    return None


@router.patch("/accounts/{code}/opening-balance", response_model=AccountCodeResponse)
async def update_opening_balance(
    code: str,
    balance_data: OpeningBalanceUpdate,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Update opening balance for an account (admin only)"""
    # Get the account
    result = await db.execute(
        select(AccountCodeDB).where(
            AccountCodeDB.code == code,
            AccountCodeDB.society_id == current_user.society_id
        )
    )
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account code {code} not found"
        )

    # Calculate the difference in opening balance
    old_opening = Decimal(str(account.opening_balance or 0.0))
    new_opening = Decimal(str(balance_data.opening_balance))
    balance_diff = new_opening - old_opening

    # Update opening balance
    account.opening_balance = float(new_opening.quantize(Decimal("0.01")))
    
    # Adjust current balance by the difference
    # This ensures that if opening balance changes, current balance reflects it
    current_bal = Decimal(str(account.current_balance or 0.0))
    account.current_balance = float((current_bal + balance_diff).quantize(Decimal("0.01")))
    
    account.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(account)

    return AccountCodeResponse(
        id=str(account.id),
        code=account.code,
        name=account.name,
        type=account.type.value if hasattr(account.type, 'value') else str(account.type),
        description=account.description,
        opening_balance=account.opening_balance,
        current_balance=account.current_balance,
        is_fixed_expense=account.is_fixed_expense,
        created_at=account.created_at,
        updated_at=account.updated_at
    )


@router.patch("/accounts/{code}/fixed-expense", response_model=AccountCodeResponse)
async def toggle_fixed_expense(
    code: str,
    update_data: AccountCodeUpdate,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Toggle is_fixed_expense flag for an account code (admin only)
    Only applicable for expense type account codes
    When enabled, this account code will be included in fixed expenses calculation for maintenance bills
    """
    # Get the account
    result = await db.execute(
        select(AccountCodeDB).where(
            AccountCodeDB.code == code,
            AccountCodeDB.society_id == current_user.society_id
        )
    )
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account code {code} not found"
        )
    
    # Only allow for expense type accounts
    if account.type != AccountType.EXPENSE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only expense type account codes can be marked for fixed expenses. Account {code} is of type {account.type.value}."
        )
    
    # Update the flag
    if update_data.is_fixed_expense is not None:
        account.is_fixed_expense = update_data.is_fixed_expense
        account.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(account)

    return AccountCodeResponse(
        id=str(account.id),
        code=account.code,
        name=account.name,
        type=account.type.value if hasattr(account.type, 'value') else str(account.type),
        description=account.description,
        opening_balance=account.opening_balance,
        current_balance=account.current_balance,
        is_fixed_expense=account.is_fixed_expense,
        created_at=account.created_at,
        updated_at=account.updated_at
    )


@router.get("/validate-balance-sheet", response_model=BalanceSheetValidation)
async def validate_balance_sheet(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Validate opening balances: Assets = Liabilities + Equity
    Returns the difference and suggests Owner's Equity adjustment
    """
    # Get all accounts with opening balances
    result = await db.execute(
        select(AccountCodeDB)
        .where(AccountCodeDB.society_id == current_user.society_id)
        .where(AccountCodeDB.type.in_([AccountType.ASSET, AccountType.LIABILITY, AccountType.CAPITAL]))
    )
    accounts = result.scalars().all()
    
    # Calculate totals
    total_assets = sum(Decimal(str(acc.opening_balance or 0.0)) for acc in accounts if acc.type == AccountType.ASSET)
    total_liabilities = sum(Decimal(str(acc.opening_balance or 0.0)) for acc in accounts if acc.type == AccountType.LIABILITY)
    total_equity = sum(Decimal(str(acc.opening_balance or 0.0)) for acc in accounts if acc.type == AccountType.CAPITAL)
    
    # Calculate difference
    total_liabilities_equity = total_liabilities + total_equity
    difference = total_assets - total_liabilities_equity
    
    # Find or suggest Owner's Equity account (code 3001)
    equity_account = None
    equity_result = await db.execute(
        select(AccountCodeDB)
        .where(AccountCodeDB.society_id == current_user.society_id)
        .where(AccountCodeDB.code == "3001")
    )
    equity_account = equity_result.scalar_one_or_none()
    
    is_balanced = abs(difference) < Decimal("0.01")  # Allow small rounding differences
    
    if is_balanced:
        message = "Balance sheet is balanced! Assets = Liabilities + Equity"
    elif difference > 0:
        # Assets > Liabilities + Equity, need to add to equity
        message = f"Assets exceed Liabilities + Equity by ₹{abs(difference):,.2f}. Add this amount to Owner's Equity (code 3001) on the liability side."
    else:
        # Liabilities + Equity > Assets, need to add to assets
        message = f"Liabilities + Equity exceed Assets by ₹{abs(difference):,.2f}. Add this amount to Owner's Equity (code 3001) on the asset side."
    
    return BalanceSheetValidation(
        total_assets=float(total_assets.quantize(Decimal("0.01"))),
        total_liabilities=float(total_liabilities.quantize(Decimal("0.01"))),
        total_equity=float(total_equity.quantize(Decimal("0.01"))),
        difference=float(difference.quantize(Decimal("0.01"))),
        is_balanced=is_balanced,
        equity_account_code=equity_account.code if equity_account else "3001",
        equity_account_name=equity_account.name if equity_account else "Owner's Equity / Capital Fund",
        message=message
    )


@router.delete("/accounts", status_code=status.HTTP_200_OK)
async def delete_all_account_codes(
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete all account codes (admin only). Use this to reset before reinitializing."""
    # Check if any account codes are used in transactions for this society
    result = await db.execute(
        select(func.count(Transaction.id)).where(
            Transaction.account_code.isnot(None),
            Transaction.society_id == current_user.society_id
        )
    )
    transaction_count = result.scalar()

    if transaction_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete all account codes. {transaction_count} transactions are using account codes. Delete transactions first."
        )

    # Get count before deletion for this society
    count_result = await db.execute(
        select(func.count(AccountCodeDB.id)).where(AccountCodeDB.society_id == current_user.society_id)
    )
    count = count_result.scalar()

    # Delete all account codes for this society
    await db.execute(
        delete(AccountCodeDB).where(AccountCodeDB.society_id == current_user.society_id)
    )
    await db.commit()

    return {
        "message": f"Deleted {count} account code(s) successfully",
        "deleted_count": count
    }