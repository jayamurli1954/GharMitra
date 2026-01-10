"""Journal Entry models for double-entry bookkeeping"""
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import List, Optional
import datetime


class JournalEntryLine(BaseModel):
    """Single line in a journal entry (debit or credit)"""
    account_code: str = Field(..., min_length=4, max_length=10, description="Account code")
    debit_amount: float = Field(0.0, ge=0, description="Debit amount (0 if credit)")
    credit_amount: float = Field(0.0, ge=0, description="Credit amount (0 if debit)")
    description: Optional[str] = Field(None, max_length=500)
    quantity: Optional[float] = Field(None, ge=0, description="Quantity/units (e.g., 60)")
    unit_price: Optional[float] = Field(None, ge=0, description="Price per unit (e.g., 450)")


class JournalEntryCreate(BaseModel):
    """Model for creating a journal entry"""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    date: Optional[datetime.date] = Field(
        None,
        description="Entry date (defaults to today if not provided). Accepts valid date objects, date strings (YYYY-MM-DD), or None."
    )
    expense_month: Optional[str] = Field(
        None,
        description="Month this entry belongs to (e.g. 'January, 2026')."
    )
    description: str = Field(..., min_length=1, max_length=500)
    entries: List[dict]  # Will be validated as JournalEntryLine in route handler

    @field_validator('date', mode='before')
    @classmethod
    def validate_date(cls, v):
        """Validate and convert date string to date object"""
        if v is None or v == '':
            return None
        if isinstance(v, datetime.date):
            return v
        if isinstance(v, str):
            # Try YYYY-MM-DD format (ISO format from HTML date input)
            try:
                return datetime.datetime.strptime(v, '%Y-%m-%d').date()
            except ValueError:
                # Try DD/MM/YYYY format
                try:
                    return datetime.datetime.strptime(v, '%d/%m/%Y').date()
                except ValueError:
                    raise ValueError(f"Invalid date format. Use YYYY-MM-DD or DD/MM/YYYY")
        return v


class JournalEntryResponse(BaseModel):
    """Model for journal entry response"""
    id: str
    entry_number: str
    date: datetime.date
    expense_month: Optional[str] = None
    description: str
    total_debit: float
    total_credit: float
    is_balanced: bool
    added_by: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    entries: List[dict] = Field(default_factory=list, description="Transaction entries in this journal")

    class Config:
        populate_by_name = True


class TrialBalanceItem(BaseModel):
    """Single item in trial balance"""
    account_code: str
    account_name: str
    debit_balance: float = 0.0
    credit_balance: float = 0.0


class TrialBalanceResponse(BaseModel):
    """Trial balance report response"""
    as_on_date: datetime.date
    items: List[TrialBalanceItem]
    total_debit: float
    total_credit: float
    difference: float
    is_balanced: bool


class LedgerEntry(BaseModel):
    """Single entry in an account ledger"""
    date: datetime.date
    description: str
    reference: Optional[str] = None
    debit: float = 0.0
    credit: float = 0.0
    balance: float = 0.0


class LedgerResponse(BaseModel):
    """Account ledger report response"""
    account_code: str
    account_name: str
    from_date: datetime.date
    to_date: datetime.date
    opening_balance: float
    entries: List[LedgerEntry]
    total_debit: float
    total_credit: float
    closing_balance: float


class BulkLedgerResponse(BaseModel):
    """Response containing multiple account ledgers"""
    from_date: datetime.date
    to_date: datetime.date
    ledgers: List[LedgerResponse]
