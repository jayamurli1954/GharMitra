"""Transaction models"""
from pydantic import BaseModel, Field, model_validator, field_validator
from typing import Optional, Literal, Union
from datetime import datetime, date


class TransactionCreate(BaseModel):
    """Model for creating a new transaction"""
    type: Literal["income", "expense"]
    category: str = Field(..., min_length=1, max_length=100)
    account_code: Optional[str] = Field(None, max_length=10)
    # Amount can be provided directly OR calculated from quantity × unit_price
    amount: Optional[float] = Field(None, description="Total amount (required if quantity/unit_price not provided)")
    quantity: Optional[float] = Field(None, description="Quantity/units (e.g., 20 tankers)")
    unit_price: Optional[float] = Field(None, description="Price per unit (e.g., 400 per tanker)")
    date: Optional[str] = None  # Transaction date (YYYY-MM-DD or DD/MM/YYYY format). If not provided, uses current date
    expense_month: Optional[str] = None  # Month this expense belongs to (YYYY-MM-DD). If not provided here, uses date's month
    description: str = Field(..., min_length=1, max_length=500)
    # Double-entry bookkeeping fields
    debit_amount: Optional[float] = Field(None, ge=0, description="Debit amount (for double-entry)")
    credit_amount: Optional[float] = Field(None, ge=0, description="Credit amount (for double-entry)")
    payment_method: Optional[str] = Field(None, description="Payment method: 'cash' or 'bank'")
    bank_account_code: Optional[str] = Field(None, max_length=10, description="Bank account code to use (if payment_method is 'bank'). If not provided, uses primary bank account from settings.")
    document_number: Optional[str] = Field(None, description="Optional document number/reference provided by user")
    
    @field_validator('amount', 'quantity', 'unit_price', 'debit_amount', 'credit_amount', mode='before')
    @classmethod
    def empty_string_to_none(cls, v):
        """Convert empty string to None for optional numeric fields"""
        if v == "":
            return None
        return v

    @field_validator('date', mode='before')
    @classmethod
    def validate_date_format(cls, v):
        """Validate date string format - accepts DD/MM/YYYY or YYYY-MM-DD"""
        if v is None:
            return None
        if isinstance(v, date):
            # If already a date object, convert to YYYY-MM-DD string format for consistency in processing
            return v.strftime('%Y-%m-%d')
        if isinstance(v, str):
            # Validate the format but keep original string
            # Try DD/MM/YYYY format first (our preferred format)
            try:
                dt = datetime.strptime(v, '%d/%m/%Y')
                return dt.strftime('%Y-%m-%d')  # Normalize to YYYY-MM-DD
            except ValueError:
                # Try YYYY-MM-DD format
                try:
                    datetime.strptime(v, '%Y-%m-%d')
                    return v  # Valid YYYY-MM-DD format, return as-is
                except ValueError:
                    raise ValueError(f"Invalid date format. Use YYYY-MM-DD or DD/MM/YYYY")
        return v
    
    @model_validator(mode='after')
    def validate_amount_calculation(self):
        """Validate that amount is provided either directly or via quantity × unit_price"""
        # If quantity and unit_price are provided, calculate amount
        if self.quantity is not None and self.unit_price is not None:
            # Validate quantity and unit_price are positive
            if self.quantity <= 0:
                raise ValueError("Quantity must be greater than 0")
            if self.unit_price <= 0:
                raise ValueError("Unit price must be greater than 0")
            calculated_amount = self.quantity * self.unit_price
            # If amount is also provided, it should match the calculation
            if self.amount is not None:
                if abs(self.amount - calculated_amount) > 0.01:  # Allow small floating point differences
                    raise ValueError(f"Amount ({self.amount}) does not match quantity × unit_price ({calculated_amount})")
            # Set amount from calculation
            self.amount = calculated_amount
        elif self.amount is not None:
            # Validate amount is positive if provided directly
            if self.amount <= 0:
                raise ValueError("Amount must be greater than 0")
        else:
            # If neither amount nor quantity/unit_price provided, raise error
            raise ValueError("Either 'amount' must be provided directly, or both 'quantity' and 'unit_price' must be provided")
        
        return self
    
    @model_validator(mode='after')
    def validate_debit_credit(self):
        """Validate debit/credit if provided"""
        if self.debit_amount is not None and self.credit_amount is not None:
            if self.debit_amount > 0 and self.credit_amount > 0:
                raise ValueError("Transaction cannot have both debit and credit amounts")
            if self.debit_amount == 0 and self.credit_amount == 0 and (self.debit_amount is not None or self.credit_amount is not None):
                raise ValueError("Transaction must have either debit or credit amount")
        return self


