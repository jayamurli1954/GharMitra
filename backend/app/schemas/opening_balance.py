"""
Opening Balance Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from uuid import UUID


class OpeningBalanceBase(BaseModel):
    """Base schema for opening balance"""
    account_head_id: UUID
    account_name: str
    opening_balance: float
    balance_type: str = Field(..., description="'debit' or 'credit'")


class OpeningBalanceCreate(OpeningBalanceBase):
    """Schema for creating manual opening balance"""
    financial_year_id: UUID
    manual_entry_reason: str = Field(..., description="Reason for manual entry (required)")


class OpeningBalanceResponse(OpeningBalanceBase):
    """Schema for opening balance response"""
    id: UUID
    society_id: UUID
    financial_year_id: UUID
    status: str = Field(..., description="'provisional' or 'finalized'")
    calculated_from_previous_year: bool
    manual_entry: bool
    manual_entry_reason: Optional[str]
    created_at: datetime
    created_by: Optional[str]
    finalized_at: Optional[datetime]
    finalized_by: Optional[str]
    
    class Config:
        from_attributes = True


class OpeningBalanceListResponse(BaseModel):
    """Schema for list of opening balances with summary"""
    financial_year_id: UUID
    financial_year_name: str
    opening_balances_status: str = Field(..., description="'provisional' or 'finalized'")
    balances: List[OpeningBalanceResponse]
    summary: Dict = Field(
        ...,
        description="Summary statistics: total_accounts, total_debit, total_credit, etc."
    )


