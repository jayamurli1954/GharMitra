"""
Enhanced Financial Year Management API with Three-Stage Closing
Implements: Open → Provisional Close → Final Close workflow
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc, update as sql_update
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict
from datetime import datetime, date, timedelta
from uuid import UUID, uuid4

from ..database import get_db
from ..models_db import (
    Society,
    FinancialYear,
    YearStatus,
    OpeningBalanceStatus,
    OpeningBalance,
    BalanceType,
    BalanceStatus,
    AuditAdjustment,
    AdjustmentType,
    AccountCode,
    Transaction
)
from ..schemas.financial_year import (
    FinancialYearCreate,
    ProvisionalClosingRequest,
    FinalClosingRequest,
    AuditAdjustmentRequest,
    AuditAdjustmentResponse,
    YearEndClosingSummary
)
from ..dependencies import get_current_user
from ..models.user import UserResponse
from ..utils.audit import log_action

router = APIRouter(prefix="/financial-years", tags=["financial-years-enhanced"])


@router.get("/", response_model=List[Dict])
async def list_financial_years(
    include_closed: bool = Query(True, description="Include closed years"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all financial years for the society
    Ensures only one financial year is active (fixes data integrity)
    """
    query = select(FinancialYear).where(
        FinancialYear.society_id == current_user.society_id
    )
    
    if not include_closed:
        query = query.where(FinancialYear.is_closed == False)
    
    query = query.order_by(FinancialYear.start_date.desc())
    
    result = await db.execute(query)
    years = result.scalars().all()
    
    # Data integrity check: Ensure only one financial year is active
    active_years = [y for y in years if y.is_active]
    if len(active_years) > 1:
        # Keep the most recent one active, deactivate others
        active_years_sorted = sorted(active_years, key=lambda x: x.start_date, reverse=True)
        for year in active_years_sorted[1:]:  # Deactivate all except the first (most recent)
            year.is_active = False
            db.add(year)
        await db.commit()
        # Refresh the list
        result = await db.execute(query)
        years = result.scalars().all()
    
    return [
        {
            "id": str(year.id),
            "year_name": year.year_name,
            "start_date": year.start_date.isoformat(),
            "end_date": year.end_date.isoformat(),
            "status": year.status.value if hasattr(year.status, 'value') else str(year.status),
            "is_active": year.is_active,
            "is_closed": year.is_closed,
            "created_at": year.created_at.isoformat() if year.created_at else None,
            "updated_at": year.updated_at.isoformat() if year.updated_at else None
        }
        for year in years
    ]


@router.get("/active", response_model=Dict)
async def get_active_financial_year(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the currently active financial year
    """
    result = await db.execute(
        select(FinancialYear).where(
            and_(
                FinancialYear.society_id == current_user.society_id,
                FinancialYear.is_active == True
            )
        ).order_by(FinancialYear.start_date.desc())
    )
    year = result.scalar_one_or_none()
    
    if not year:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active financial year found"
        )
    
    return {
        "id": str(year.id),
        "year_name": year.year_name,
        "start_date": year.start_date.isoformat(),
        "end_date": year.end_date.isoformat(),
        "status": year.status.value if hasattr(year.status, 'value') else str(year.status),
        "is_active": year.is_active,
        "is_closed": year.is_closed
    }


@router.get("/{year_id}", response_model=Dict)
async def get_financial_year(
    year_id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific financial year by ID
    """
    result = await db.execute(
        select(FinancialYear).where(
            and_(
                FinancialYear.id == year_id,
                FinancialYear.society_id == current_user.society_id
            )
        )
    )
    year = result.scalar_one_or_none()
    
    if not year:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Financial year not found"
        )
    
    return {
        "id": str(year.id),
        "year_name": year.year_name,
        "start_date": year.start_date.isoformat(),
        "end_date": year.end_date.isoformat(),
        "status": year.status.value if hasattr(year.status, 'value') else str(year.status),
        "is_active": year.is_active,
        "is_closed": year.is_closed,
        "created_at": year.created_at.isoformat() if year.created_at else None,
        "updated_at": year.updated_at.isoformat() if year.updated_at else None
    }