class TransactionUpdate(BaseModel):
    """Model for updating a transaction"""
    type: Optional[Literal["income", "expense"]] = None
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    account_code: Optional[str] = Field(None, max_length=10)
    amount: Optional[float] = Field(None, gt=0)
    quantity: Optional[float] = Field(None, gt=0, description="Quantity/units")
    unit_price: Optional[float] = Field(None, gt=0, description="Price per unit")
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    date: Optional[str] = None  # Transaction date (YYYY-MM-DD or DD/MM/YYYY format)
    expense_month: Optional[str] = Field(None, description="Month this expense belongs to (e.g., 'January, 2026')")
    # Double-entry bookkeeping fields
    debit_amount: Optional[float] = Field(None, ge=0, description="Debit amount")
    credit_amount: Optional[float] = Field(None, ge=0, description="Credit amount")
    payment_method: Optional[str] = Field(None, description="Payment method: 'cash' or 'bank'")
    bank_account_code: Optional[str] = Field(None, max_length=10, description="Bank account code")
    flat_id: Optional[str] = None
    document_number: Optional[str] = Field(None, description="Optional document number/reference")

    @field_validator('amount', 'quantity', 'unit_price', 'debit_amount', 'credit_amount', mode='before')
    @classmethod
    def empty_string_to_none(cls, v):
        """Convert empty string to None for optional numeric fields"""
        if v == "":
            return None
        return v
    
    @field_validator('description', 'category', 'account_code', 'payment_method', 'bank_account_code', 'document_number', 'expense_month', mode='before')
    @classmethod
    def empty_string_to_none_strings(cls, v):
        """Convert empty string to None for optional string fields"""
        if v == "":
            return None
        return v
    
    @model_validator(mode='after')
    def validate_amount_calculation(self):
        """Validate that amount is provided either directly or via quantity × unit_price"""
        # If both quantity and unit_price are provided, calculate amount
        if self.quantity is not None and self.unit_price is not None:
            calculated_amount = self.quantity * self.unit_price
            # If amount is also provided, it should match the calculation
            if self.amount is not None:
                if abs(self.amount - calculated_amount) > 0.01:
                    raise ValueError(f"Amount ({self.amount}) does not match quantity × unit_price ({calculated_amount})")
            # Set amount from calculation
            self.amount = calculated_amount
        # If only one of quantity/unit_price is provided, raise error
        elif (self.quantity is not None and self.unit_price is None) or (self.quantity is None and self.unit_price is not None):
            raise ValueError("Both 'quantity' and 'unit_price' must be provided together, or provide 'amount' directly")
        
        return self

class ReceiptCreate(BaseModel):
    """Model for creating a specialized Receipt Voucher"""
    date: str = Field(..., description="Voucher date (YYYY-MM-DD)")
    account_code: str = Field(..., description="Income account (e.g., 1100)")
    amount: float = Field(..., gt=0)
    payment_method: Literal["cash", "bank"] = Field(..., description="Source: cash or bank")
    bank_account_code: Optional[str] = None
    description: str = Field(..., max_length=500)
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    expense_month: Optional[str] = None
    flat_id: Optional[str] = None
    reference: Optional[str] = None
    received_from: Optional[str] = Field(None, max_length=100, description="Name of the person/entity payment received from")

class PaymentCreate(BaseModel):
    """Model for creating a specialized Payment Voucher"""
    date: str = Field(..., description="Voucher date (YYYY-MM-DD)")
    account_code: str = Field(..., description="Expense account (e.g., 5001)")
    amount: float = Field(..., gt=0)
    payment_method: Literal["cash", "bank"] = Field(..., description="Destination: cash or bank")
    bank_account_code: Optional[str] = None
    description: str = Field(..., max_length=500)
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    expense_month: Optional[str] = None
    flat_id: Optional[str] = None
    reference: Optional[str] = None

class TransactionResponse(BaseModel):
    """Model for transaction response"""
    id: str
    document_number: Optional[str] = None  # Individual document number (if exists) or None
    voucher_number: Optional[str] = None  # Voucher number from journal entry (QV-0001, JV-0001, etc.)
    type: Literal["income", "expense"]
    category: str
    account_code: Optional[str] = None
    amount: float
    quantity: Optional[float] = None  # Quantity/units if itemized
    unit_price: Optional[float] = None  # Price per unit if itemized
    description: str
    date: date
    expense_month: Optional[str] = None
    journal_entry_id: Optional[int] = None
    added_by: str  # User ID who created the transaction (as string for API consistency)
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
