"""Expense Heads Selection API routes for Fixed Expenses"""
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel

from app.database import get_db
from app.models.user import UserResponse
from app.models_db import AccountCode as AccountCodeDB, SocietySettings
from app.dependencies import get_current_user, get_current_admin_user

router = APIRouter()


class ExpenseHeadResponse(BaseModel):
    """Response model for expense head"""
    code: str
    name: str
    type: str
    description: Optional[str] = None


class ExpenseHeadSelectionRequest(BaseModel):
    """Request model for selecting expense heads"""
    expense_head_codes: List[str]  # List of account codes to include in fixed expenses


@router.get("/expense-heads", response_model=List[ExpenseHeadResponse])
async def get_available_expense_heads(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all available expense account codes (type='expense')
    These can be selected for inclusion in fixed expenses calculation
    """
    result = await db.execute(
        select(AccountCodeDB).where(
            AccountCodeDB.society_id == current_user.society_id,
            AccountCodeDB.type == "expense"
        ).order_by(AccountCodeDB.code)
    )
    expense_heads = result.scalars().all()
    
    return [
        ExpenseHeadResponse(
            code=expense.code,
            name=expense.name,
            type=expense.type.value if hasattr(expense.type, 'value') else str(expense.type),
            description=expense.description
        )
        for expense in expense_heads
    ]


@router.get("/expense-heads/selected", response_model=List[str])
async def get_selected_expense_heads(
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get currently selected expense heads for fixed expenses calculation
    Returns list of account codes
    """
    result = await db.execute(
        select(SocietySettings).where(SocietySettings.society_id == current_user.society_id)
    )
    settings = result.scalar_one_or_none()
    
    if not settings or not settings.fixed_expense_heads:
        return []
    
    return settings.fixed_expense_heads


@router.post("/expense-heads/select", response_model=List[str])
@router.patch("/expense-heads/select", response_model=List[str])
async def select_expense_heads(
    request: ExpenseHeadSelectionRequest,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Select which expense heads to include in fixed expenses calculation (admin only)
    This is used for water-based billing method
    
    The selected expense heads will be used to calculate fixed expenses per flat
    by summing transactions for those account codes in the billing month
    """
    # Validate that all provided codes are valid expense account codes
    result = await db.execute(
        select(AccountCodeDB).where(
            AccountCodeDB.society_id == current_user.society_id,
            AccountCodeDB.type == "expense",
            AccountCodeDB.code.in_(request.expense_head_codes)
        )
    )
    valid_codes = {expense.code for expense in result.scalars().all()}
    
    # Check if all provided codes are valid
    invalid_codes = set(request.expense_head_codes) - valid_codes
    if invalid_codes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid expense head codes: {', '.join(invalid_codes)}"
        )
    
    # Get or create society settings
    result = await db.execute(
        select(SocietySettings).where(SocietySettings.society_id == current_user.society_id)
    )
    settings = result.scalar_one_or_none()
    
    if not settings:
        # Create new settings
        from datetime import datetime
        settings = SocietySettings(
            society_id=current_user.society_id,
            fixed_expense_heads=request.expense_head_codes,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(settings)
    else:
        # Update existing settings
        settings.fixed_expense_heads = request.expense_head_codes
        from datetime import datetime
        settings.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(settings)
    
    return settings.fixed_expense_heads or []