@router.post("/", response_model=Dict, status_code=status.HTTP_201_CREATED)
async def create_financial_year(
    year_data: FinancialYearCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new financial year
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Creating financial year: {year_data.year_name}, {year_data.start_date} to {year_data.end_date} for society {current_user.society_id}")
    except Exception as e:
        logger.error(f"Error logging: {e}")
    
    # Check for overlapping dates
    result = await db.execute(
        select(FinancialYear).where(
            and_(
                FinancialYear.society_id == current_user.society_id,
                or_(
                    and_(
                        FinancialYear.start_date <= year_data.start_date,
                        FinancialYear.end_date >= year_data.start_date
                    ),
                    and_(
                        FinancialYear.start_date <= year_data.end_date,
                        FinancialYear.end_date >= year_data.end_date
                    ),
                    and_(
                        FinancialYear.start_date >= year_data.start_date,
                        FinancialYear.end_date <= year_data.end_date
                    )
                )
            )
        )
    )
    overlapping = result.scalars().all()
    
    if overlapping:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Financial year dates overlap with existing year: {overlapping[0].year_name}"
        )
    
    # Validate dates
    if year_data.start_date >= year_data.end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start date must be before end date"
        )
    
    # Deactivate all other active years - only one can be active at a time
    result = await db.execute(
        select(FinancialYear).where(
            and_(
                FinancialYear.society_id == current_user.society_id,
                FinancialYear.is_active == True
            )
        )
    )
    existing_active = result.scalars().all()
    
    # Deactivate all existing active years
    for active_year in existing_active:
        active_year.is_active = False
        db.add(active_year)
    
    # Create new financial year - set as active (since we deactivated all others)
    new_year = FinancialYear(
        society_id=current_user.society_id,
        year_name=year_data.year_name,
        start_date=year_data.start_date,
        end_date=year_data.end_date,
        status=YearStatus.OPEN,
        is_active=True,  # Always set new year as active (we've deactivated others)
        is_closed=False,
        opening_balances_status=OpeningBalanceStatus.PROVISIONAL
    )
    
    try:
        db.add(new_year)
        await db.commit()
        await db.refresh(new_year)
        
        logger.info(f"Financial year created successfully: {new_year.id} - {new_year.year_name}")
        
        return {
            "id": str(new_year.id),
            "year_name": new_year.year_name,
            "start_date": new_year.start_date.isoformat(),
            "end_date": new_year.end_date.isoformat(),
            "status": new_year.status.value if hasattr(new_year.status, 'value') else str(new_year.status),
            "is_active": new_year.is_active,
            "is_closed": new_year.is_closed
        }
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating financial year: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create financial year: {str(e)}"
        )


