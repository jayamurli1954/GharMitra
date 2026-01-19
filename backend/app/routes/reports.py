"""Financial Reports API routes"""
from fastapi import APIRouter, HTTPException, Depends, Query, status
from fastapi.responses import StreamingResponse
from typing import Dict, Any, List, Optional
from datetime import date, datetime
from decimal import Decimal
from collections import defaultdict
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, case
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.user import UserResponse
from app.models.journal import TrialBalanceResponse, TrialBalanceItem, LedgerResponse, LedgerEntry, BulkLedgerResponse
from app.models.resource import ResourceFileResponse
from app.models_db import Transaction, AccountCode, Flat, MaintenanceBill as MaintenanceBillDB, Society, BillStatus, FinancialYear, OpeningBalance, BalanceType, JournalEntry, TransactionType, AccountType, Asset, AcquisitionType
from app.dependencies import get_current_user, get_current_accountant_user
from app.utils.permissions import check_permission
from app.utils.export_utils import ExcelExporter, PDFExporter

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/asset-register")
async def asset_register_report(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Asset Register Report - List of all assets with their WDV
    """
    result = await db.execute(
        select(Asset).where(Asset.society_id == current_user.society_id).order_by(Asset.created_at.desc())
    )
    assets = result.scalars().all()
    
    report_data = []
    for asset in assets:
        # Simple SLM depreciation calculation for report display
        original_cost = Decimal(str(asset.original_cost))
        dep_rate = Decimal(str(asset.depreciation_rate or 0)) / 100
        acq_date = asset.purchase_date or asset.handover_date
        
        # Calculate years passed
        years_passed = (date.today() - acq_date).days / 365.25
        if years_passed < 0: years_passed = 0
        
        total_depreciation = Decimal("0.00")
        if asset.depreciation_method == "straight_line":
            total_depreciation = original_cost * dep_rate * Decimal(str(years_passed))
        
        wdv = max(Decimal(str(asset.residual_value or 0)), original_cost - total_depreciation)
        
        report_data.append({
            "asset_code": asset.asset_code,
            "name": asset.name,
            "category": asset.category.value if hasattr(asset.category, 'value') else str(asset.category),
            "location": asset.location,
            "acquisition_type": asset.acquisition_type.value if hasattr(asset.acquisition_type, 'value') else str(asset.acquisition_type),
            "acquisition_date": acq_date,
            "original_cost": float(original_cost),
            "total_depreciation": float(total_depreciation),
            "wdv": float(wdv),
            "status": asset.status,
            "amc_expiry": asset.amc_expiry
        })
        
    return {
        "society_name": current_user.society_id, # Can be enhanced to show name
        "report_date": date.today(),
        "data": report_data
    }


@router.get("/society-summary")
async def society_summary_report(
    from_date: date = Query(..., description="Start date"),
    to_date: date = Query(..., description="End date"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Society Financial Summary - High-level overview for members
    Optimized bulk calculation for better performance and accuracy
    """
    # 1. Get Financial Year for to_date
    res = await db.execute(
        select(FinancialYear).where(
            and_(
                FinancialYear.society_id == current_user.society_id,
                FinancialYear.start_date <= to_date,
                FinancialYear.end_date >= to_date
            )
        ).order_by(FinancialYear.start_date.desc())
    )
    financial_year = res.scalars().first()
    
    if not financial_year:
        # Fallback to active year
        res = await db.execute(
            select(FinancialYear).where(
                and_(
                    FinancialYear.society_id == current_user.society_id,
                    FinancialYear.is_active == True
                )
            ).order_by(FinancialYear.start_date.desc())
        )
        financial_year = res.scalars().first()
        if not financial_year:
             raise HTTPException(status_code=400, detail="Financial year not found")

    fy_start_date = financial_year.start_date

    # 2. Get all accounts for this society (one query)
    res = await db.execute(
        select(AccountCode).where(AccountCode.society_id == current_user.society_id)
    )
    accounts_list = res.scalars().all()
    accounts_dict = {a.code: a for a in accounts_list}
    
    # 3. Get opening balances (one query)
    ob_res = await db.execute(
        select(OpeningBalance).where(OpeningBalance.financial_year_id == financial_year.id)
    )
    ob_dict = {ob.account_code: ob for ob in ob_res.scalars().all()}

    # 4. Bulk Aggregate Transactions (one query)
    # We aggregate up to to_date for cumulative balance, 
    # and separately for the period [from_date, to_date] for P&L items
    txn_agg = await db.execute(
        select(
            Transaction.account_code,
            func.sum(Transaction.debit_amount).label("debit"),
            func.sum(Transaction.credit_amount).label("credit"),
            # Period-specific sums for Income/Expense display
            func.sum(case((and_(Transaction.date >= from_date, Transaction.date <= to_date), Transaction.debit_amount), else_=0)).label("period_debit"),
            func.sum(case((and_(Transaction.date >= from_date, Transaction.date <= to_date), Transaction.credit_amount), else_=0)).label("period_credit")
        ).where(
            and_(
                Transaction.society_id == current_user.society_id,
                Transaction.date >= fy_start_date,
                Transaction.date <= to_date,
                Transaction.is_reversed == False
            )
        ).group_by(Transaction.account_code)
    )
    txns = {r.account_code: r for r in txn_agg.all()}

    # 5. Process everything in memory
    total_assets = Decimal("0.00")
    total_liabilities = Decimal("0.00")
    total_income_period = Decimal("0.00")
    total_expenses_period = Decimal("0.00")

    for code, account in accounts_dict.items():
        # A. Start with Opening Balance
        ob = ob_dict.get(code)
        if ob:
            ob_val = Decimal(str(ob.opening_balance))
            # Math: Debit is positive, Credit is negative
            current_bal = -ob_val if ob.balance_type == BalanceType.CREDIT else ob_val
        else:
            # Fallback to master opening balance
            current_bal = Decimal(str(account.opening_balance or 0.0))
            if account.type in [AccountType.LIABILITY, AccountType.CAPITAL, AccountType.INCOME]:
                current_bal = -current_bal
        
        # B. Add Transactions up to to_date
        txn_data = txns.get(code)
        if txn_data:
            debits = Decimal(str(txn_data.debit or 0.0))
            credits = Decimal(str(txn_data.credit or 0.0))
            current_bal = current_bal + debits - credits
            
            # C. Extract Period Totals for Income/Expenses
            if account.type == AccountType.INCOME:
                total_income_period += Decimal(str(txn_data.period_credit or 0.0))
            elif account.type == AccountType.EXPENSE:
                total_expenses_period += Decimal(str(txn_data.period_debit or 0.0))

        # D. Aggregate Assets/Liabilities
        if account.type == AccountType.ASSET:
            total_assets += current_bal
        elif account.type in [AccountType.LIABILITY, AccountType.CAPITAL]:
            total_liabilities += (-current_bal)

    # Society Balance (Capital/Net Worth) = Assets - Liabilities
    # In a perfect tally: Assets = Liabs + Capital + (Income - Expense)
    # But here we show "Society Balance" as net of Assets - External Liabilities
    society_balance = total_assets - total_liabilities
    
    # Net Surplus for the selected period
    period_surplus = total_income_period - total_expenses_period

    return {
        "status": "success",
        "data": {
            "period": f"{from_date.strftime('%d/%m/%Y')} to {to_date.strftime('%d/%m/%Y')}",
            "society_balance": float(society_balance),
            "total_income": float(total_income_period),
            "total_expenses": float(total_expenses_period),
            "total_assets": float(total_assets),
            "total_liabilities": float(total_liabilities),
            "period_surplus": float(period_surplus)
        }
    }
    society_balance = total_assets - total_liabilities
    
    # Get society info
    society_info = await get_society_info(current_user.society_id, db)
    
    return {
        "report_type": "Society Financial Summary",
        "society": society_info,
        "period": {
            "from": from_date,
            "to": to_date
        },
        "generated_at": datetime.utcnow(),
        "summary": {
            "society_balance": float(society_balance.quantize(Decimal("0.01"))),
            "total_assets": float(total_assets.quantize(Decimal("0.01"))),
            "total_liabilities": float(total_liabilities.quantize(Decimal("0.01"))),
            "period_income": float(total_income_period.quantize(Decimal("0.01"))),
            "period_expenses": float(total_expenses_period.quantize(Decimal("0.01"))),
            "surplus_deficit": float((total_income_period - total_expenses_period).quantize(Decimal("0.01")))
        }
    }


@router.get("/agm-documents", response_model=List[ResourceFileResponse])
async def get_agm_documents(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Fetch AGM notices and minutes for the society"""
    from app.models_db import ResourceFile
    result = await db.execute(
        select(ResourceFile).where(
            and_(
                ResourceFile.society_id == current_user.society_id,
                ResourceFile.category == "agm"
            )
        ).order_by(ResourceFile.created_at.desc())
    )
    docs = result.scalars().all()
    return docs


@router.get("/audit-reports", response_model=List[ResourceFileResponse])
async def get_audit_reports(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Fetch signed audit reports for the society"""
    from app.models_db import ResourceFile
    result = await db.execute(
        select(ResourceFile).where(
            and_(
                ResourceFile.society_id == current_user.society_id,
                ResourceFile.category == "audit"
            )
        ).order_by(ResourceFile.created_at.desc())
    )
    docs = result.scalars().all()
    return docs


async def get_society_info(society_id: int, db: AsyncSession) -> Dict[str, Any]:
    """Helper function to get society information for reports"""
    result = await db.execute(select(Society).where(Society.id == society_id))
    society = result.scalar_one_or_none()
    if not society:
        return {
            "name": "Unknown Society",
            "address": "",
            "logo_url": None
        }
    return {
        "name": society.name or "Unknown Society",
        "address": society.address or "",
        "logo_url": society.logo_url
    }


@router.get("/receipts-and-payments")
async def receipts_and_payments_report(
    from_date: date = Query(..., description="Start date"),
    to_date: date = Query(..., description="End date"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Receipts & Payments Account (Cash-based report)
    Shows actual cash received and paid during the period
    Restricted to Committee and Auditors
    """
    # RBAC: Only ADM, COM, and AUD roles can view full financial reports
    # SEC and MEM are restricted
    from app.models_db import UserRole
    allowed_roles = [
        UserRole.SUPER_ADMIN, 
        UserRole.ADMIN, 
        UserRole.ACCOUNTANT,
        UserRole.CHAIRMAN,
        UserRole.SECRETARY,
        UserRole.TREASURER,
        UserRole.AUDITOR
    ]
    
    if current_user.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="MEMBERS/SECURITY are only allowed to see summary reports. Full detail reports are restricted to Committee and Auditors."
        )

    # Check permission - auditors can view reports
    user_id_int = int(current_user.id)
    # Note: We still keep permission check for custom roles if implemented
    has_permission = await check_permission(
        user_id=user_id_int,
        permission_code="reports.view",
        db=db
    )
    if not has_permission:
        # Fallback: if they have one of the explicit roles above, we allow it even without explicit DB permission record
        pass
    # 1. Identify Cash and Bank accounts (Liquid Accounts)
    liquid_accounts_result = await db.execute(
        select(AccountCode).where(
            and_(
                AccountCode.society_id == current_user.society_id,
                or_(
                    AccountCode.code.like('100%'), # Cash
                    AccountCode.code.like('101%'), # Petty Cash
                    AccountCode.code.like('102%'), # Bank Accounts
                    AccountCode.code.like('103%'),
                    AccountCode.code.like('104%'),
                    AccountCode.code.like('105%'),
                    AccountCode.code.like('106%')
                )
            )
        )
    )
    liquid_accounts = liquid_accounts_result.scalars().all()
    liquid_codes = [acc.code for acc in liquid_accounts]
    liquid_account_ids = [acc.id for acc in liquid_accounts]

    if not liquid_codes:
        # Fallback if codes don't match pattern - look for 'Cash' or 'Bank' in name
        liquid_accounts_result = await db.execute(
            select(AccountCode).where(
                and_(
                    AccountCode.society_id == current_user.society_id,
                    or_(
                        AccountCode.name.ilike('%Cash%'),
                        AccountCode.name.ilike('%Bank%')
                    ),
                    AccountCode.type == AccountType.ASSET
                )
            )
        )
        liquid_accounts = liquid_accounts_result.scalars().all()
        liquid_codes = [acc.code for acc in liquid_accounts]
        liquid_account_ids = [acc.id for acc in liquid_accounts]

    # 2. Get Financial Year and Opening Balance for liquid accounts
    result = await db.execute(
        select(FinancialYear).where(
            and_(
                FinancialYear.society_id == current_user.society_id,
                FinancialYear.start_date <= from_date,
                FinancialYear.end_date >= from_date
            )
        ).order_by(FinancialYear.start_date.desc())
    )
    financial_year = result.scalars().first()
    
    opening_liquid_balance = Decimal("0.00")
    if financial_year:
        fy_start_date = financial_year.start_date
        # Get OB from OpeningBalance table
        ob_result = await db.execute(
            select(OpeningBalance).where(
                and_(
                    OpeningBalance.financial_year_id == financial_year.id,
                    OpeningBalance.account_head_id.in_(liquid_account_ids)
                )
            )
        )
        obs = ob_result.scalars().all()
        for ob in obs:
            val = Decimal(str(ob.opening_balance))
            # Liquid assets are debits
            if ob.balance_type == BalanceType.CREDIT:
                opening_liquid_balance -= val
            else:
                opening_liquid_balance += val
        
        # Add transactions between FY start and report from_date
        if fy_start_date < from_date:
            txn_ob_result = await db.execute(
                select(
                    func.sum(Transaction.debit_amount).label("debit"),
                    func.sum(Transaction.credit_amount).label("credit")
                ).where(
                    and_(
                        Transaction.society_id == current_user.society_id,
                        Transaction.account_code.in_(liquid_codes),
                        Transaction.date >= fy_start_date,
                        Transaction.date < from_date
                    )
                )
            )
            txn_ob_data = txn_ob_result.one()
            opening_liquid_balance += Decimal(str(txn_ob_data.debit or 0.0))
            opening_liquid_balance -= Decimal(str(txn_ob_data.credit or 0.0))
    else:
        # Fallback to account's current opening_balance if no FY found
        for acc in liquid_accounts:
            opening_liquid_balance += Decimal(str(acc.opening_balance or 0.0))

    # 3. Get all liquid transactions in the period
    result = await db.execute(
        select(Transaction)
        .where(
            and_(
                Transaction.society_id == current_user.society_id,
                Transaction.account_code.in_(liquid_codes),
                Transaction.date >= from_date,
                Transaction.date <= to_date
            )
        )
        .order_by(Transaction.date)
    )
    transactions = result.scalars().all()

    receipts = []
    payments = []
    total_receipts = Decimal("0.00")
    total_payments = Decimal("0.00")

    for txn in transactions:
        debit = Decimal(str(txn.debit_amount or 0.0))
        credit = Decimal(str(txn.credit_amount or 0.0))
        
        if debit > 0:
            receipts.append({
                "date": txn.date,
                "description": txn.description,
                "category": txn.category,
                "amount": float(debit.quantize(Decimal("0.01"))),
                "account_code": txn.account_code
            })
            total_receipts += debit
        
        if credit > 0:
            payments.append({
                "date": txn.date,
                "description": txn.description,
                "category": txn.category,
                "amount": float(credit.quantize(Decimal("0.01"))),
                "account_code": txn.account_code
            })
            total_payments += credit

    # Get society info
    society_info = await get_society_info(current_user.society_id, db)
    
    closing_liquid_balance = opening_liquid_balance + total_receipts - total_payments
    
    return {
        "report_type": "Receipts & Payments Account",
        "society": society_info,
        "period": {
            "from": from_date,
            "to": to_date
        },
        "generated_at": datetime.utcnow(),
        "opening_balance": float(opening_liquid_balance.quantize(Decimal("0.01"))),
        "receipts": receipts,
        "payments": payments,
        "total_receipts": float(total_receipts.quantize(Decimal("0.01"))),
        "total_payments": float(total_payments.quantize(Decimal("0.01"))),
        "closing_balance": float(closing_liquid_balance.quantize(Decimal("0.01")))
    }


@router.get("/income-and-expenditure")
async def income_and_expenditure_report(
    from_date: date = Query(..., description="Start date"),
    to_date: date = Query(..., description="End date"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Income & Expenditure Account (Accrual-based)
    Shows income earned and expenses incurred (profit & loss)
    Restricted to Committee and Auditors
    """
    # RBAC: Only ADM, COM, and AUD roles can view full financial reports
    from app.models_db import UserRole
    allowed_roles = [
        UserRole.SUPER_ADMIN, 
        UserRole.ADMIN, 
        UserRole.ACCOUNTANT,
        UserRole.CHAIRMAN,
        UserRole.SECRETARY,
        UserRole.TREASURER,
        UserRole.AUDITOR
    ]
    
    if current_user.role not in allowed_roles:
         # Note:  says members can see "summary". 
         # For now, we restrict the full report.
         raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="MEMBERS/SECURITY are only allowed to see summary reports. Full detail reports are restricted to Committee and Auditors."
        )

    # Check permission - auditors can view reports
    user_id_int = int(current_user.id)
    has_permission = await check_permission(
        user_id=user_id_int,
        permission_code="reports.view",
        db=db
    )
    if not has_permission:
        pass
    
    # Income & Expenditure Statement should ONLY include Income and Expense accounts
    # NOT Assets, Liabilities, or Capital accounts
    # IMPORTANT: Should match Trial Balance - calculate from Financial Year start to to_date
    
    # 1. Get Financial Year for the period
    result = await db.execute(
        select(FinancialYear).where(
            and_(
                FinancialYear.society_id == current_user.society_id,
                FinancialYear.start_date <= to_date,
                FinancialYear.end_date >= to_date
            )
        ).order_by(FinancialYear.start_date.desc())
    )
    financial_year = result.scalars().first()
    
    if not financial_year:
        # Fallback to active financial year
        result = await db.execute(
            select(FinancialYear).where(
                and_(
                    FinancialYear.society_id == current_user.society_id,
                    FinancialYear.is_active == True
                )
            ).order_by(FinancialYear.start_date.desc())
        )
        financial_year = result.scalars().first()
        
        if not financial_year:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No financial year found. Please create a financial year first."
            )
    
    fy_start_date = financial_year.start_date
    effective_date = min(to_date, financial_year.end_date)
    
    # 2. Get all Income and Expense accounts
    income_expense_accounts_result = await db.execute(
        select(AccountCode).where(
            and_(
                AccountCode.society_id == current_user.society_id,
                or_(
                    AccountCode.type == AccountType.INCOME,
                    AccountCode.type == AccountType.EXPENSE
                )
            )
        )
    )
    income_expense_accounts = income_expense_accounts_result.scalars().all()
    income_expense_codes = [acc.code for acc in income_expense_accounts]
    income_expense_accounts_dict = {acc.code: acc for acc in income_expense_accounts}
    
    if not income_expense_codes:
        # No income/expense accounts found
        return {
            "report_type": "Income & Expenditure Account",
            "society": await get_society_info(current_user.society_id, db),
            "period": {"from": from_date, "to": to_date},
            "generated_at": datetime.utcnow(),
            "income_items": [],
            "expenditure_items": [],
            "total_income": 0.0,
            "total_expenditure": 0.0,
            "net_income": 0.0,
            "result": "Balanced"
        }
    
    # 3. Get opening balances for income/expense accounts
    opening_balances_result = await db.execute(
        select(OpeningBalance, AccountCode).join(
            AccountCode, OpeningBalance.account_head_id == AccountCode.id
        ).where(
            and_(
                OpeningBalance.financial_year_id == financial_year.id,
                AccountCode.society_id == current_user.society_id,
                AccountCode.code.in_(income_expense_codes)
            )
        )
    )
    opening_balances = {}
    for ob, ac in opening_balances_result.all():
        opening_balances[ac.code] = ob
    
    # 4. Get all transactions for income/expense accounts from FY start to to_date
    # This matches the Trial Balance calculation method
    result = await db.execute(
        select(Transaction).where(
            and_(
                Transaction.society_id == current_user.society_id,
                Transaction.account_code.in_(income_expense_codes),
                Transaction.date >= fy_start_date,
                Transaction.date <= effective_date
            )
        ).order_by(Transaction.date, Transaction.id)
    )
    transactions = result.scalars().all()
    
    # 5. Calculate balances by account (same logic as Trial Balance)
    income_by_account = {}  # {account_code: {"name": str, "amount": Decimal}}
    expense_by_account = {}  # {account_code: {"name": str, "amount": Decimal}}
    
    total_income = Decimal("0.00")
    total_expenditure = Decimal("0.00")
    
    # Process each account
    for account_code, account in income_expense_accounts_dict.items():
        # Start with opening balance
        balance = Decimal("0.00")
        ob = opening_balances.get(account_code)
        if ob:
            ob_val = Decimal(str(ob.opening_balance))
            if ob.balance_type == BalanceType.DEBIT:
                balance = ob_val
            else:  # credit
                balance = -ob_val  # Credit stored as negative
        else:
            # Fallback to account's opening_balance field
            balance = Decimal(str(account.opening_balance or 0.0))
            if account.type in ['income']:
                balance = -balance  # Income accounts: credit balance (negative)
        
        # Process all transactions for this account
        for txn in transactions:
            if txn.account_code != account_code:
                continue
                
            debit = Decimal(str(txn.debit_amount or 0.0))
            credit = Decimal(str(txn.credit_amount or 0.0))
            
            if account.type == AccountType.INCOME:
                # Income accounts: Credit increases (more negative), Debit decreases
                balance += debit  # Debit decreases credit balance
                balance -= credit  # Credit increases (more negative)
            elif account.type == AccountType.EXPENSE:
                # Expense accounts: Debit increases, Credit decreases
                balance += debit
                balance -= credit
        
        # Convert balance to display format
        if account.type == AccountType.INCOME:
            # Income accounts: negative balance = positive income (credit balance)
            if balance < 0:
                income_amount = abs(balance)
                income_by_account[account_code] = {
                    "name": account.name,
                    "amount": income_amount
                }
                total_income += income_amount
        elif account.type == AccountType.EXPENSE:
            # Expense accounts: positive balance = expense (debit balance)
            if balance > 0:
                expense_amount = balance
                expense_by_account[account_code] = {
                    "name": account.name,
                    "amount": expense_amount
                }
                total_expenditure += expense_amount
    
    surplus_or_deficit = total_income - total_expenditure

    # Get society info
    society_info = await get_society_info(current_user.society_id, db)

    # Prepare items as lists for frontend (only include accounts with non-zero amounts)
    income_items = [
        {
            "account_name": data["name"],
            "amount": float(data["amount"].quantize(Decimal("0.01"))),
            "account_code": code
        }
        for code, data in income_by_account.items()
        if abs(data["amount"]) >= Decimal("0.01")
    ]
    expenditure_items = [
        {
            "account_name": data["name"],
            "amount": float(data["amount"].quantize(Decimal("0.01"))),
            "account_code": code
        }
        for code, data in expense_by_account.items()
        if abs(data["amount"]) >= Decimal("0.01")
    ]
    
    # Sort by amount (descending)
    income_items.sort(key=lambda x: x["amount"], reverse=True)
    expenditure_items.sort(key=lambda x: x["amount"], reverse=True)

    return {
        "report_type": "Income & Expenditure Account",
        "society": society_info,
        "period": {
            "from": from_date,
            "to": to_date
        },
        "generated_at": datetime.utcnow(),
        "income_items": income_items,
        "expenditure_items": expenditure_items,
        "total_income": float(total_income.quantize(Decimal("0.01"))),
        "total_expenditure": float(total_expenditure.quantize(Decimal("0.01"))),
        "net_income": float(surplus_or_deficit.quantize(Decimal("0.01"))),
        "result": "Surplus" if surplus_or_deficit > Decimal("0") else "Deficit" if surplus_or_deficit < Decimal("0") else "Balanced"
    }


@router.get("/balance-sheet")
async def balance_sheet_report(
    as_on_date: date = Query(..., description="Balance sheet date"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Balance Sheet - Assets, Liabilities, and Capital position
    Restricted to Committee and Auditors
    """
    try:
        # RBAC: Only ADM, COM, and AUD roles can view full financial reports
        from app.models_db import UserRole
        allowed_roles = [
            UserRole.SUPER_ADMIN, 
            UserRole.ADMIN, 
            UserRole.ACCOUNTANT,
            UserRole.CHAIRMAN,
            UserRole.SECRETARY,
            UserRole.TREASURER,
            UserRole.AUDITOR
        ]
        
        if current_user.role not in allowed_roles:
             raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="MEMBERS/SECURITY are only allowed to see summary reports. Full detail reports are restricted to Committee and Auditors."
            )

        # Check permission - auditors can view reports
        user_id_int = int(current_user.id)
        has_permission = await check_permission(
            user_id=user_id_int,
            permission_code="reports.view",
            db=db
        )
        if not has_permission:
            pass
    except Exception as e:
        logger.error(f"Error in balance_sheet_report (initial checks): {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating balance sheet: {str(e)}"
        )
    
    # Find the financial year that contains as_on_date
    result = await db.execute(
        select(FinancialYear).where(
            and_(
                FinancialYear.society_id == current_user.society_id,
                FinancialYear.start_date <= as_on_date,
                FinancialYear.end_date >= as_on_date
            )
        ).order_by(FinancialYear.start_date.desc())
    )
    financial_year = result.scalars().first()
    
    if not financial_year:
        # Fallback to active financial year
        result = await db.execute(
            select(FinancialYear).where(
                and_(
                    FinancialYear.society_id == current_user.society_id,
                    FinancialYear.is_active == True
                )
            ).order_by(FinancialYear.start_date.desc())
        )
        financial_year = result.scalars().first()
        
        if not financial_year:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No financial year found. Please create a financial year first."
            )
    
    fy_start_date = financial_year.start_date
    effective_date = min(as_on_date, financial_year.end_date)
    
    # Get all accounts for this society
    result = await db.execute(
        select(AccountCode).where(AccountCode.society_id == current_user.society_id)
        .order_by(AccountCode.code)
    )
    accounts = result.scalars().all()
    
    # Get opening balances for this financial year
    opening_balances_result = await db.execute(
        select(OpeningBalance, AccountCode).join(
            AccountCode, OpeningBalance.account_head_id == AccountCode.id
        ).where(
            OpeningBalance.financial_year_id == financial_year.id,
            AccountCode.society_id == current_user.society_id
        )
    )
    opening_balances = {}
    for ob, ac in opening_balances_result.all():
        opening_balances[ac.code] = ob

    # Standard Balance Sheet Format for Housing Society
    # LIABILITIES: A. Capital & Funds, B. Current Liabilities & Provisions
    # ASSETS: A. Fixed Assets, B. Investments, C. Current Assets
    
    # Helper function to categorize accounts
    def categorize_account(account):
        """Categorize account for Balance Sheet format"""
        name_lower = account.name.lower()
        code = account.code
        
        if account.type == AccountType.CAPITAL:
            return "capital_funds"
        elif account.type == AccountType.LIABILITY:
            return "current_liabilities"
        elif account.type == AccountType.ASSET:
            # Fixed Assets (typically 2000-2999 range or contains keywords)
            if any(keyword in name_lower for keyword in ['building', 'lift', 'generator', 'electrical', 'equipment', 'furniture', 'fixture', 'depreciation']):
                return "fixed_assets"
            # Investments (Fixed Deposits)
            elif 'fixed deposit' in name_lower or 'fd' in name_lower:
                return "investments"
            # Current Assets (everything else)
            else:
                return "current_assets"
        return None
    
    # Calculate balances for all accounts
    account_balances = {}
    
    for account in accounts:
        # Skip Income and Expense accounts (they contribute to Surplus/Deficit which goes to Capital)
        if account.type in [AccountType.INCOME, AccountType.EXPENSE]:
            continue
            
        # Start with opening balance
        balance = Decimal("0.00")
        ob = opening_balances.get(account.code)
        if ob:
            ob_val = Decimal(str(ob.opening_balance))
            if ob.balance_type == BalanceType.DEBIT:
                balance = ob_val
            else:  # credit
                balance = -ob_val  # Credit stored as negative
        else:
            # Fallback to account's opening_balance field
            balance = Decimal(str(account.opening_balance or 0.0))
            if account.type in [AccountType.LIABILITY, AccountType.CAPITAL]:
                balance = -balance  # Credit balance (negative)
        
        # Get all transactions for this account from FY start to as_on_date
        transactions_result = await db.execute(
            select(Transaction).where(
                and_(
                    Transaction.society_id == current_user.society_id,
                    Transaction.account_code == account.code,
                    Transaction.date >= fy_start_date,
                    Transaction.date <= effective_date
                )
            ).order_by(Transaction.date, Transaction.id)
        )
        transactions = transactions_result.scalars().all()
        
        # Calculate balance from transactions
        for txn in transactions:
            debit = Decimal(str(txn.debit_amount or 0.0))
            credit = Decimal(str(txn.credit_amount or 0.0))
            
            if account.type == AccountType.ASSET:
                # Asset: Debit increases, Credit decreases
                balance += debit
                balance -= credit
            else:  # liability, capital
                # Liability/Capital: Credit increases (negative), Debit decreases
                balance += debit  # Debit decreases credit balance
                balance -= credit  # Credit increases (more negative)
        
        # Store balance with category
        category = categorize_account(account)
        if category:
            if account.type == AccountType.ASSET:
                # Assets: positive balance = asset
                if balance > Decimal("0.01"):
                    if category not in account_balances:
                        account_balances[category] = []
                    account_balances[category].append({
                        "code": account.code,
                        "name": account.name,
                        "balance": float(balance.quantize(Decimal("0.01")))
                    })
            else:  # liability, capital
                # Liabilities/Capital: negative balance = positive liability/capital (credit balance)
                if balance < -Decimal("0.01"):
                    if category not in account_balances:
                        account_balances[category] = []
                    account_balances[category].append({
                        "code": account.code,
                        "name": account.name,
                        "balance": float(abs(balance).quantize(Decimal("0.01")))
                    })
    
    # Calculate Income & Expenditure Surplus/Deficit
    # This will be added to "Retained Surplus" or shown as "Surplus/Deficit" in Capital & Funds
    income_expense_accounts_result = await db.execute(
        select(AccountCode).where(
            and_(
                AccountCode.society_id == current_user.society_id,
                or_(
                    AccountCode.type == AccountType.INCOME,
                    AccountCode.type == AccountType.EXPENSE
                )
            )
        )
    )
    income_expense_accounts = income_expense_accounts_result.scalars().all()
    income_expense_codes = [acc.code for acc in income_expense_accounts]
    
    total_income = Decimal("0.00")
    total_expenses = Decimal("0.00")
    
    if income_expense_codes:
        # Get all income/expense transactions from FY start to as_on_date
        ie_transactions_result = await db.execute(
            select(Transaction, AccountCode).join(
                AccountCode, Transaction.account_code == AccountCode.code
            ).where(
                and_(
                    Transaction.society_id == current_user.society_id,
                    Transaction.account_code.in_(income_expense_codes),
                    Transaction.date >= fy_start_date,
                    Transaction.date <= effective_date
                )
            )
        )
        ie_transactions = ie_transactions_result.all()
        
        for txn, account in ie_transactions:
            debit = Decimal(str(txn.debit_amount or 0.0))
            credit = Decimal(str(txn.credit_amount or 0.0))
            
            if account.type == AccountType.INCOME:
                total_income += (credit - debit)
            elif account.type == AccountType.EXPENSE:
                total_expenses += (debit - credit)
        
        # Include opening balances for income/expense accounts
        for account in income_expense_accounts:
            ob = opening_balances.get(account.code)
            if ob:
                ob_val = Decimal(str(ob.opening_balance))
                if account.type == AccountType.INCOME:
                    if ob.balance_type == BalanceType.CREDIT:
                        total_income += ob_val
                    else:
                        total_income -= ob_val
                elif account.type == AccountType.EXPENSE:
                    if ob.balance_type == BalanceType.DEBIT:
                        total_expenses += ob_val
                    else:
                        total_expenses -= ob_val
    
    # Surplus/Deficit = Income - Expenses
    surplus_deficit = total_income - total_expenses
    
    # Add Surplus/Deficit to Capital & Funds (as "Surplus/Deficit" or add to "Retained Surplus")
    if abs(surplus_deficit) >= Decimal("0.01"):
        if "capital_funds" not in account_balances:
            account_balances["capital_funds"] = []
        # Check if "Retained Surplus" exists, otherwise add as "Surplus/Deficit"
        retained_surplus_found = False
        for item in account_balances["capital_funds"]:
            if "retained" in item["name"].lower() or "surplus" in item["name"].lower():
                item["balance"] += float(surplus_deficit.quantize(Decimal("0.01")))
                retained_surplus_found = True
                break
        if not retained_surplus_found:
            account_balances["capital_funds"].append({
                "code": "9999",
                "name": "Surplus/Deficit (Excess of Income over Expenditure)" if surplus_deficit >= 0 else "Deficit (Excess of Expenditure over Income)",
                "balance": float(abs(surplus_deficit).quantize(Decimal("0.01")))
            })
    
    # Calculate totals for each category
    def calculate_total(items):
        """Calculate total from list of items, ensuring Decimal type"""
        if not items:
            return Decimal("0.00")
        total = sum(Decimal(str(item["balance"])) for item in items)
        return Decimal(str(total))  # Ensure it's a Decimal
    
    capital_funds = account_balances.get("capital_funds", [])
    current_liabilities = account_balances.get("current_liabilities", [])
    fixed_assets = account_balances.get("fixed_assets", [])
    investments = account_balances.get("investments", [])
    current_assets = account_balances.get("current_assets", [])
    
    total_capital_funds = calculate_total(capital_funds)
    total_current_liabilities = calculate_total(current_liabilities)
    total_liabilities = total_capital_funds + total_current_liabilities
    
    total_fixed_assets = calculate_total(fixed_assets)
    total_investments = calculate_total(investments)
    total_current_assets = calculate_total(current_assets)
    total_assets = total_fixed_assets + total_investments + total_current_assets
    
    try:
        # Get society info
        society_info = await get_society_info(current_user.society_id, db)

        return {
            "report_type": "Balance Sheet",
            "as_on_date": as_on_date,
            "society": society_info,
            "generated_at": datetime.utcnow(),
            # Liabilities side
            "capital_funds": capital_funds,
            "current_liabilities": current_liabilities,
            "total_capital_funds": float(total_capital_funds.quantize(Decimal("0.01"))),
            "total_current_liabilities": float(total_current_liabilities.quantize(Decimal("0.01"))),
            "total_liabilities": float(total_liabilities.quantize(Decimal("0.01"))),
            # Assets side
            "fixed_assets": fixed_assets,
            "investments": investments,
            "current_assets": current_assets,
            "total_fixed_assets": float(total_fixed_assets.quantize(Decimal("0.01"))),
            "total_investments": float(total_investments.quantize(Decimal("0.01"))),
            "total_current_assets": float(total_current_assets.quantize(Decimal("0.01"))),
            "total_assets": float(total_assets.quantize(Decimal("0.01"))),
            # Balance check (ensure both are Decimal)
            "is_balanced": abs(total_assets - total_liabilities) < Decimal("0.01"),
            "surplus_deficit": float(surplus_deficit.quantize(Decimal("0.01")))
        }
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"Error generating balance sheet: {str(e)}\n{error_trace}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating balance sheet: {str(e)}"
        )


@router.get("/member-dues")
async def member_dues_report(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Member Dues Report - Outstanding dues for all members
    Restricted to Committee and Auditors
    """
    # RBAC: Only ADM, COM, and AUD roles can view full financial reports
    from app.models_db import UserRole
    allowed_roles = [
        UserRole.SUPER_ADMIN, 
        UserRole.ADMIN, 
        UserRole.ACCOUNTANT,
        UserRole.CHAIRMAN,
        UserRole.SECRETARY,
        UserRole.TREASURER,
        UserRole.AUDITOR
    ]
    
    if current_user.role not in allowed_roles:
         raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="MEMBERS/SECURITY are only allowed to see a summary of society dues. Detailed member-wise dues are restricted to Committee and Auditors."
        )

    # Check permission - auditors can view reports
    user_id_int = int(current_user.id)
    has_permission = await check_permission(
        user_id=user_id_int,
        permission_code="reports.view",
        db=db
    )
    if not has_permission:
        pass
    # Get all flats
    result = await db.execute(select(Flat).order_by(Flat.flat_number))
    flats = result.scalars().all()

    # Get all Users to map to flats (fallback for owner name)
    # Filter for residents/members
    from app.models_db import User
    result_users = await db.execute(select(User).where(User.role == UserRole.RESIDENT))
    users = result_users.scalars().all()
    
    # Create a map of Flat Number -> User Name (first one found)
    flat_user_map = {}
    for user in users:
        # Normalize: Remove "Flat " prefix if exists to match flat_number
        clean_apt = user.apartment_number.replace("Flat ", "").replace("flat ", "").strip()
        if clean_apt not in flat_user_map:
            flat_user_map[clean_apt] = user.name

    dues_report = []
    total_outstanding = Decimal("0.00")

    # Calculate dues directly from GL Account 1100 transactions
    # This is the source of truth - the General Ledger
    # For each flat, we calculate: Outstanding = Debits - Credits
    for flat in flats:
        # Debits (bills raised) - use flat_id for direct lookup
        debits_result = await db.execute(
            select(func.sum(Transaction.debit_amount)).where(
                and_(
                    Transaction.account_code == "1100",
                    Transaction.flat_id == flat.id
                )
            )
        )
        total_debits = debits_result.scalar() or Decimal("0.00")

        # Credits (payments received) - use flat_id for direct lookup
        credits_result = await db.execute(
            select(func.sum(Transaction.credit_amount)).where(
                and_(
                    Transaction.account_code == "1100",
                    Transaction.flat_id == flat.id
                )
            )
        )
        total_credits = credits_result.scalar() or Decimal("0.00")

        # Outstanding = Debits - Credits
        outstanding_amount = Decimal(str(total_debits)) - Decimal(str(total_credits))
        total_outstanding += outstanding_amount

        # Get unpaid posted bills for bill details (for display only, not for calculation)
        result = await db.execute(
            select(MaintenanceBillDB).where(
                and_(
                    MaintenanceBillDB.flat_id == flat.id,
                    MaintenanceBillDB.status == BillStatus.UNPAID,
                    MaintenanceBillDB.is_posted == True
                )
            ).order_by(MaintenanceBillDB.year.desc(), MaintenanceBillDB.month.desc())
        )
        unpaid_bills = result.scalars().all()

        # Get last payment info from transactions (credits to 1100)
        last_payment_result = await db.execute(
            select(Transaction.date).where(
                and_(
                    Transaction.account_code == "1100",
                    Transaction.credit_amount > 0,
                    or_(
                        Transaction.description.like(f"%from {flat.flat_number}%"),
                        Transaction.description.like(f"%Flat: {flat.flat_number}%"),
                        Transaction.description.like(f"%Flat {flat.flat_number}%")
                    )
                )
            ).order_by(Transaction.date.desc()).limit(1)
        )
        last_payment_date = last_payment_result.scalar()

        dues_report.append({
            "flat_number": flat.flat_number,
            "owner_name": flat.owner_name or flat_user_map.get(flat.flat_number, "Unknown"),
            "outstanding_bills": len(unpaid_bills),
            "outstanding_amount": float(outstanding_amount),
            "last_payment": last_payment_date.isoformat() if last_payment_date else "Never",
            "bills": [
                {
                    "month": bill.month,
                    "year": bill.year,
                    "amount": float(bill.total_amount)
                } for bill in unpaid_bills
            ]
        })

    return {
        "report_type": "Member Dues Report",
        "generated_at": datetime.utcnow(),
        "total_flats": len(flats),
        "flats_with_dues": len([d for d in dues_report if d["outstanding_amount"] > 0]),
        "total_outstanding": float(total_outstanding),
        "members": dues_report  # Changed from "dues_by_flat" to "members" to match frontend expectation
    }


@router.get("/member-ledger/{flat_id}")
async def member_transaction_ledger(
    flat_id: str,
    from_date: date = Query(None, description="Start date (optional)"),
    to_date: date = Query(None, description="End date (optional)"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Member Transaction Ledger - Detailed transaction history for a specific flat
    Ordinary members can only view their own ledger 
    Committee and Auditors can view any member's ledger
    """
    # RBAC: Only ADM, COM, and AUD roles can view any member's ledger
    from app.models_db import UserRole
    committee_auditor_roles = [
        UserRole.SUPER_ADMIN, 
        UserRole.ADMIN, 
        UserRole.ACCOUNTANT,
        UserRole.CHAIRMAN,
        UserRole.SECRETARY,
        UserRole.TREASURER,
        UserRole.AUDITOR
    ]
    
    try:
        flat_id_int = int(flat_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid flat ID")

    # If user is a typical resident, they can only request their own flat's ledger
    if current_user.role not in committee_auditor_roles:
        # Check if the requested flat_id matches the user's flat
        result = await db.execute(
            select(Flat).where(
                and_(
                    Flat.id == flat_id_int,
                    Flat.society_id == current_user.society_id,
                    Flat.flat_number == current_user.apartment_number
                )
            )
        )
        flat = result.scalar_one_or_none()
        if not flat:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own flat's ledger. Access to other member data is prohibited."
            )
    else:
        # Committee/Auditor can view any flat in the society
        result = await db.execute(
            select(Flat).where(
                and_(
                    Flat.id == flat_id_int, 
                    Flat.society_id == current_user.society_id
                )
            )
        )
        flat = result.scalar_one_or_none()
        if not flat:
            raise HTTPException(status_code=404, detail="Flat not found in this society")

    # Check permission - optional check if permission system is used for committee
    user_id_int = int(current_user.id)
    has_permission = await check_permission(
        user_id=user_id_int,
        permission_code="reports.view",
        db=db
    )
    if not has_permission:
        # If they are a resident viewing their own ledger, we allow it even without explicit 'reports.view'
        if current_user.role not in [UserRole.RESIDENT]:
             pass

    # Get bills for this flat
    result = await db.execute(
        select(MaintenanceBillDB)
        .where(MaintenanceBillDB.flat_id == flat_id_int)
        .order_by(MaintenanceBillDB.year, MaintenanceBillDB.month)
    )
    bills = result.scalars().all()

    transactions = []
    total_billed = 0.0
    total_paid = 0.0

    for bill in bills:
        bill_status = bill.status.value if hasattr(bill.status, 'value') else str(bill.status)
        transactions.append({
            "date": f"{bill.year}-{bill.month:02d}",
            "description": f"Maintenance bill for {bill.month}/{bill.year}",
            "amount": bill.total_amount,
            "status": bill_status,
            "paid_at": bill.paid_date
        })

        total_billed += bill.total_amount
        if bill_status == "paid":
            total_paid += bill.total_amount

    return {
        "report_type": "Member Transaction Ledger",
        "flat": {
            "flat_number": flat.flat_number,
            "owner_name": flat.owner_name,
            "area_sqft": flat.area_sqft,
            "occupants": flat.occupants
        },
        "period": {
            "from": from_date,
            "to": to_date
        },
        "transactions": transactions,
        "summary": {
            "total_billed": total_billed,
            "total_paid": total_paid,
            "outstanding": total_billed - total_paid
        }
    }


@router.get("/trial-balance", response_model=TrialBalanceResponse)
async def trial_balance_report(
    as_on_date: date = Query(..., description="Date for trial balance (YYYY-MM-DD)"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Trial Balance Report
    Shows all account balances as on a specific date within the current Financial Year
    Restricted to Committee and Auditors 
    """
    # RBAC: Only ADM, COM, and AUD roles can view full financial reports
    from app.models_db import UserRole
    allowed_roles = [
        UserRole.SUPER_ADMIN, 
        UserRole.ADMIN, 
        UserRole.ACCOUNTANT,
        UserRole.CHAIRMAN,
        UserRole.SECRETARY,
        UserRole.TREASURER,
        UserRole.AUDITOR
    ]
    
    if current_user.role not in allowed_roles:
         raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Trial Balance is an internal audit report and is restricted to Committee and Auditors."
        )

    # Check permission - auditors can view reports
    user_id_int = int(current_user.id)
    has_permission = await check_permission(
        user_id=user_id_int,
        permission_code="reports.view",
        db=db
    )
    if not has_permission:
        pass
    
    # Find the financial year that contains as_on_date
    # Use first() instead of scalar_one_or_none() to handle cases where multiple years might overlap
    result = await db.execute(
        select(FinancialYear).where(
            and_(
                FinancialYear.society_id == current_user.society_id,
                FinancialYear.start_date <= as_on_date,
                FinancialYear.end_date >= as_on_date
            )
        ).order_by(FinancialYear.start_date.desc())
    )
    financial_year = result.scalars().first()
    
    if not financial_year:
        # If no financial year found, try to get active financial year
        result = await db.execute(
            select(FinancialYear).where(
                and_(
                    FinancialYear.society_id == current_user.society_id,
                    FinancialYear.is_active == True
                )
            ).order_by(FinancialYear.start_date.desc())
        )
        financial_year = result.scalars().first()
        
        if not financial_year:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No financial year found. Please create a financial year first."
            )
    
    # Use financial year start date as the beginning point
    fy_start_date = financial_year.start_date
    # Use as_on_date or FY end date, whichever is earlier
    effective_date = min(as_on_date, financial_year.end_date)
    
    # Get all account codes
    result = await db.execute(
        select(AccountCode).where(AccountCode.society_id == current_user.society_id)
        .order_by(AccountCode.code)
    )
    accounts = result.scalars().all()
    
    # Get opening balances for this financial year
    opening_balances_result = await db.execute(
        select(OpeningBalance, AccountCode).join(
            AccountCode, OpeningBalance.account_head_id == AccountCode.id
        ).where(
            OpeningBalance.financial_year_id == financial_year.id,
            AccountCode.society_id == current_user.society_id
        )
    )
    opening_balances = {}
    for ob, ac in opening_balances_result.all():
        opening_balances[ac.code] = ob
    
    # GOLDEN RULE 2: Trial Balance must get net balance from General Ledger only
    # We calculate balances from transactions (which form the General Ledger)
    # Then extract net debit or credit balance for each account
    # This ensures Trial Balance is derived from General Ledger (Golden Rule 2)
    
    items = []
    total_debit = Decimal("0.00")
    total_credit = Decimal("0.00")
    
    for account in accounts:
        # Get opening balance for this account from OpeningBalance table
        opening_balance = opening_balances.get(account.code)
        if opening_balance:
            # Convert opening balance based on balance_type
            if opening_balance.balance_type == BalanceType.DEBIT:
                balance = Decimal(str(opening_balance.opening_balance))
            else:  # credit
                balance = -Decimal(str(opening_balance.opening_balance))  # Credit stored as negative
        else:
            # Fallback to account's opening_balance field if no OpeningBalance record
            balance = Decimal(str(account.opening_balance or 0.0))
            # For Liability, Capital, and Income, opening balance is Credit (negative in this logic)
            if account.type in ['liability', 'capital', 'income']:
                balance = -balance
        
        # Get all transactions for this account from FY start to as_on_date
        # expense_month is a string (e.g., "December, 2025"), so we can't compare it directly to dates
        # Instead, use date field for date range filtering, and expense_month for exact month matching
        # For ledger purposes, we'll use the date field which is more reliable for date range queries
        transactions_result = await db.execute(
            select(Transaction).where(
                and_(
                    Transaction.society_id == current_user.society_id,
                    Transaction.account_code == account.code,
                    Transaction.date >= fy_start_date,
                    Transaction.date <= effective_date
                )
            ).order_by(Transaction.date, Transaction.id)
        )
        transactions = transactions_result.scalars().all()
        
        # Calculate balance from transactions
        for txn in transactions:
            # Update balance based on account type and debit/credit
            debit = Decimal(str(txn.debit_amount or 0.0))
            credit = Decimal(str(txn.credit_amount or 0.0))
            
            if account.type in ['asset', 'expense']:
                # Asset/Expense: Debit increases, Credit decreases
                balance += debit
                balance -= credit
            else:  # liability, capital, income
                # Liability/Capital/Income: Credit increases (negative), Debit decreases
                balance += debit  # Debit decreases credit balance
                balance -= credit  # Credit increases (more negative)
        
        # Skip accounts with zero balance
        if abs(balance) < Decimal("0.01"):
            continue
        
        # Determine debit/credit based on account type and calculated balance
        # Asset and Expense accounts: positive balance = debit, negative balance = credit
        # Liability, Capital, and Income accounts: positive balance = credit, negative balance = debit
        
        if account.type in ['asset', 'expense']:
            # Asset/Expense accounts normally have debit balances
            if balance > 0:
                # Normal debit balance
                items.append(TrialBalanceItem(
                    account_code=account.code,
                    account_name=account.name,
                    debit_balance=float(balance.quantize(Decimal("0.01"))),
                    credit_balance=0.0
                ))
                total_debit += balance
            elif balance < 0:
                # Abnormal credit balance (contra account)
                items.append(TrialBalanceItem(
                    account_code=account.code,
                    account_name=account.name,
                    debit_balance=0.0,
                    credit_balance=float(abs(balance).quantize(Decimal("0.01")))
                ))
                total_credit += abs(balance)
        else:  # liability, capital, income
            # Liability/Capital/Income accounts normally have credit balances (stored as negative)
            if balance < 0:
                # Normal credit balance (stored as negative, display as positive credit)
                items.append(TrialBalanceItem(
                    account_code=account.code,
                    account_name=account.name,
                    debit_balance=0.0,
                    credit_balance=float(abs(balance).quantize(Decimal("0.01")))
                ))
                total_credit += abs(balance)
            elif balance > 0:
                # Abnormal debit balance (contra account)
                items.append(TrialBalanceItem(
                    account_code=account.code,
                    account_name=account.name,
                    debit_balance=float(balance.quantize(Decimal("0.01"))),
                    credit_balance=0.0
                ))
                total_debit += balance
    
    difference = abs(total_debit - total_credit)
    is_balanced = difference < Decimal("0.01")
    
    return TrialBalanceResponse(
        as_on_date=as_on_date,
        items=items,
        total_debit=float(total_debit.quantize(Decimal("0.01"))),
        total_credit=float(total_credit.quantize(Decimal("0.01"))),
        difference=float(difference.quantize(Decimal("0.01"))),
        is_balanced=is_balanced
    )


async def generate_account_ledger(
    db: AsyncSession,
    society_id: int,
    account: AccountCode,
    from_date: date,
    to_date: date
) -> Optional[LedgerResponse]:
    """Helper function to generate a ledger for a specific account"""
    account_code = account.code
    
    # Find the financial year for the period
    result = await db.execute(
        select(FinancialYear).where(
            and_(
                FinancialYear.society_id == society_id,
                FinancialYear.start_date <= from_date,
                FinancialYear.end_date >= from_date
            )
        ).order_by(FinancialYear.start_date.desc())
    )
    financial_year = result.scalars().first()
    
    if not financial_year:
        # Fallback to active financial year
        result = await db.execute(
            select(FinancialYear).where(
                and_(
                    FinancialYear.society_id == society_id,
                    FinancialYear.is_active == True
                )
            ).order_by(FinancialYear.start_date.desc())
        )
        financial_year = result.scalars().first()
        
        if not financial_year:
            return None

    fy_start_date = financial_year.start_date
    
    # 1. Start with opening balance from FY
    result = await db.execute(
        select(OpeningBalance).where(
            and_(
                OpeningBalance.financial_year_id == financial_year.id,
                OpeningBalance.account_head_id == account.id
            )
        )
    )
    ob_record = result.scalar_one_or_none()
    
    if ob_record:
        if ob_record.balance_type == BalanceType.DEBIT:
            balance = Decimal(str(ob_record.opening_balance))
        else:
            balance = -Decimal(str(ob_record.opening_balance))
    else:
        balance = Decimal(str(account.opening_balance or 0.0))
        if account.type in ['liability', 'capital', 'income']:
            balance = -balance

    # 2. Add movements between FY start and from_date - 1
    # Use date field for date range filtering (expense_month is string format, not suitable for range queries)
    if from_date > fy_start_date:
        result = await db.execute(
            select(
                func.sum(Transaction.debit_amount).label('dr'),
                func.sum(Transaction.credit_amount).label('cr')
            ).where(
                and_(
                    Transaction.society_id == society_id,
                    Transaction.account_code == account_code,
                    Transaction.date >= fy_start_date,
                    Transaction.date < from_date
                )
            )
        )
        movements = result.one_or_none()
        if movements:
            dr = Decimal(str(movements.dr or 0.0))
            cr = Decimal(str(movements.cr or 0.0))
            balance += (dr - cr)

    opening_balance_at_start = balance

    # 3. Get transactions during the period
    # Use date field for date range filtering (expense_month is string format, not suitable for range queries)
    # IMPORTANT: Eager load journal_entry to avoid N+1 queries
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(Transaction)
        .where(
            and_(
                Transaction.society_id == society_id,
                Transaction.account_code == account_code,
                Transaction.date >= from_date,
                Transaction.date <= to_date
            )
        )
        .options(selectinload(Transaction.journal_entry).selectinload(JournalEntry.attachments))
        .order_by(Transaction.date, Transaction.id)
    )
    transactions = result.scalars().all()
    
    # Include account if it has opening balance OR transactions in the period
    # This ensures accounts with opening balances are shown even if no transactions in period
    if abs(opening_balance_at_start) < Decimal("0.01") and not transactions:
        return None

    entries = []
    current_running_balance = opening_balance_at_start
    total_debit = Decimal("0.00")
    total_credit = Decimal("0.00")
    
    # Pre-fetch all journal entries referenced by transactions to avoid N+1 queries
    jv_ids = [txn.journal_entry_id for txn in transactions if txn.journal_entry_id]
    jv_map = {}
    if jv_ids:
        jv_result = await db.execute(
            select(JournalEntry).where(JournalEntry.id.in_(jv_ids))
        )
        for jv in jv_result.scalars().all():
            jv_map[jv.id] = jv.entry_number
    
    for txn in transactions:
        dr = Decimal(str(txn.debit_amount or 0.0))
        cr = Decimal(str(txn.credit_amount or 0.0))
        
        total_debit += dr
        total_credit += cr
        
        # Update balance based on account type
        if account.type in ['asset', 'expense']:
            # Asset/Expense: Debit increases, Credit decreases
            current_running_balance += (dr - cr)
        else:
            # Liability/Capital/Income: Credit increases (negative), Debit decreases
            current_running_balance += (dr - cr)
        
        # Display balance logic
        display_balance = current_running_balance
        if account.type in ['liability', 'capital', 'income']:
            display_balance = -current_running_balance
            
        # Get JV number from journal_entry if document_number is None
        # IMPORTANT: Show JV number (entry_number) as reference, not "N/A" or None
        reference = txn.document_number
        if not reference and txn.journal_entry_id:
            # Use pre-fetched JV map
            reference = jv_map.get(txn.journal_entry_id)
        
        # If still no reference, try to get from eager-loaded relationship
        if not reference and hasattr(txn, 'journal_entry') and txn.journal_entry:
            reference = txn.journal_entry.entry_number
        
        entries.append(LedgerEntry(
            date=txn.date,
            description=txn.description,  # This should be "Maintenance bill generated for {month} {year}" or similar
            reference=reference or f"JV-{txn.journal_entry_id}" if txn.journal_entry_id else "Manual Entry",  # Show JV number or fallback
            debit=float(dr.quantize(Decimal("0.01"))),
            credit=float(cr.quantize(Decimal("0.01"))),
            balance=float(display_balance.quantize(Decimal("0.01"))),
            journal_entry_id=txn.journal_entry_id,
            has_attachment=len(txn.journal_entry.attachments) > 0 if txn.journal_entry else False
        ))
        
    final_opening = opening_balance_at_start
    final_closing = current_running_balance
    
    if account.type in ['liability', 'capital', 'income']:
        final_opening = -opening_balance_at_start
        final_closing = -current_running_balance

    return LedgerResponse(
        account_code=account.code,
        account_name=account.name,
        from_date=from_date,
        to_date=to_date,
        opening_balance=float(final_opening.quantize(Decimal("0.01"))),
        entries=entries,
        total_debit=float(total_debit.quantize(Decimal("0.01"))),
        total_credit=float(total_credit.quantize(Decimal("0.01"))),
        closing_balance=float(final_closing.quantize(Decimal("0.01")))
    )


@router.get("/ledger", response_model=Any)
async def account_ledger_report(
    from_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    to_date: date = Query(..., description="End date (YYYY-MM-DD)"),
    account_code: str = Query(..., description="Account code (or 'all')"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Account Ledger Report
    Shows detailed transaction ledger for a specific account with running balance.
    """
    # Check permission
    user_id_int = int(current_user.id)
    has_permission = await check_permission(
        user_id=user_id_int,
        permission_code="reports.view",
        db=db
    )
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view reports."
        )
    
    if account_code.lower() == 'all':
        # Get all accounts
        result = await db.execute(
            select(AccountCode).where(AccountCode.society_id == current_user.society_id).order_by(AccountCode.code)
        )
        accounts = result.scalars().all()
        
        all_ledgers = []
        for account in accounts:
            ledger = await generate_account_ledger(db, current_user.society_id, account, from_date, to_date)
            if ledger:
                all_ledgers.append(ledger)
                
        return BulkLedgerResponse(
            from_date=from_date,
            to_date=to_date,
            ledgers=all_ledgers
        )
    else:
        # Get account details
        result = await db.execute(
            select(AccountCode).where(
                and_(
                    AccountCode.society_id == current_user.society_id,
                    AccountCode.code == account_code
                )
            )
        )
        account = result.scalar_one_or_none()
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Account with code {account_code} not found."
            )
            
        ledger = await generate_account_ledger(db, current_user.society_id, account, from_date, to_date)
        if not ledger:
            # Return empty ledger if no transactions and no opening balance
            return LedgerResponse(
                account_code=account.code,
                account_name=account.name,
                from_date=from_date,
                to_date=to_date,
                opening_balance=0.0,
                entries=[],
                total_debit=0.0,
                total_credit=0.0,
                closing_balance=0.0
            )
        return ledger


@router.get("/cash-book")
async def cash_book_ledger(
    from_date: date = Query(..., description="Start date"),
    to_date: date = Query(..., description="End date"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Cash Book Ledger
    Shows all cash transactions (where payment_method = 'cash')
    Auditors can view this report
    """
    # Check permission - auditors can view reports
    user_id_int = int(current_user.id)
    has_permission = await check_permission(
        user_id=user_id_int,
        permission_code="reports.view",
        db=db
    )
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view reports."
        )
    # Get cash account codes and their opening balances
    result = await db.execute(
        select(AccountCode).where(
            AccountCode.society_id == current_user.society_id,
            AccountCode.code.like('1010%')  # Cash accounts
        )
    )
    cash_account_records = result.scalars().all()
    cash_accounts = [ac.code for ac in cash_account_records]
    
    # Base opening balance from AccountCode table
    opening_balance = sum(Decimal(str(ac.opening_balance or 0.0)) for ac in cash_account_records)
    
    # Add movements BEFORE from_date to get true opening balance at from_date
    prev_result = await db.execute(
        select(
            func.sum(Transaction.debit_amount).label('dr'),
            func.sum(Transaction.credit_amount).label('cr')
        ).where(
            and_(
                Transaction.society_id == current_user.society_id,
                Transaction.date < from_date,
                or_(
                    Transaction.payment_method == 'cash',
                    Transaction.account_code.in_(cash_accounts) if cash_accounts else False
                )
            )
        )
    )
    prev_totals = prev_result.one_or_none()
    if prev_totals and prev_totals.dr is not None:
        opening_balance += (Decimal(str(prev_totals.dr)) - Decimal(str(prev_totals.cr or 0)))

    # Get all cash transactions in the actual period
    result = await db.execute(
        select(Transaction).where(
            and_(
                Transaction.society_id == current_user.society_id,
                Transaction.date >= from_date,
                Transaction.date <= to_date,
                or_(
                    Transaction.payment_method == 'cash',
                    Transaction.account_code.in_(cash_accounts) if cash_accounts else False
                )
            )
        ).order_by(Transaction.date, Transaction.id)
    )
    transactions = result.scalars().all()
    
    closing_balance = opening_balance
    receipts = []
    payments = []
    
    for txn in transactions:
        dr = Decimal(str(txn.debit_amount or 0.0))
        cr = Decimal(str(txn.credit_amount or 0.0))
        if dr > 0:  # Receipt (cash coming in)
            receipts.append({
                "date": txn.date,
                "description": txn.description,
                "amount": float(dr.quantize(Decimal("0.01"))),
                "account_code": txn.account_code,
            })
            closing_balance += dr
        elif cr > 0:  # Payment (cash going out)
            payments.append({
                "date": txn.date,
                "description": txn.description,
                "amount": float(cr.quantize(Decimal("0.01"))),
                "account_code": txn.account_code,
            })
            closing_balance -= cr
    
    total_receipts = sum(Decimal(str(r["amount"])) for r in receipts)
    total_payments = sum(Decimal(str(p["amount"])) for p in payments)
    
    return {
        "report_type": "Cash Book Ledger",
        "period": {
            "from": from_date,
            "to": to_date
        },
        "opening_balance": float(opening_balance.quantize(Decimal("0.01"))),
        "receipts": receipts,
        "payments": payments,
        "total_receipts": float(total_receipts.quantize(Decimal("0.01"))),
        "total_payments": float(total_payments.quantize(Decimal("0.01"))),
        "closing_balance": float((opening_balance + total_receipts - total_payments).quantize(Decimal("0.01")))
    }


@router.get("/general-ledger")
async def general_ledger_report(
    from_date: date = Query(..., description="Start date"),
    to_date: date = Query(..., description="End date"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    General Ledger Report
    Consolidated transaction ledger of ALL accounts, grouped by account head.
    Shows all transactions with correct debit/credit handling and balances.
    """
    # Check permission
    user_id_int = int(current_user.id)
    has_permission = await check_permission(
        user_id=user_id_int,
        permission_code="reports.view",
        db=db
    )
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view reports."
        )
    
    # Get society info
    society_info = await get_society_info(current_user.society_id, db)
    
    # Get ALL account codes
    result = await db.execute(
        select(AccountCode).where(AccountCode.society_id == current_user.society_id).order_by(AccountCode.code)
    )
    account_codes = result.scalars().all()
    
    # Find the financial year for the period
    result = await db.execute(
        select(FinancialYear).where(
            and_(
                FinancialYear.society_id == current_user.society_id,
                FinancialYear.start_date <= from_date,
                FinancialYear.end_date >= from_date
            )
        ).order_by(FinancialYear.start_date.desc())
    )
    financial_year = result.scalars().first()
    
    if not financial_year:
        # Fallback to active financial year
        result = await db.execute(
            select(FinancialYear).where(
                and_(
                    FinancialYear.society_id == current_user.society_id,
                    FinancialYear.is_active == True
                )
            ).order_by(FinancialYear.start_date.desc())
        )
        financial_year = result.scalars().first()
    
    fy_start_date = financial_year.start_date if financial_year else from_date
    
    # Get all transactions in the period
    result = await db.execute(
        select(Transaction).where(
            and_(
                Transaction.society_id == current_user.society_id,
                Transaction.date >= from_date,
                Transaction.date <= to_date
            )
        )
        .options(selectinload(Transaction.journal_entry))
        .order_by(Transaction.date, Transaction.id)
    )
    transactions = result.scalars().all()
    
    # Pre-fetch opening balances for all accounts if FY exists
    opening_balances_map = {}
    if financial_year:
        ob_res = await db.execute(
            select(OpeningBalance).where(OpeningBalance.financial_year_id == financial_year.id)
        )
        for ob in ob_res.scalars().all():
            opening_balances_map[ob.account_head_id] = ob
            
    ledger_by_account = {}
    
    # 2. Optimized: Pre-calculate opening balance movements for ALL accounts in one query
    opening_movements = {}
    if from_date > fy_start_date:
        m_res = await db.execute(
            select(
                Transaction.account_code,
                func.sum(Transaction.debit_amount).label('dr'),
                func.sum(Transaction.credit_amount).label('cr')
            ).where(
                and_(
                    Transaction.society_id == current_user.society_id,
                    Transaction.date >= fy_start_date,
                    Transaction.date < from_date
                )
            ).group_by(Transaction.account_code)
        )
        for row in m_res.all():
            opening_movements[row.account_code] = (Decimal(str(row.dr or 0.0)), Decimal(str(row.cr or 0.0)))

    # Initialize ledger entries for each account
    for account in account_codes:
        # 1. Start with FY opening balance
        ob_record = opening_balances_map.get(account.id)
        if ob_record:
            if ob_record.balance_type == BalanceType.DEBIT:
                balance = Decimal(str(ob_record.opening_balance))
            else:
                balance = -Decimal(str(ob_record.opening_balance))
        else:
            balance = Decimal(str(account.opening_balance or 0.0))
            if account.type in ['liability', 'capital', 'income']:
                balance = -balance
        
        # 2. Add movements between FY start and from_date - 1 (from optimized map)
        if from_date > fy_start_date:
            dr_m, cr_m = opening_movements.get(account.code, (Decimal("0.00"), Decimal("0.00")))
            balance += (dr_m - cr_m)
        
        # Display balance logic (convert internal credit-as-negative to display format)
        display_opening = balance
        if account.type in ['liability', 'capital', 'income']:
            display_opening = -balance
            
        ledger_by_account[account.code] = {
            "account_code": account.code,
            "account_name": account.name,
            "account_type": account.type.value if hasattr(account.type, 'value') else str(account.type),
            "internal_balance": balance, # Use this for ongoing calculations
            "opening_balance": display_opening,
            "transactions": [],
            "total_debit": Decimal("0.00"),
            "total_credit": Decimal("0.00"),
            "closing_balance": display_opening # Will be updated after transactions
        }
    
    # Process transactions
    total_gl_debit = Decimal("0.00")
    total_gl_credit = Decimal("0.00")
    
    # Pre-fetch JV map for performance
    jv_ids = [txn.journal_entry_id for txn in transactions if txn.journal_entry_id]
    jv_map = {}
    if jv_ids:
        jv_res = await db.execute(select(JournalEntry).where(JournalEntry.id.in_(jv_ids)))
        for jv in jv_res.scalars().all():
            jv_map[jv.id] = jv.entry_number

    for txn in transactions:
        account_code = txn.account_code
        if account_code not in ledger_by_account:
            # Dynamic account creation if missing (unlikely if account_codes list is complete)
            ledger_by_account[account_code] = {
                "account_code": account_code,
                "account_name": txn.category or account_code,
                "account_type": txn.type.value if hasattr(txn.type, 'value') else str(txn.type),
                "internal_balance": Decimal("0.00"),
                "opening_balance": Decimal("0.00"),
                "transactions": [],
                "total_debit": Decimal("0.00"),
                "total_credit": Decimal("0.00"),
                "closing_balance": Decimal("0.00")
            }
        
        dr = Decimal(str(txn.debit_amount or 0.0))
        cr = Decimal(str(txn.credit_amount or 0.0))
        
        total_gl_debit += dr
        total_gl_credit += cr
        
        ledger_by_account[account_code]["total_debit"] += dr
        ledger_by_account[account_code]["total_credit"] += cr
        
        # Update internal balance
        ledger_by_account[account_code]["internal_balance"] += (dr - cr)
        
        # Calculate closing balance for display
        new_balance = ledger_by_account[account_code]["internal_balance"]
        if ledger_by_account[account_code]["account_type"] in ['liability', 'capital', 'income']:
            ledger_by_account[account_code]["closing_balance"] = -new_balance
        else:
            ledger_by_account[account_code]["closing_balance"] = new_balance
        
        # Determine reference (priority: document_number > JV number)
        reference = txn.document_number
        if not reference and txn.journal_entry_id:
            reference = jv_map.get(txn.journal_entry_id)
        
        # Calculate row-level balance (adjusted for account type)
        row_balance = new_balance
        if ledger_by_account[account_code]["account_type"] in ['liability', 'capital', 'income']:
            row_balance = -new_balance

        ledger_by_account[account_code]["transactions"].append({
            "date": txn.date,
            "description": txn.description,
            "reference": reference or "",
            "debit": float(dr.quantize(Decimal("0.01"))),
            "credit": float(cr.quantize(Decimal("0.01"))),
            "balance": float(row_balance.quantize(Decimal("0.01")))
        })
    
    # GOLDEN RULE 1: Validate that General Ledger Debit = Credit
    gl_difference = abs(total_gl_debit - total_gl_credit)
    if gl_difference > Decimal("0.01"):
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"GENERAL LEDGER IMBALANCE: Total Debit={total_gl_debit}, Total Credit={total_gl_credit}, Difference={gl_difference}")
        # Don't raise exception, but log the error - this should never happen if double-entry is enforced
    
    # Prepare entries for response, converting Decimals to floats
    # Include accounts that have transactions OR non-zero opening/closing balance
    ledger_entries = []
    for entry in ledger_by_account.values():
        has_transactions = len(entry["transactions"]) > 0
        has_opening_balance = abs(entry["opening_balance"]) > Decimal("0.01")
        has_closing_balance = abs(entry["closing_balance"]) > Decimal("0.01")
        
        # Include account if it has transactions, opening balance, or closing balance
        if has_transactions or has_opening_balance or has_closing_balance:
            # Create a copy with float conversions and remove internal_balance
            formatted_entry = entry.copy()
            formatted_entry.pop("internal_balance", None) # Remove Decimal to avoid serialization error
            formatted_entry["opening_balance"] = float(entry["opening_balance"].quantize(Decimal("0.01")))
            formatted_entry["total_debit"] = float(entry["total_debit"].quantize(Decimal("0.01")))
            formatted_entry["total_credit"] = float(entry["total_credit"].quantize(Decimal("0.01")))
            formatted_entry["closing_balance"] = float(entry["closing_balance"].quantize(Decimal("0.01")))
            ledger_entries.append(formatted_entry)
    ledger_entries.sort(key=lambda x: x["account_code"])
    
    # Calculate summary based on INCOME and EXPENSE types (Include Capital in income for this view)
    total_income = Decimal("0.00")
    total_expense = Decimal("0.00")
    
    for entry_code, entry in ledger_by_account.items():
        if entry["account_type"] in ["income", "capital"]:
            # For income/capital, movements are credits
            total_income += entry["total_credit"] - entry["total_debit"]
        elif entry["account_type"] == "expense":
            # For expense, movements are debits
            total_expense += entry["total_debit"] - entry["total_credit"]
            
    return {
        "report_type": "General Ledger Report",
        "society": society_info,
        "period": {
            "from": from_date,
            "to": to_date
        },
        "generated_at": datetime.utcnow(),
        "ledger_entries": ledger_entries,
        "summary": {
            "total_income_accounts": len([e for e in ledger_entries if e["account_type"] == "income"]),
            "total_expense_accounts": len([e for e in ledger_entries if e["account_type"] == "expense"]),
            "total_income": float(total_income.quantize(Decimal("0.01"))),
            "total_expense": float(total_expense.quantize(Decimal("0.01"))),
            "net_income": float((total_income - total_expense).quantize(Decimal("0.01")))
        },
        # GOLDEN RULE 1: General Ledger totals for validation
        "general_ledger_totals": {
            "total_debit": float(total_gl_debit.quantize(Decimal("0.01"))),
            "total_credit": float(total_gl_credit.quantize(Decimal("0.01"))),
            "difference": float(gl_difference.quantize(Decimal("0.01"))),
            "is_balanced": gl_difference < Decimal("0.01")
        }
    }


@router.get("/bank-ledger")
async def bank_ledger(
    from_date: date = Query(..., description="Start date"),
    to_date: date = Query(..., description="End date"),
    account_code: Optional[str] = Query(None, description="Specific bank account code"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Bank Ledger
    Shows all bank transactions (where payment_method = 'bank')
    Can filter by specific bank account code
    Auditors can view this report
    """
    # Check permission - auditors can view reports
    user_id_int = int(current_user.id)
    has_permission = await check_permission(
        user_id=user_id_int,
        permission_code="reports.view",
        db=db
    )
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view reports."
        )
    # Get bank account records and codes
    if account_code:
        result = await db.execute(
            select(AccountCode).where(
                AccountCode.society_id == current_user.society_id,
                AccountCode.code == account_code
            )
        )
    else:
        result = await db.execute(
            select(AccountCode).where(
                AccountCode.society_id == current_user.society_id,
                AccountCode.code.like('100%'),  # Bank accounts
                AccountCode.type == 'asset'
            )
        )
    bank_account_records = result.scalars().all()
    bank_accounts = [ac.code for ac in bank_account_records]
    
    if not bank_accounts:
        return {
            "report_type": "Bank Ledger",
            "period": {"from": from_date, "to": to_date},
            "opening_balance": 0.0,
            "transactions": [],
            "total_debit": 0.0,
            "total_credit": 0.0,
            "closing_balance": 0.0
        }

    # Base opening balance from AccountCode table
    opening_balance = sum(Decimal(str(ac.opening_balance or 0.0)) for ac in bank_account_records)
    
    # Add movements BEFORE from_date
    prev_result = await db.execute(
        select(
            func.sum(Transaction.debit_amount).label('dr'),
            func.sum(Transaction.credit_amount).label('cr')
        ).where(
            and_(
                Transaction.society_id == current_user.society_id,
                Transaction.date < from_date,
                or_(
                    Transaction.payment_method == 'bank',
                    Transaction.account_code.in_(bank_accounts)
                )
            )
        )
    )
    prev_totals = prev_result.one_or_none()
    if prev_totals and prev_totals.dr is not None:
        opening_balance += (Decimal(str(prev_totals.dr)) - Decimal(str(prev_totals.cr or 0)))

    # Get all bank transactions in period
    result = await db.execute(
        select(Transaction).where(
            and_(
                Transaction.society_id == current_user.society_id,
                Transaction.date >= from_date,
                Transaction.date <= to_date,
                or_(
                    Transaction.payment_method == 'bank',
                    Transaction.account_code.in_(bank_accounts)
                )
            )
        ).order_by(Transaction.date, Transaction.id)
    )
    transactions = result.scalars().all()
    
    transactions_list = []
    total_debit = Decimal("0.00")
    total_credit = Decimal("0.00")
    
    for txn in transactions:
        dr = Decimal(str(txn.debit_amount or 0.0))
        cr = Decimal(str(txn.credit_amount or 0.0))
        transactions_list.append({
            "date": txn.date,
            "description": txn.description,
            "debit": float(dr.quantize(Decimal("0.01"))),
            "credit": float(cr.quantize(Decimal("0.01"))),
            "balance": float((dr - cr).quantize(Decimal("0.01"))),
            "account_code": txn.account_code,
        })
        total_debit += dr
        total_credit += cr
    
    closing_balance = opening_balance + total_debit - total_credit
    
    return {
        "report_type": "Bank Ledger",
        "period": {
            "from": from_date,
            "to": to_date
        },
        "account_code": account_code,
        "opening_balance": float(opening_balance.quantize(Decimal("0.01"))),
        "transactions": transactions_list,
        "total_debit": float(total_debit.quantize(Decimal("0.01"))),
        "total_credit": float(total_credit.quantize(Decimal("0.01"))),
        "closing_balance": float(closing_balance.quantize(Decimal("0.01")))
    }


# ==================== EXPORT ENDPOINTS ====================

@router.get("/general-ledger/export/excel")
async def export_general_ledger_excel(
    from_date: date = Query(..., description="Start date"),
    to_date: date = Query(..., description="End date"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Export General Ledger Report to Excel format
    """
    # Check permission
    user_id_int = int(current_user.id)
    has_permission = await check_permission(
        user_id=user_id_int,
        permission_code="reports.view",
        db=db
    )
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to export reports."
        )
    
    # Get report data (reuse existing logic)
    report_data = await general_ledger_report(from_date, to_date, current_user, db)
    society_info = await get_society_info(current_user.society_id, db)
    
    # Format data for export
    export_data = {
        "from_date": str(from_date),
        "to_date": str(to_date),
        "ledger": {}
    }
    
    for entry in report_data["ledger_entries"]:
        account_code = entry["account_code"]
        export_data["ledger"][account_code] = {
            "account_name": entry["account_name"],
            "account_type": entry["account_type"],
            "opening_balance": entry["opening_balance"],
            "total_debit": entry["total_debit"],
            "total_credit": entry["total_credit"],
            "closing_balance": entry["closing_balance"],
            "transactions": [
                {
                    "date": str(txn["date"]),
                    "description": txn["description"],
                    "debit": txn["debit"],
                    "credit": txn["credit"],
                    "balance": txn.get("balance", 0)
                }
                for txn in entry["transactions"]
            ]
        }
    
    # Generate Excel file
    excel_file = ExcelExporter.create_general_ledger_excel(export_data, society_info)
    
    # Return as streaming response
    filename = f"General_Ledger_{from_date}_to_{to_date}.xlsx"
    return StreamingResponse(
        excel_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/general-ledger/export/pdf")
async def export_general_ledger_pdf(
    from_date: date = Query(..., description="Start date"),
    to_date: date = Query(..., description="End date"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Export General Ledger Report to PDF format
    """
    # Check permission
    user_id_int = int(current_user.id)
    has_permission = await check_permission(
        user_id=user_id_int,
        permission_code="reports.view",
        db=db
    )
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to export reports."
        )
    
    # Get report data
    report_data = await general_ledger_report(from_date, to_date, current_user, db)
    society_info = await get_society_info(current_user.society_id, db)
    
    # Format data for export
    export_data = {
        "from_date": str(from_date),
        "to_date": str(to_date),
        "ledger": {}
    }
    
    for entry in report_data["ledger_entries"]:
        account_code = entry["account_code"]
        export_data["ledger"][account_code] = {
            "account_name": entry["account_name"],
            "account_type": entry["account_type"],
            "opening_balance": entry["opening_balance"],
            "total_debit": entry["total_debit"],
            "total_credit": entry["total_credit"],
            "closing_balance": entry["closing_balance"],
            "transactions": [
                {
                    "date": str(txn["date"]),
                    "description": txn["description"],
                    "debit": txn["debit"],
                    "credit": txn["credit"],
                    "balance": txn.get("balance", 0)
                }
                for txn in entry["transactions"]
            ]
        }
    
    # Generate PDF file
    pdf_file = PDFExporter.create_general_ledger_pdf(export_data, society_info)
    
    # Return as streaming response
    filename = f"General_Ledger_{from_date}_to_{to_date}.pdf"
    return StreamingResponse(
        pdf_file,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/receipts-and-payments/export/excel")
async def export_receipts_payments_excel(
    from_date: date = Query(..., description="Start date"),
    to_date: date = Query(..., description="End date"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Export Receipts & Payments Report to Excel format
    """
    # Check permission
    user_id_int = int(current_user.id)
    has_permission = await check_permission(
        user_id=user_id_int,
        permission_code="reports.view",
        db=db
    )
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to export reports."
        )
    
    # Get report data
    report_data = await receipts_and_payments_report(from_date, to_date, current_user, db)
    society_info = await get_society_info(current_user.society_id, db)
    
    # Format for simple table export
    export_data = {
        "from_date": str(from_date),
        "to_date": str(to_date),
        "receipts": report_data["receipts"],
        "payments": report_data["payments"],
        "total_receipts": report_data["total_receipts"],
        "total_payments": report_data["total_payments"]
    }
    
    # Generate Excel (using simple report template)
    excel_file = ExcelExporter.create_simple_report_excel(
        export_data,
        society_info,
        "Receipts & Payments Report",
        ["Date", "Description", "Category", "Amount"],
        "receipts"  # You might want to create combined view
    )
    
    filename = f"Receipts_Payments_{from_date}_to_{to_date}.xlsx"
    return StreamingResponse(
        excel_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/receipts-and-payments/export/pdf")
async def export_receipts_payments_pdf(
    from_date: date = Query(..., description="Start date"),
    to_date: date = Query(..., description="End date"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Export Receipts & Payments Report to PDF format
    """
    # Check permission
    user_id_int = int(current_user.id)
    has_permission = await check_permission(
        user_id=user_id_int,
        permission_code="reports.view",
        db=db
    )
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to export reports."
        )
    
    # Get report data
    report_data = await receipts_and_payments_report(from_date, to_date, current_user, db)
    society_info = await get_society_info(current_user.society_id, db)
    
    # Format for export
    export_data = {
        "from_date": str(from_date),
        "to_date": str(to_date),
        "receipts": report_data["receipts"],
        "payments": report_data["payments"]
    }
    
    # Generate PDF
    pdf_file = PDFExporter.create_simple_report_pdf(
        export_data,
        society_info,
        "Receipts & Payments Report",
        ["Date", "Description", "Category", "Amount"],
        "receipts"
    )
    
    filename = f"Receipts_Payments_{from_date}_to_{to_date}.pdf"
    return StreamingResponse(
        pdf_file,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/cash-book/export/excel")
async def export_cash_book_excel(
    from_date: date = Query(..., description="Start date"),
    to_date: date = Query(..., description="End date"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Export Cash Book Ledger to Excel format
    """
    # Check permission
    user_id_int = int(current_user.id)
    has_permission = await check_permission(
        user_id=user_id_int,
        permission_code="reports.view",
        db=db
    )
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to export reports."
        )
    
    # Get report data
    report_data = await cash_book_ledger(from_date, to_date, current_user, db)
    society_info = await get_society_info(current_user.society_id, db)
    
    # Format for export - combine receipts and payments
    all_transactions = []
    for receipt in report_data.get("receipts", []):
        all_transactions.append({
            "date": str(receipt["date"]),
            "description": receipt["description"],
            "receipt": receipt["amount"],
            "payment": 0,
            "balance": 0  # Will calculate
        })
    
    for payment in report_data.get("payments", []):
        all_transactions.append({
            "date": str(payment["date"]),
            "description": payment["description"],
            "receipt": 0,
            "payment": payment["amount"],
            "balance": 0  # Will calculate
        })
    
    # Sort by date and calculate running balance
    all_transactions.sort(key=lambda x: x["date"])
    balance = report_data.get("opening_balance", 0)
    for txn in all_transactions:
        balance += txn["receipt"] - txn["payment"]
        txn["balance"] = balance
    
    export_data = {
        "from_date": str(from_date),
        "to_date": str(to_date),
        "transactions": all_transactions,
        "opening_balance": report_data.get("opening_balance", 0),
        "closing_balance": report_data.get("closing_balance", 0)
    }
    
    # Generate Excel
    excel_file = ExcelExporter.create_simple_report_excel(
        export_data,
        society_info,
        "Cash Book Ledger",
        ["Date", "Description", "Receipt", "Payment", "Balance"],
        "transactions"
    )
    
    filename = f"Cash_Book_{from_date}_to_{to_date}.xlsx"
    return StreamingResponse(
        excel_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/cash-book/export/pdf")
async def export_cash_book_pdf(
    from_date: date = Query(..., description="Start date"),
    to_date: date = Query(..., description="End date"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Export Cash Book Ledger to PDF format
    """
    # Check permission
    user_id_int = int(current_user.id)
    has_permission = await check_permission(
        user_id=user_id_int,
        permission_code="reports.view",
        db=db
    )
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to export reports."
        )
    
    # Get report data
    report_data = await cash_book_ledger(from_date, to_date, current_user, db)
    society_info = await get_society_info(current_user.society_id, db)
    
    # Format for export
    all_transactions = []
    for receipt in report_data.get("receipts", []):
        all_transactions.append({
            "date": str(receipt["date"]),
            "description": receipt["description"],
            "receipt": receipt["amount"],
            "payment": 0,
            "balance": 0
        })
    
    for payment in report_data.get("payments", []):
        all_transactions.append({
            "date": str(payment["date"]),
            "description": payment["description"],
            "receipt": 0,
            "payment": payment["amount"],
            "balance": 0
        })
    
    all_transactions.sort(key=lambda x: x["date"])
    balance = report_data.get("opening_balance", 0)
    for txn in all_transactions:
        balance += txn["receipt"] - txn["payment"]
        txn["balance"] = balance
    
    export_data = {
        "from_date": str(from_date),
        "to_date": str(to_date),
        "transactions": all_transactions
    }
    
    # Generate PDF
    pdf_file = PDFExporter.create_simple_report_pdf(
        export_data,
        society_info,
        "Cash Book Ledger",
        ["Date", "Description", "Receipt", "Payment", "Balance"],
        "transactions"
    )
    
    filename = f"Cash_Book_{from_date}_to_{to_date}.pdf"
    return StreamingResponse(
        pdf_file,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/bank-ledger/export/excel")
async def export_bank_ledger_excel(
    from_date: date = Query(..., description="Start date"),
    to_date: date = Query(..., description="End date"),
    account_code: Optional[str] = Query(None, description="Specific bank account code"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Export Bank Ledger to Excel format
    """
    # Check permission
    user_id_int = int(current_user.id)
    has_permission = await check_permission(
        user_id=user_id_int,
        permission_code="reports.view",
        db=db
    )
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to export reports."
        )
    
    # Get report data
    report_data = await bank_ledger(from_date, to_date, account_code, current_user, db)
    society_info = await get_society_info(current_user.society_id, db)
    
    export_data = {
        "from_date": str(from_date),
        "to_date": str(to_date),
        "transactions": report_data.get("transactions", [])
    }
    
    # Generate Excel
    excel_file = ExcelExporter.create_simple_report_excel(
        export_data,
        society_info,
        "Bank Ledger",
        ["Date", "Description", "Debit", "Credit", "Balance"],
        "transactions"
    )
    
    filename = f"Bank_Ledger_{from_date}_to_{to_date}.xlsx"
    return StreamingResponse(
        excel_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/bank-ledger/export/pdf")
async def export_bank_ledger_pdf(
    from_date: date = Query(..., description="Start date"),
    to_date: date = Query(..., description="End date"),
    account_code: Optional[str] = Query(None, description="Specific bank account code"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Export Bank Ledger to PDF format
    """
    # Check permission
    user_id_int = int(current_user.id)
    has_permission = await check_permission(
        user_id=user_id_int,
        permission_code="reports.view",
        db=db
    )
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to export reports."
        )
    
    # Get report data
    report_data = await bank_ledger(from_date, to_date, account_code, current_user, db)
    society_info = await get_society_info(current_user.society_id, db)
    
    export_data = {
        "from_date": str(from_date),
        "to_date": str(to_date),
        "transactions": report_data.get("transactions", [])
    }
    
    # Generate PDF
    pdf_file = PDFExporter.create_simple_report_pdf(
        export_data,
        society_info,
        "Bank Ledger",
        ["Date", "Description", "Debit", "Credit", "Balance"],
        "transactions"
    )
    
    filename = f"Bank_Ledger_{from_date}_to_{to_date}.pdf"
    return StreamingResponse(
        pdf_file,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/member-ledger/{flat_id}/export/excel")
async def export_member_ledger_excel(
    flat_id: str,
    from_date: Optional[date] = Query(None, description="Start date"),
    to_date: Optional[date] = Query(None, description="End date"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Export Member Transaction Ledger to Excel format
    """
    # Check permission
    user_id_int = int(current_user.id)
    has_permission = await check_permission(
        user_id=user_id_int,
        permission_code="reports.view",
        db=db
    )
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to export reports."
        )
    
    # Get report data
    report_data = await member_transaction_ledger(flat_id, from_date, to_date, current_user, db)
    society_info = await get_society_info(current_user.society_id, db)
    
    export_data = {
        "from_date": str(from_date) if from_date else "All Time",
        "to_date": str(to_date) if to_date else "All Time",
        "flat_number": report_data["flat"]["flat_number"],
        "owner_name": report_data["flat"].get("owner_name", "N/A"),
        "transactions": report_data.get("transactions", [])
    }
    
    # Generate Excel
    excel_file = ExcelExporter.create_simple_report_excel(
        export_data,
        society_info,
        f"Member Ledger - {report_data['flat']['flat_number']}",
        ["Date", "Description", "Amount", "Status"],
        "transactions"
    )
    
    filename = f"Member_Ledger_{report_data['flat']['flat_number']}.xlsx"
    return StreamingResponse(
        excel_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/member-ledger/{flat_id}/export/pdf")
async def export_member_ledger_pdf(
    flat_id: str,
    from_date: Optional[date] = Query(None, description="Start date"),
    to_date: Optional[date] = Query(None, description="End date"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Export Member Transaction Ledger to PDF format
    """
    # Check permission
    user_id_int = int(current_user.id)
    has_permission = await check_permission(
        user_id=user_id_int,
        permission_code="reports.view",
        db=db
    )
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to export reports."
        )
    
    # Get report data
    report_data = await member_transaction_ledger(flat_id, from_date, to_date, current_user, db)
    society_info = await get_society_info(current_user.society_id, db)
    
    export_data = {
        "from_date": str(from_date) if from_date else "All Time",
        "to_date": str(to_date) if to_date else "All Time",
        "flat_number": report_data["flat"]["flat_number"],
        "owner_name": report_data["flat"].get("owner_name", "N/A"),
        "transactions": report_data.get("transactions", [])
    }
    
    # Generate PDF
    pdf_file = PDFExporter.create_simple_report_pdf(
        export_data,
        society_info,
        f"Member Ledger - {report_data['flat']['flat_number']}",
        ["Date", "Description", "Amount", "Status"],
        "transactions"
    )
    
    filename = f"Member_Ledger_{report_data['flat']['flat_number']}.pdf"
    return StreamingResponse(
        pdf_file,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/trial-balance/export/excel")
async def export_trial_balance_excel(
    as_on_date: date = Query(..., description="Date for trial balance"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Export Trial Balance to Excel"""
    # Check permission
    user_id_int = int(current_user.id)
    has_permission = await check_permission(user_id=user_id_int, permission_code="reports.view", db=db)
    if not has_permission:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No permission")
        
    report_data = await trial_balance_report(as_on_date, current_user, db)
    society_info = await get_society_info(current_user.society_id, db)
    excel_file = ExcelExporter.create_trial_balance_excel(report_data, society_info)
    
    filename = f"Trial_Balance_{as_on_date}.xlsx"
    return StreamingResponse(
        excel_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/trial-balance/export/pdf")
async def export_trial_balance_pdf(
    as_on_date: date = Query(..., description="Date for trial balance"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Export Trial Balance to PDF"""
    user_id_int = int(current_user.id)
    has_permission = await check_permission(user_id=user_id_int, permission_code="reports.view", db=db)
    if not has_permission:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No permission")
        
    report_data = await trial_balance_report(as_on_date, current_user, db)
    society_info = await get_society_info(current_user.society_id, db)
    # Convert Pydantic model to dict for PDF export
    report_dict = report_data.model_dump() if hasattr(report_data, 'model_dump') else report_data.dict()
    pdf_file = PDFExporter.create_trial_balance_pdf(report_dict, society_info)
    
    filename = f"Trial_Balance_{as_on_date}.pdf"
    return StreamingResponse(
        pdf_file,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/income-and-expenditure/export/excel")
async def export_income_expenditure_excel(
    from_date: date = Query(...),
    to_date: date = Query(...),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Export Income & Expenditure to Excel"""
    user_id_int = int(current_user.id)
    has_permission = await check_permission(user_id=user_id_int, permission_code="reports.view", db=db)
    if not has_permission:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No permission")
        
    report_data = await income_and_expenditure_report(from_date, to_date, current_user, db)
    society_info = await get_society_info(current_user.society_id, db)
    excel_file = ExcelExporter.create_income_and_expenditure_excel(report_data, society_info)
    
    filename = f"Income_Expenditure_{from_date}_to_{to_date}.xlsx"
    return StreamingResponse(
        excel_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/income-and-expenditure/export/pdf")
async def export_income_expenditure_pdf(
    from_date: date = Query(...),
    to_date: date = Query(...),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Export Income & Expenditure to PDF"""
    user_id_int = int(current_user.id)
    has_permission = await check_permission(user_id=user_id_int, permission_code="reports.view", db=db)
    if not has_permission:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No permission")
        
    report_data = await income_and_expenditure_report(from_date, to_date, current_user, db)
    society_info = await get_society_info(current_user.society_id, db)
    # Convert Pydantic model to dict for PDF export if needed
    if hasattr(report_data, 'model_dump'):
        report_dict = report_data.model_dump()
    elif hasattr(report_data, 'dict'):
        report_dict = report_data.dict()
    else:
        report_dict = report_data
    pdf_file = PDFExporter.create_income_and_expenditure_pdf(report_dict, society_info)
    
    filename = f"Income_Expenditure_{from_date}_to_{to_date}.pdf"
    return StreamingResponse(
        pdf_file,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/balance-sheet/export/excel")
async def export_balance_sheet_excel(
    as_on_date: date = Query(...),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Export Balance Sheet to Excel"""
    user_id_int = int(current_user.id)
    has_permission = await check_permission(user_id=user_id_int, permission_code="reports.view", db=db)
    if not has_permission:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No permission")
        
    report_data = await balance_sheet_report(as_on_date, current_user, db)
    society_info = await get_society_info(current_user.society_id, db)
    excel_file = ExcelExporter.create_balance_sheet_excel(report_data, society_info)
    
    filename = f"Balance_Sheet_{as_on_date}.xlsx"
    return StreamingResponse(
        excel_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/balance-sheet/export/pdf")
async def export_balance_sheet_pdf(
    as_on_date: date = Query(...),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Export Balance Sheet to PDF"""
    user_id_int = int(current_user.id)
    has_permission = await check_permission(user_id=user_id_int, permission_code="reports.view", db=db)
    if not has_permission:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No permission")
        
    report_data = await balance_sheet_report(as_on_date, current_user, db)
    society_info = await get_society_info(current_user.society_id, db)
    # Convert Pydantic model to dict for PDF export if needed
    if hasattr(report_data, 'model_dump'):
        report_dict = report_data.model_dump()
    elif hasattr(report_data, 'dict'):
        report_dict = report_data.dict()
    else:
        report_dict = report_data
    pdf_file = PDFExporter.create_balance_sheet_pdf(report_dict, society_info)
    
    filename = f"Balance_Sheet_{as_on_date}.pdf"
    return StreamingResponse(
        pdf_file,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
@router.get("/member-ledger")
async def member_ledger_report(
    flat_id: Optional[int] = Query(None, description="Filter by Flat ID"),
    from_date: Optional[date] = Query(None, description="Start Date"),
    to_date: Optional[date] = Query(None, description="End Date"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Member Ledger Report
    Shows all bills (Dr) and payments (Cr) for a member/flat
    Reconciles with Accounts Receivable
    """
    if not flat_id:
        raise HTTPException(status_code=400, detail="Flat ID is required")

    # Get Flat Details
    result = await db.execute(select(Flat).where(Flat.id == flat_id))
    flat = result.scalar_one_or_none()
    if not flat:
        raise HTTPException(status_code=404, detail="Flat not found")

    # 1. Opening Balance (Sum of all bills - payments before from_date)
    opening_balance = 0.0
    if from_date:
        # Bills before from_date
        bill_res = await db.execute(
            select(func.sum(MaintenanceBillDB.total_amount)).where(
                and_(
                    MaintenanceBillDB.flat_id == flat_id,
                    MaintenanceBillDB.created_at < datetime.combine(from_date, datetime.min.time())
                )
            )
        )
        total_billed_prev = bill_res.scalar() or 0.0

        # Payments before from_date (linked to bills of this flat)
        # Note: Need Payment model import
        from app.models_db import Payment
        pay_res = await db.execute(
            select(func.sum(Payment.amount)).where(
                and_(
                    Payment.flat_id == flat_id,
                    Payment.payment_date < from_date
                )
            )
        )
        total_paid_prev = pay_res.scalar() or 0.0
        opening_balance = total_billed_prev - total_paid_prev

    # 2. Transactions during period
    ledger_entries = []
    
    # Get Bills
    bills_query = select(MaintenanceBillDB).where(
        and_(
            MaintenanceBillDB.flat_id == flat_id,
            MaintenanceBillDB.society_id == current_user.society_id
        )
    )
    if from_date:
        bills_query = bills_query.where(MaintenanceBillDB.created_at >= datetime.combine(from_date, datetime.min.time()))
    if to_date:
        bills_query = bills_query.where(MaintenanceBillDB.created_at <= datetime.combine(to_date, datetime.max.time()))
    
    bills_result = await db.execute(bills_query)
    bills = bills_result.scalars().all()

    for bill in bills:
        ledger_entries.append({
            "date": bill.created_at.date(),
            "description": f"Bill #{bill.bill_number} - {calendar.month_name[bill.month]} {bill.year}",
            "type": "DEBIT",
            "amount": bill.total_amount,
            "ref_id": bill.id
        })

    # Get Payments
    from app.models_db import Payment
    pay_query = select(Payment).where(
        and_(
            Payment.flat_id == flat_id,
            Payment.society_id == current_user.society_id
        )
    )
    if from_date:
        pay_query = pay_query.where(Payment.payment_date >= from_date)
    if to_date:
        pay_query = pay_query.where(Payment.payment_date <= to_date)
        
    pay_result = await db.execute(pay_query)
    payments = pay_result.scalars().all()

    for pay in payments:
        ledger_entries.append({
            "date": pay.payment_date,
            "description": f"Receipt #{pay.receipt_number} ({pay.payment_mode})",
            "type": "CREDIT",
            "amount": pay.amount,
            "ref_id": pay.id
        })

    # Sort entries by date
    ledger_entries.sort(key=lambda x: x['date'])

    # Calculate running balance
    running_balance = opening_balance
    final_entries = []
    
    # Add opening balance row
    if from_date:
        final_entries.append({
            "date": from_date,
            "description": "Opening Balance",
            "type": "OB",
            "debit": 0,
            "credit": 0,
            "balance": opening_balance
        })

    total_debit = 0
    total_credit = 0

    for entry in ledger_entries:
        debit = entry['amount'] if entry['type'] == 'DEBIT' else 0
        credit = entry['amount'] if entry['type'] == 'CREDIT' else 0
        running_balance += (debit - credit)
        
        total_debit += debit
        total_credit += credit

        final_entries.append({
            "date": entry['date'],
            "description": entry['description'],
            "type": entry['type'],
            "debit": debit,
            "credit": credit,
            "balance": running_balance
        })

    return {
        "flat_number": flat.flat_number,
        "opening_balance": opening_balance,
        "entries": final_entries,
        "closing_balance": running_balance,
        "total_debit": total_debit,
        "total_credit": total_credit
    }
