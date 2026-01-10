"""
Opening Balances API
Manage opening balances for financial years
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from typing import List
from uuid import UUID

from ..database import get_db
from ..models_db import (
    OpeningBalance,
    BalanceStatus,
    BalanceType,
    FinancialYear
)
from ..schemas.opening_balance import (
    OpeningBalanceResponse,
    OpeningBalanceCreate,
    OpeningBalanceListResponse
)
from ..dependencies import get_current_user
from ..models.user import UserResponse
from ..utils.audit import log_action

router = APIRouter(prefix="/opening-balances", tags=["opening-balances"])


@router.get("/year/{year_id}", response_model=OpeningBalanceListResponse)
async def list_opening_balances_for_year(
    year_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all opening balances for a specific financial year
    
    Returns:
    - List of all opening balances
    - Summary statistics
    - Status information
    """
    # Verify year exists and belongs to user's society
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
    
    # Get all opening balances
    result = await db.execute(
        select(OpeningBalance).where(
            OpeningBalance.financial_year_id == year_id
        ).order_by(OpeningBalance.account_name)
    )
    opening_balances = result.scalars().all()
    
    # Calculate summary
    total_debit = sum(
        float(ob.opening_balance) for ob in opening_balances
        if ob.balance_type == BalanceType.DEBIT
    )
    total_credit = sum(
        float(ob.opening_balance) for ob in opening_balances
        if ob.balance_type == BalanceType.CREDIT
    )
    
    provisional_count = sum(
        1 for ob in opening_balances
        if ob.status == BalanceStatus.PROVISIONAL
    )
    finalized_count = sum(
        1 for ob in opening_balances
        if ob.status == BalanceStatus.FINALIZED
    )
    
    return OpeningBalanceListResponse(
        financial_year_id=year_id,
        financial_year_name=fy.year_name,
        opening_balances_status=fy.opening_balances_status.value,
        balances=[
            OpeningBalanceResponse(
                id=ob.id,
                society_id=ob.society_id,
                financial_year_id=ob.financial_year_id,
                account_head_id=ob.account_head_id,
                account_name=ob.account_name,
                opening_balance=float(ob.opening_balance),
                balance_type=ob.balance_type.value,
                status=ob.status.value,
                calculated_from_previous_year=ob.calculated_from_previous_year,
                manual_entry=ob.manual_entry,
                manual_entry_reason=ob.manual_entry_reason,
                created_at=ob.created_at,
                created_by=str(ob.created_by) if ob.created_by else None,
                finalized_at=ob.finalized_at,
                finalized_by=str(ob.finalized_by) if ob.finalized_by else None
            )
            for ob in opening_balances
        ],
        summary={
            "total_accounts": len(opening_balances),
            "total_debit": total_debit,
            "total_credit": total_credit,
            "difference": abs(total_debit - total_credit),
            "is_balanced": abs(total_debit - total_credit) < 0.01,
            "provisional_count": provisional_count,
            "finalized_count": finalized_count,
            "all_finalized": finalized_count == len(opening_balances) and len(opening_balances) > 0
        }
    )


@router.get("/{balance_id}", response_model=OpeningBalanceResponse)
async def get_opening_balance(
    balance_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific opening balance by ID"""
    result = await db.execute(
        select(OpeningBalance).where(
            and_(
                OpeningBalance.id == balance_id,
                OpeningBalance.society_id == current_user.society_id
            )
        )
    )
    ob = result.scalar_one_or_none()
    
    if not ob:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Opening balance not found"
        )
    
    return OpeningBalanceResponse(
        id=ob.id,
        society_id=ob.society_id,
        financial_year_id=ob.financial_year_id,
        account_head_id=ob.account_head_id,
        account_name=ob.account_name,
        opening_balance=float(ob.opening_balance),
        balance_type=ob.balance_type.value,
        status=ob.status.value,
        calculated_from_previous_year=ob.calculated_from_previous_year,
        manual_entry=ob.manual_entry,
        manual_entry_reason=ob.manual_entry_reason,
        created_at=ob.created_at,
        created_by=str(ob.created_by) if ob.created_by else None,
        finalized_at=ob.finalized_at,
        finalized_by=str(ob.finalized_by) if ob.finalized_by else None
    )


@router.post("", response_model=OpeningBalanceResponse, status_code=status.HTTP_201_CREATED)
async def create_manual_opening_balance(
    balance_data: OpeningBalanceCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a manual opening balance entry
    
    This is used for:
    - First year setup (no previous year to calculate from)
    - Manual corrections approved by committee
    """
    # Verify year exists and is not finalized
    result = await db.execute(
        select(FinancialYear).where(
            and_(
                FinancialYear.id == balance_data.financial_year_id,
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
    
    # Check if opening balance already exists for this account
    result = await db.execute(
        select(OpeningBalance).where(
            and_(
                OpeningBalance.financial_year_id == balance_data.financial_year_id,
                OpeningBalance.account_head_id == balance_data.account_head_id
            )
        )
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Opening balance already exists for this account"
        )
    
    # Create new opening balance
    new_ob = OpeningBalance(
        society_id=current_user.society_id,
        financial_year_id=balance_data.financial_year_id,
        account_head_id=balance_data.account_head_id,
        account_name=balance_data.account_name,
        opening_balance=balance_data.opening_balance,
        balance_type=BalanceType(balance_data.balance_type),
        status=BalanceStatus.PROVISIONAL,  # Manual entries start as provisional
        calculated_from_previous_year=False,
        manual_entry=True,
        manual_entry_reason=balance_data.manual_entry_reason,
        created_by=UUID(current_user.id)
    )
    
    db.add(new_ob)
    await db.commit()
    await db.refresh(new_ob)
    
    # Log action
    await log_action(
        db=db,
        society_id=current_user.society_id,
        user_id=int(current_user.id),
        action_type="create",
        entity_type="opening_balance",
        entity_id=str(new_ob.id),
        new_values={
            "account": balance_data.account_name,
            "amount": balance_data.opening_balance,
            "type": balance_data.balance_type
        }
    )
    
    return OpeningBalanceResponse(
        id=new_ob.id,
        society_id=new_ob.society_id,
        financial_year_id=new_ob.financial_year_id,
        account_head_id=new_ob.account_head_id,
        account_name=new_ob.account_name,
        opening_balance=float(new_ob.opening_balance),
        balance_type=new_ob.balance_type.value,
        status=new_ob.status.value,
        calculated_from_previous_year=new_ob.calculated_from_previous_year,
        manual_entry=new_ob.manual_entry,
        manual_entry_reason=new_ob.manual_entry_reason,
        created_at=new_ob.created_at,
        created_by=str(new_ob.created_by) if new_ob.created_by else None,
        finalized_at=new_ob.finalized_at,
        finalized_by=str(new_ob.finalized_by) if new_ob.finalized_by else None
    )