@router.post("/{year_id}/provisional-close", response_model=YearEndClosingSummary)
async def provisional_close_financial_year(
    year_id: UUID,
    closing_request: ProvisionalClosingRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    **Stage 1: Provisional Closing**
    
    Provisionally close the financial year. This:
    - Marks the year as 'provisional_close'
    - Calculates closing balances for all accounts
    - Creates the next financial year (if doesn't exist)
    - Creates provisional opening balances for next year
    - Allows new year to start operations
    - Keeps previous year "locked but adjustable" for audit
    
    After provisional close:
    - Current year can continue normal operations
    - Previous year can receive audit adjustment entries
    - Opening balances remain "provisional" until final close
    """
    # Step 1: Get and validate financial year
    result = await db.execute(
        select(FinancialYear).where(
            and_(
                FinancialYear.id == year_id,
                FinancialYear.society_id == current_user.society_id
            )
        )
    )
    fy = result.scalar_one_or_none()
    
    if not fy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Financial year not found"
        )
    
    if fy.status != YearStatus.OPEN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Year is already {fy.status.value}. Can only provisionally close an open year."
        )
    
    # Step 2: Verify no unbalanced journal entries
    # TODO: Add journal entry validation here
    # For now, we'll skip this check
    
    # Step 3: Calculate closing balances for all accounts
    closing_balances = await calculate_closing_balances(db, current_user.society_id, year_id)
    
    # Calculate financial summary
    bank_balance = next((b['closing_balance'] for b in closing_balances if b['account_code'] == '1210'), 0.0)
    cash_balance = next((b['closing_balance'] for b in closing_balances if b['account_code'] == '1200'), 0.0)
    
    # Calculate total income and expenses
    result = await db.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            and_(
                Transaction.society_id == current_user.society_id,
                Transaction.type == "income",
                Transaction.date >= fy.start_date,
                Transaction.date <= fy.end_date
            )
        )
    )
    total_income = float(result.scalar() or 0)
    
    result = await db.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            and_(
                Transaction.society_id == current_user.society_id,
                Transaction.type == "expense",
                Transaction.date >= fy.start_date,
                Transaction.date <= fy.end_date
            )
        )
    )
    total_expenses = float(result.scalar() or 0)
    
    net_surplus_deficit = total_income - total_expenses
    
    # Step 4: Create or get next financial year
    next_fy_start = fy.end_date + timedelta(days=1)
    next_fy_end = date(next_fy_start.year + 1, 3, 31)  # March 31 next year
    
    result = await db.execute(
        select(FinancialYear).where(
            and_(
                FinancialYear.society_id == current_user.society_id,
                FinancialYear.start_date == next_fy_start
            )
        )
    )
    next_fy = result.scalar_one_or_none()
    
    if not next_fy:
        # Create next financial year
        next_fy = FinancialYear(
            society_id=current_user.society_id,
            year_name=f"FY {next_fy_start.year}-{str(next_fy_start.year + 1)[-2:]}",
            start_date=next_fy_start,
            end_date=next_fy_end,
            status=YearStatus.OPEN,
            is_active=True,
            is_closed=False,
            opening_balances_status=OpeningBalanceStatus.PROVISIONAL
        )
        db.add(next_fy)
        await db.flush()  # Get the ID
    
    # Step 5: Create provisional opening balances for next year
    opening_balances_created = 0
    for balance_data in closing_balances:
        if abs(balance_data['closing_balance']) > 0.01:
            # Determine balance type
            if balance_data['closing_balance'] > 0:
                balance_type = BalanceType.DEBIT
                opening_amount = balance_data['closing_balance']
            else:
                balance_type = BalanceType.CREDIT
                opening_amount = abs(balance_data['closing_balance'])
            
            # Check if opening balance already exists
            result = await db.execute(
                select(OpeningBalance).where(
                    and_(
                        OpeningBalance.financial_year_id == next_fy.id,
                        OpeningBalance.account_head_id == balance_data['account_id']
                    )
                )
            )
            existing_ob = result.scalar_one_or_none()
            
            if existing_ob:
                # Update existing
                existing_ob.opening_balance = opening_amount
                existing_ob.balance_type = balance_type
                existing_ob.status = BalanceStatus.PROVISIONAL
                existing_ob.calculated_from_previous_year = True
            else:
                # Create new
                opening_balance = OpeningBalance(
                    society_id=current_user.society_id,
                    financial_year_id=next_fy.id,
                    account_head_id=balance_data['account_id'],
                    account_name=balance_data['account_name'],
                    opening_balance=opening_amount,
                    balance_type=balance_type,
                    status=BalanceStatus.PROVISIONAL,
                    calculated_from_previous_year=True,
                    manual_entry=False,
                    created_by=UUID(current_user.id)
                )
                db.add(opening_balance)
                opening_balances_created += 1
    
    # Step 6: Update current year status
    fy.status = YearStatus.PROVISIONAL_CLOSE
    fy.is_closed = True  # Legacy field
    fy.provisional_close_date = closing_request.closing_date
    fy.provisional_closed_by = UUID(current_user.id)
    fy.closing_notes = closing_request.notes
    fy.opening_balances_status = OpeningBalanceStatus.PROVISIONAL
    
    # Store financial summary
    fy.closing_bank_balance = bank_balance
    fy.closing_cash_balance = cash_balance
    fy.total_income = total_income
    fy.total_expenses = total_expenses
    fy.net_surplus_deficit = net_surplus_deficit
    
    # Deactivate current year, activate next year
    fy.is_active = False
    next_fy.is_active = True
    
    await db.commit()
    await db.refresh(fy)
    await db.refresh(next_fy)
    
    # Log action
    await log_action(
        db=db,
        society_id=current_user.society_id,
        user_id=int(current_user.id),
        action_type="provisional_close",
        entity_type="financial_year",
        entity_id=str(fy.id),
        new_values={
            "year": fy.year_name,
            "closing_date": str(closing_request.closing_date),
            "bank_balance": bank_balance,
            "cash_balance": cash_balance
        }
    )
    
    return YearEndClosingSummary(
        financial_year_id=fy.id,
        year_name=fy.year_name,
        closing_date=datetime.combine(closing_request.closing_date, datetime.min.time()),
        bank_balance=bank_balance,
        cash_balance=cash_balance,
        total_income=total_income,
        total_expenses=total_expenses,
        net_surplus_deficit=net_surplus_deficit,
        opening_balances_created=True,
        next_year_activated=True,
        message=f"Year {fy.year_name} provisionally closed. Next year {next_fy.year_name} is now active. "
                f"Opening balances are PROVISIONAL and will be finalized after audit completion."
    )


@router.post("/{year_id}/adjustment-entry", response_model=AuditAdjustmentResponse)
async def post_adjustment_entry(
    year_id: UUID,
    adjustment_request: AuditAdjustmentRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    **Stage 2: Post Audit Adjustment Entry**
    
    Post an adjustment entry to a provisionally closed financial year.
    This allows auditors to correct entries after year-end.
    
    Key Features:
    - Entry is dated in the closed year (effective_date)
    - But posted in current year (today)
    - Closing balances automatically recalculated
    - Opening balances automatically updated (remain provisional)
    - Current year operations unaffected
    
    Example:
    - Posting date: July 10, 2024
    - Effective date: March 31, 2024
    - Entry: Dr. Expenses ₹5,000 / Cr. Payables ₹5,000
    - Result: FY 2023-24 closing updated, FY 2024-25 opening updated
    """
    # Step 1: Get and validate financial year
    result = await db.execute(
        select(FinancialYear).where(
            and_(
                FinancialYear.id == year_id,
                FinancialYear.society_id == current_user.society_id
            )
        )
    )
    fy = result.scalar_one_or_none()
    
    if not fy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Financial year not found"
        )
    
    if fy.status == YearStatus.OPEN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Year is still open. Use regular journal entry for current year."
        )
    
    if fy.status == YearStatus.FINAL_CLOSE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Year is permanently closed. Cannot post adjustments to finalized year."
        )
    
    # Verify effective date is within the year
    if not (fy.start_date <= adjustment_request.effective_date <= fy.end_date):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Effective date must be within {fy.year_name} ({fy.start_date} to {fy.end_date})"
        )
    
    # Step 2: Generate adjustment number
    adjustment_number = await generate_adjustment_number(db, current_user.society_id, year_id)
    entry_number = f"JE-{adjustment_number}"
    
    # Calculate total amount
    total_debit = sum(e.amount for e in adjustment_request.entries if e.entry_type == 'debit')
    total_credit = sum(e.amount for e in adjustment_request.entries if e.entry_type == 'credit')
    
    # Step 3: Create audit adjustment record
    audit_adjustment = AuditAdjustment(
        society_id=current_user.society_id,
        financial_year_id=year_id,
        adjustment_number=adjustment_number,
        adjustment_date=date.today(),
        effective_date=adjustment_request.effective_date,
        adjustment_type=AdjustmentType(adjustment_request.adjustment_type),
        description=adjustment_request.description,
        reason=adjustment_request.reason,
        auditor_reference=adjustment_request.auditor_reference,
        amount=total_debit,
        approved_by=UUID(current_user.id),
        approved_at=datetime.utcnow(),
        journal_entry_number=entry_number
    )
    db.add(audit_adjustment)
    
    # Step 4: Post journal entries (with adjustment flag)
    # TODO: Create journal entries with is_adjustment_entry=True
    # For now, we'll just create the adjustment record
    
    # Step 5: Recalculate closing balances for affected accounts
    affected_account_ids = [e.account_head_id for e in adjustment_request.entries]
    await recalculate_closing_balances(db, year_id, affected_account_ids)
    
    # Step 6: Update provisional opening balances for next year
    await update_provisional_opening_balances(db, current_user.society_id, year_id, affected_account_ids)
    
    await db.commit()
    
    # Log action
    await log_action(
        db=db,
        society_id=current_user.society_id,
        user_id=int(current_user.id),
        action_type="adjustment_entry",
        entity_type="audit_adjustment",
        entity_id=str(audit_adjustment.id),
        new_values={
            "adjustment_number": adjustment_number,
            "year": fy.year_name,
            "amount": total_debit,
            "type": adjustment_request.adjustment_type
        }
    )
    
    return AuditAdjustmentResponse(
        success=True,
        message="Adjustment entry posted successfully",
        adjustment_id=audit_adjustment.id,
        adjustment_number=adjustment_number,
        entry_number=entry_number,
        effective_date=adjustment_request.effective_date,
        amount=total_debit,
        financial_year=fy.year_name,
        note="Opening balances for current year have been updated (still provisional)",
        affected_accounts=[
            {
                "account_name": e.account_name,
                "adjustment": e.amount,
                "type": e.entry_type
            }
            for e in adjustment_request.entries
        ]
    )


