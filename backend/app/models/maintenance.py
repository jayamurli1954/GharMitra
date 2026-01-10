"""Maintenance billing models"""
from pydantic import BaseModel, Field
from typing import Optional, Literal, Dict, List
from datetime import datetime


class ApartmentSettings(BaseModel):
    """Model for apartment settings"""
    apartment_name: str = Field(..., min_length=1, max_length=100)
    total_flats: int = Field(..., gt=0)
    calculation_method: Literal["sqft_rate", "variable"] = "variable"
    sqft_rate: Optional[float] = Field(None, ge=0)  # For sqft_rate method
    sinking_fund_total: Optional[float] = Field(None, ge=0)  # For variable method


class ApartmentSettingsResponse(BaseModel):
    """Model for apartment settings response"""
    id: str = Field(..., alias="_id")
    apartment_name: str
    total_flats: int
    calculation_method: Literal["sqft_rate", "variable"]
    sqft_rate: Optional[float] = None
    sinking_fund_total: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True


class FixedExpense(BaseModel):
    """Model for fixed monthly expense"""
    name: str = Field(..., min_length=1, max_length=100)
    amount: float = Field(..., gt=0)
    frequency: Literal["monthly", "quarterly", "annual"] = "monthly"
    description: Optional[str] = None


class FixedExpenseResponse(BaseModel):
    """Model for fixed expense response"""
    id: str = Field(..., alias="_id")
    name: str
    amount: float
    frequency: Literal["monthly", "quarterly", "annual"]
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True


class WaterExpense(BaseModel):
    """Model for monthly water expense"""
    month: int = Field(..., ge=1, le=12)
    year: int = Field(..., ge=2020)
    tanker_charges: float = Field(..., ge=0)
    government_charges: float = Field(..., ge=0)
    other_charges: float = Field(0, ge=0)


class WaterExpenseResponse(BaseModel):
    """Model for water expense response"""
    id: str = Field(..., alias="_id")
    month: int
    year: int
    tanker_charges: float
    government_charges: float
    other_charges: float
    total_water_expense: float
    created_at: datetime

    class Config:
        populate_by_name = True


class BillBreakdown(BaseModel):
    """Breakdown of bill calculation"""
    water_charges: Optional[float] = None
    per_person_water_charge: Optional[float] = None
    fixed_expenses: Optional[float] = None
    sinking_fund: Optional[float] = None
    sqft_calculation: Optional[str] = None


class MaintenanceBill(BaseModel):
    """Model for maintenance bill response"""
    id: str = Field(..., alias="_id")
    flat_id: str
    flat_number: str
    bill_number: Optional[str] = None
    month: int
    year: int
    amount: float
    breakdown: Dict  # Changed to Dict to allow flexible breakdown
    status: Literal["unpaid", "paid"] = "unpaid"
    is_posted: bool = False
    created_at: datetime
    paid_at: Optional[datetime] = None

    class Config:
        populate_by_name = True


class MaintenanceBillDetail(BaseModel):
    """Comprehensive bill format with all details for printing"""
    # Header
    society_name: str
    society_logo_url: Optional[str] = None
    bill_date: str  # Formatted date
    bill_number: str
    member_name: str
    flat_number: str
    
    # Description
    bill_description: str  # "Maintenance Bill for the month of [Month Year]"
    
    # Bill Body
    bill_type: Literal["sqft_rate", "water_based"]  # Type of billing
    # For sqft_rate type
    sqft_amount: Optional[float] = None
    sqft_rate: Optional[float] = None
    flat_area_sqft: Optional[float] = None
    # For water_based type
    water_charges: Optional[float] = None
    water_charge_per_person: Optional[float] = None
    number_of_occupants: Optional[int] = None
    fixed_expenses_share: Optional[float] = None
    sinking_fund: Optional[float] = None
    other_funds: Optional[Dict[str, float]] = None  # Additional funds if any
    
    # Total
    total_amount: float
    amount_in_words: str  # Amount in words
    
    # Footer
    eoe_text: str = "E & O E"  # Errors & Omissions Excepted
    bank_name: Optional[str] = None
    bank_branch: Optional[str] = None
    bank_account_number: Optional[str] = None
    bank_ifsc_code: Optional[str] = None
    upi_qr_code_url: Optional[str] = None
    society_address: Optional[str] = None


