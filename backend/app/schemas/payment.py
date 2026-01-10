"""
Payment Schemas
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import date, datetime
from uuid import UUID
from decimal import Decimal


class PaymentRecordRequest(BaseModel):
    """Schema for recording a payment"""
    bill_id: UUID
    payment_date: date
    payment_mode: str = Field(..., description="cash, cheque, upi, neft, rtgs, etc.")
    amount: float = Field(..., gt=0, description="Payment amount")
    transaction_reference: Optional[str] = Field(None, description="Cheque no, UPI ref, etc.")
    bank_name: Optional[str] = None
    remarks: Optional[str] = None
    late_fee_charged: float = Field(0, ge=0)
    
    @validator('payment_mode')
    def validate_payment_mode(cls, v):
        valid_modes = ['cash', 'cheque', 'upi', 'neft', 'rtgs', 'imps', 
                       'bank_transfer', 'online', 'debit_card', 'credit_card', 'other']
        if v.lower() not in valid_modes:
            raise ValueError(f'Invalid payment mode. Must be one of: {", ".join(valid_modes)}')
        return v.lower()


class PaymentResponse(BaseModel):
    """Schema for payment response"""
    id: UUID
    society_id: UUID
    bill_id: UUID
    flat_id: UUID
    member_id: UUID
    receipt_number: str
    payment_date: date
    payment_mode: str
    amount: float
    transaction_reference: Optional[str]
    bank_name: Optional[str]
    remarks: Optional[str]
    status: str
    late_fee_charged: float
    is_partial_payment: bool
    receipt_generated: bool
    receipt_file_url: Optional[str]
    created_at: datetime
    
    # Additional info
    flat_number: Optional[str] = None
    member_name: Optional[str] = None
    bill_amount: Optional[float] = None
    
    class Config:
        from_attributes = True


class PaymentReceiptData(BaseModel):
    """Schema for payment receipt generation"""
    receipt_number: str
    payment_date: date
    payment_mode: str
    amount: float
    late_fee: float
    total_amount: float
    transaction_reference: Optional[str]
    
    # Bill details
    bill_number: str
    bill_date: date
    billing_period: str
    
    # Member details
    member_name: str
    flat_number: str
    
    # Society details
    society_name: str
    society_address: Optional[str]
    
    # Breakdown
    maintenance_amount: float
    sinking_fund: float
    other_charges: float


class PaymentHistoryResponse(BaseModel):
    """Schema for payment history"""
    payments: List[PaymentResponse]
    summary: dict = Field(
        ...,
        description="Summary: total_payments, total_amount, payment_modes_breakdown"
    )


class ReconciliationSummary(BaseModel):
    """Schema for bank reconciliation summary"""
    period_start: date
    period_end: date
    
    # Bills
    total_bills_generated: int
    total_bills_amount: float
    
    # Payments
    total_payments_received: int
    total_payments_amount: float
    
    # Outstanding
    total_outstanding_bills: int
    total_outstanding_amount: float
    
    # Overdue
    total_overdue_bills: int
    total_overdue_amount: float
    
    # Payment mode breakdown
    payment_by_mode: dict  # {"cash": 50000, "upi": 120000, ...}
    
    # Collection efficiency
    collection_rate: float  # Percentage of bills paid
    average_collection_days: float  # Average days to collect


class OverdueBill(BaseModel):
    """Schema for overdue bill"""
    bill_id: UUID
    bill_number: str
    flat_number: str
    member_name: str
    bill_date: date
    due_date: date
    amount: float
    days_overdue: int
    last_reminder_sent: Optional[date]
    member_phone: Optional[str]
    member_email: Optional[str]


class OverdueBillsResponse(BaseModel):
    """Schema for overdue bills list"""
    overdue_bills: List[OverdueBill]
    summary: dict = Field(
        ...,
        description="Summary: total_count, total_amount, oldest_overdue_days"
    )


class PaymentReminderRequest(BaseModel):
    """Schema for sending payment reminders"""
    bill_ids: List[UUID] = Field(..., min_items=1)
    reminder_type: str = Field(..., description="email, sms, whatsapp, or push")
    custom_message: Optional[str] = None
    
    @validator('reminder_type')
    def validate_reminder_type(cls, v):
        valid_types = ['email', 'sms', 'whatsapp', 'push']
        if v.lower() not in valid_types:
            raise ValueError(f'Invalid reminder type. Must be one of: {", ".join(valid_types)}')
        return v.lower()


class PaymentReminderResponse(BaseModel):
    """Schema for reminder response"""
    success: bool
    reminders_sent: int
    failed: int
    details: List[dict]


