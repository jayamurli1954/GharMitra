"""
Pydantic Schemas for Financial Year
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from uuid import UUID


class FinancialYearBase(BaseModel):
    """Base schema for financial year"""
    year_name: str = Field(..., description="Year name (e.g., '2024-2025', 'FY 2024-25')")
    start_date: date = Field(..., description="Year start date")
    end_date: date = Field(..., description="Year end date")


class FinancialYearCreate(FinancialYearBase):
    """Schema for creating a new financial year"""
    
    @validator('end_date')
    def end_date_must_be_after_start_date(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('end_date must be after start_date')
        return v


class FinancialYearUpdate(BaseModel):
    """Schema for updating a financial year"""
    year_name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: Optional[bool] = None


class FinancialYearResponse(FinancialYearBase):
    """Schema for financial year response"""
    id: UUID
    society_id: UUID
    is_active: bool
    is_closed: bool
    closed_at: Optional[datetime] = None
    closed_by_user_id: Optional[UUID] = None
    closing_notes: Optional[str] = None
    closing_bank_balance: Optional[float] = None
    closing_cash_balance: Optional[float] = None
    total_income: Optional[float] = None
    total_expenses: Optional[float] = None
    net_surplus_deficit: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class YearEndClosingRequest(BaseModel):
    """Schema for year-end closing"""
    closing_notes: Optional[str] = Field(None, description="Notes about the year-end closing")
    confirm_closure: bool = Field(..., description="Confirmation flag (must be true)")
    
    @validator('confirm_closure')
    def confirm_must_be_true(cls, v):
        if not v:
            raise ValueError('Year-end closing must be explicitly confirmed')
        return v


class YearEndClosingSummary(BaseModel):
    """Schema for year-end closing summary"""
    financial_year_id: UUID
    year_name: str
    closing_date: datetime
    bank_balance: float
    cash_balance: float
    total_income: float
    total_expenses: float
    net_surplus_deficit: float
    opening_balances_created: bool
    next_year_activated: bool
    message: str


class ProvisionalClosingRequest(BaseModel):
    """Schema for provisional year closing"""
    closing_date: date = Field(..., description="Date of provisional closing")
    notes: Optional[str] = Field(None, description="Notes about provisional closing")


class FinalClosingRequest(BaseModel):
    """Schema for final year closing"""
    audit_completion_date: date = Field(..., description="Date audit was completed")
    auditor_name: str = Field(..., description="Name of auditor")
    auditor_firm: str = Field(..., description="Audit firm name")
    audit_report_file_url: str = Field(..., description="Cloudinary URL to audit report PDF")
    final_statements_approved: bool = Field(..., description="Committee approval confirmation")
    committee_approval_date: Optional[date] = Field(None, description="Date of committee approval")
    notes: Optional[str] = Field(None, description="Notes about final closing")


class JournalEntryItem(BaseModel):
    """Schema for journal entry item in adjustment"""
    account_head_id: str
    account_name: str
    entry_type: str = Field(..., description="'debit' or 'credit'")
    amount: float = Field(..., gt=0)
    description: Optional[str] = None


class AuditAdjustmentRequest(BaseModel):
    """Schema for posting audit adjustment entry"""
    effective_date: date = Field(..., description="Date entry is effective (in closed year)")
    adjustment_type: str = Field(..., description="Type of adjustment")
    description: str = Field(..., description="Brief description")
    reason: str = Field(..., description="Detailed reason from auditor")
    auditor_reference: Optional[str] = Field(None, description="Audit finding reference")
    entries: List[JournalEntryItem] = Field(..., min_items=2)
    
    @validator('entries')
    def validate_balanced(cls, v):
        """Ensure entries are balanced"""
        total_debit = sum(e.amount for e in v if e.entry_type == 'debit')
        total_credit = sum(e.amount for e in v if e.entry_type == 'credit')
        if abs(total_debit - total_credit) > 0.01:
            raise ValueError('Adjustment entries must be balanced')
        return v


class AuditAdjustmentResponse(BaseModel):
    """Schema for audit adjustment response"""
    success: bool
    message: str
    adjustment_id: UUID
    adjustment_number: str
    entry_number: str
    effective_date: date
    amount: float
    financial_year: str
    note: str
    affected_accounts: List[dict]