class CollectibleExpense(BaseModel):
    """Monthly total for an expense account code"""
    account_code: str
    account_name: str
    total_amount: float
    transaction_count: int

class CollectibleExpensesResponse(BaseModel):
    """Response for fetching potential expenses for a month"""
    month: int
    year: int
    water_tanker_amount: float
    water_govt_amount: float
    fixed_expenses: List[CollectibleExpense]

class BillGenerationRequest(BaseModel):
    """Enhanced request to generate bills for a month - CR-021 compliant"""
    month: int = Field(..., ge=1, le=12)
    year: int = Field(..., ge=2020)
    
    # Maintenance Base (CR-021: sq.ft × rate, if rate is 0, don't calculate by area)
    override_sqft_rate: Optional[float] = Field(None, ge=0, description="Maintenance rate per sq.ft. If 0, maintenance not calculated by area")
    
    # Water (CR-021: Per person calculation with admin-adjusted inmates)
    override_water_charges: Optional[float] = Field(None, ge=0, description="Total water charges override (5110 + 5120). If not provided, calculated from transactions")
    adjusted_inmates: Optional[Dict[str, int]] = Field(None, description="Flat-wise adjusted inmate counts for water calculation. Key: flat_id, Value: adjusted count. Used for guests/vacations >7 days")
    
    # Fixed Expenses (CR-021: Admin selects which expenses to include, equal or sqft distribution)
    selected_fixed_expense_codes: Optional[List[str]] = Field(default_factory=list, description="Account codes to include in fixed expenses (admin selection)")
    fixed_calculation_method: Literal["equal", "sqft"] = "equal"
    override_fixed_expenses: Optional[float] = Field(None, ge=0, description="Direct override for total fixed expenses if needed")
    
    # Sinking Fund (CR-021: Per sq.ft or per flat)
    sinking_calculation_method: Literal["equal", "sqft"] = "equal"
    override_sinking_fund: Optional[float] = Field(None, ge=0, description="Total sinking fund to collect. If not provided, uses settings")
    
    # Repair Fund (CR-021: Per sq.ft or per flat)
    repair_fund_calculation_method: Literal["equal", "sqft"] = "equal"
    override_repair_fund: Optional[float] = Field(None, ge=0, description="Total repair fund to collect. If not provided, uses settings")
    
    # Corpus Fund (CR-021: Per sq.ft or per flat)
    corpus_fund_calculation_method: Literal["equal", "sqft"] = "equal"
    override_corpus_fund: Optional[float] = Field(None, ge=0, description="Total corpus fund to collect. If not provided, uses settings")
    
    # Accounting Posting (CR-021: Auto-post to accounting)
    auto_post_to_accounting: bool = Field(True, description="Automatically post bills to accounting (Debit 1100, Credit 4000/4010/etc)")


class PostBillsRequest(BaseModel):
    """Request to post draft bills to accounting"""
    month: int = Field(..., ge=1, le=12)
    year: int = Field(..., ge=2020)


class BillGenerationResponse(BaseModel):
    """Response after generating bills"""
    total_bills_generated: int
    total_amount: float
    month: int
    year: int
    bills: List[MaintenanceBill]


class ReverseBillRequest(BaseModel):
    """CR-021_revised: Request to reverse and regenerate a single flat's bill"""
    bill_id: str = Field(..., description="ID of the bill to reverse")
    reversal_reason: str = Field(..., min_length=10, description="Reason for reversal (required for audit compliance)")
    committee_approval: Optional[str] = Field(None, description="Committee approval reference/number")


class RegenerateBillRequest(BaseModel):
    """CR-021_revised: Request to regenerate a single flat's bill after reversal"""
    flat_id: str = Field(..., description="Flat ID for which to regenerate bill")
    month: int = Field(..., ge=1, le=12)
    year: int = Field(..., ge=2020)
    # Manual overrides for the regenerated bill
    override_maintenance: Optional[float] = Field(None, ge=0)
    override_water: Optional[float] = Field(None, ge=0)
    override_fixed: Optional[float] = Field(None, ge=0)
    override_sinking: Optional[float] = Field(None, ge=0)
    override_repair: Optional[float] = Field(None, ge=0)
    override_corpus: Optional[float] = Field(None, ge=0)
    notes: Optional[str] = Field(None, description="Additional notes for the regenerated bill")