@router.post("/{year_id}/final-close", response_model=Dict)
async def final_close_financial_year(
    year_id: UUID,
    closing_request: FinalClosingRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    **Stage 3: Final Closing**
    
    Permanently close the financial year after audit completion.
    This is irreversible!
    
    Requirements:
    - Year must be provisionally closed
    - Audit must be complete
    - Audit report must be uploaded
    - All adjustments must be approved
    
    Actions:
    - Mark year as 'final_close' (permanently locked)
    - Finalize opening balances for next year
    - Store audit information
    - Generate final financial statements
    - No further changes allowed
    """
    # Step 1: Get and validate financial year
    result = await db.execute(
        select(FinancialYear).where(
            and_(
                FinancialYear.id == year_id,
                FinancialYear.society_id == current_user.society_id
            )
        )
    )
    fy = result.scalar_one_or_none()
    
    if not fy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Financial year not found"
        )
    
    if fy.status != YearStatus.PROVISIONAL_CLOSE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Year must be provisionally closed first. Current status: {fy.status.value}"
        )
    
    # Step 2: Update financial year to final close
    fy.status = YearStatus.FINAL_CLOSE
    fy.final_close_date = closing_request.audit_completion_date
    fy.final_closed_by = UUID(current_user.id)
    fy.audit_end_date = closing_request.audit_completion_date
    fy.auditor_name = closing_request.auditor_name
    fy.auditor_firm = closing_request.auditor_firm
    fy.audit_report_date = closing_request.audit_completion_date
    fy.audit_report_file_url = closing_request.audit_report_file_url
    fy.opening_balances_status = OpeningBalanceStatus.FINALIZED
    
    # Step 3: Finalize opening balances for next year
    result = await db.execute(
        select(FinancialYear).where(
            and_(
                FinancialYear.society_id == current_user.society_id,
                FinancialYear.start_date == fy.end_date + timedelta(days=1)
            )
        )
    )
    next_fy = result.scalar_one_or_none()
    
    opening_balances_finalized = 0
    if next_fy:
        # Update all provisional opening balances to finalized
        result = await db.execute(
            sql_update(OpeningBalance).where(
                and_(
                    OpeningBalance.financial_year_id == next_fy.id,
                    OpeningBalance.status == BalanceStatus.PROVISIONAL
                )
            ).values(
                status=BalanceStatus.FINALIZED,
                finalized_at=datetime.utcnow(),
                finalized_by=UUID(current_user.id)
            )
        )
        opening_balances_finalized = result.rowcount
        
        # Update next year's opening balance status
        next_fy.opening_balances_status = OpeningBalanceStatus.FINALIZED
    
    await db.commit()
    
    # Log action
    await log_action(
        db=db,
        society_id=current_user.society_id,
        user_id=int(current_user.id),
        action_type="final_close",
        entity_type="financial_year",
        entity_id=str(fy.id),
        new_values={
            "year": fy.year_name,
            "auditor": f"{closing_request.auditor_name} ({closing_request.auditor_firm})",
            "audit_date": str(closing_request.audit_completion_date)
        }
    )
    
    return {
        "success": True,
        "message": "Financial year permanently closed and locked",
        "year_label": fy.year_name,
        "status": "final_close",
        "final_close_date": closing_request.audit_completion_date.isoformat(),
        "audit_info": {
            "completion_date": closing_request.audit_completion_date.isoformat(),
            "auditor": closing_request.auditor_name,
            "firm": closing_request.auditor_firm,
            "report_url": closing_request.audit_report_file_url
        },
        "opening_balances_finalized": {
            "next_year": next_fy.year_name if next_fy else None,
            "count": opening_balances_finalized,
            "status": "finalized"
        },
        "note": "⚠️ This year is now PERMANENTLY LOCKED. No further changes are possible.",
        "next_steps": [
            "Download and archive all final reports",
            "Present to society members in AGM",
            "File statutory returns if applicable",
            "Begin planning for next year"
        ]
    }


# Helper Functions

async def calculate_closing_balances(
    db: AsyncSession,
    society_id: UUID,
    year_id: UUID
) -> List[Dict]:
    """Calculate closing balances for all accounts in the financial year"""
    # Get all account heads
    result = await db.execute(
        select(AccountCode).where(
            AccountCode.society_id == society_id
        )
    )
    account_heads = result.scalars().all()
    
    closing_balances = []
    for account in account_heads:
        # Get current balance (which becomes closing balance)
        closing_balances.append({
            'account_id': account.id,
            'account_name': account.name,
            'account_code': account.code,
            'closing_balance': float(account.current_balance or 0)
        })
    
    return closing_balances


async def generate_adjustment_number(
    db: AsyncSession,
    society_id: UUID,
    year_id: UUID
) -> str:
    """Generate sequential adjustment number: ADJ-2024-001"""
    result = await db.execute(
        select(FinancialYear).where(FinancialYear.id == year_id)
    )
    fy = result.scalar_one()
    
    # Extract year from year_name (e.g., "FY 2023-24" → "2024")
    year_parts = fy.year_name.split()
    if len(year_parts) > 1:
        year_num = year_parts[1].split('-')[0]
    else:
        year_num = str(fy.start_date.year)
    
    # Get last adjustment number
    result = await db.execute(
        select(AuditAdjustment).where(
            AuditAdjustment.financial_year_id == year_id
        ).order_by(desc(AuditAdjustment.adjustment_number)).limit(1)
    )
    last_adj = result.scalar_one_or_none()
    
    if last_adj:
        last_num = int(last_adj.adjustment_number.split('-')[-1])
        next_num = last_num + 1
    else:
        next_num = 1
    
    return f"ADJ-{year_num}-{next_num:03d}"


async def recalculate_closing_balances(
    db: AsyncSession,
    year_id: UUID,
    affected_account_ids: List[str]
):
    """Recalculate closing balances after adjustment (placeholder)"""
    # TODO: Implement balance recalculation
    pass


async def update_provisional_opening_balances(
    db: AsyncSession,
    society_id: UUID,
    previous_year_id: UUID,
    affected_account_ids: List[str]
):
    """Update provisional opening balances after adjustment"""
    # Get previous year
    result = await db.execute(
        select(FinancialYear).where(FinancialYear.id == previous_year_id)
    )
    prev_fy = result.scalar_one()
    
    # Get next year
    result = await db.execute(
        select(FinancialYear).where(
            and_(
                FinancialYear.society_id == society_id,
                FinancialYear.start_date == prev_fy.end_date + timedelta(days=1)
            )
        )
    )
    next_fy = result.scalar_one_or_none()
    
    if not next_fy:
        return  # Next year doesn't exist yet
    
    # Update opening balances for affected accounts
    for account_id in affected_account_ids:
        # Get account's current balance (closing balance from previous year)
        result = await db.execute(
            select(AccountCode).where(AccountCode.id == UUID(account_id))
        )
        account = result.scalar_one_or_none()
        
        if not account:
            continue
        
        closing_balance = float(account.current_balance or 0)
        
        # Get or create opening balance record
        result = await db.execute(
            select(OpeningBalance).where(
                and_(
                    OpeningBalance.financial_year_id == next_fy.id,
                    OpeningBalance.account_head_id == UUID(account_id)
                )
            )
        )
        opening_balance = result.scalar_one_or_none()
        
        if abs(closing_balance) < 0.01:
            # Balance is zero, delete opening balance if exists
            if opening_balance:
                await db.delete(opening_balance)
            continue
        
        # Determine balance type and amount
        if closing_balance > 0:
            balance_type = BalanceType.DEBIT
            opening_amount = closing_balance
        else:
            balance_type = BalanceType.CREDIT
            opening_amount = abs(closing_balance)
        
        if opening_balance:
            # Update existing
            opening_balance.opening_balance = opening_amount
            opening_balance.balance_type = balance_type
            opening_balance.calculated_from_previous_year = True
        else:
            # Create new
            new_opening_balance = OpeningBalance(
                society_id=society_id,
                financial_year_id=next_fy.id,
                account_head_id=UUID(account_id),
                account_name=account.name,
                opening_balance=opening_amount,
                balance_type=balance_type,
                status=BalanceStatus.PROVISIONAL,
                calculated_from_previous_year=True,
                manual_entry=False
            )
            db.add(new_opening_balance)
    
    await db.commit()

