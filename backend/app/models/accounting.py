"""Accounting models"""
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


class AccountCode(BaseModel):
    """Model for account code"""
    code: str = Field(..., min_length=4, max_length=10)
    name: str = Field(..., min_length=1, max_length=100)
    type: Literal["asset", "liability", "capital", "income", "expense"]
    description: Optional[str] = None
    category: Optional[str] = None
    opening_balance: float = 0.0


class AccountCodeResponse(BaseModel):
    """Model for account code response"""
    id: str = Field(..., alias="_id")
    code: str
    name: str
    type: Literal["asset", "liability", "capital", "income", "expense"]
    description: Optional[str] = None
    category: Optional[str] = None
    opening_balance: float
    current_balance: float
    is_fixed_expense: bool = False  # If True, include in fixed expenses calculation for maintenance bills
    utility_type: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True


class AccountCodeUpdate(BaseModel):
    """Model for updating account code"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Account name")
    description: Optional[str] = Field(None, description="Account description")
    is_fixed_expense: Optional[bool] = Field(None, description="Include in fixed expenses calculation for maintenance bills")


class OpeningBalanceUpdate(BaseModel):
    """Model for updating opening balance"""
    opening_balance: float = Field(..., description="New opening balance amount")


class BalanceSheetValidation(BaseModel):
    """Model for balance sheet validation response"""
    total_assets: float
    total_liabilities: float
    total_equity: float
    difference: float
    is_balanced: bool
    equity_account_code: Optional[str] = None
    equity_account_name: Optional[str] = None
    message: str
