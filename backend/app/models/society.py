"""Society models"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Literal
from datetime import datetime, date


class SocietyCreate(BaseModel):
    """Model for creating a new society (self-service registration)"""
    # Admin details
    admin_name: str = Field(..., min_length=1, max_length=100)
    admin_email: EmailStr
    admin_phone: Optional[str] = Field(None, min_length=10, max_length=20)
    admin_password: str = Field(..., min_length=6)
    
    # Society details
    society_name: str = Field(..., min_length=1, max_length=100)
    society_address: Optional[str] = None
    registration_no: Optional[str] = Field(None, max_length=100)
    pan_no: Optional[str] = Field(None, max_length=20)
    
    # Optional document URLs (uploaded to Cloudinary first)
    reg_cert_url: Optional[str] = None
    pan_card_url: Optional[str] = None
    logo_url: Optional[str] = None  # Society logo URL
    
    # Financial year and accounting settings
    financial_year_start: Optional[date] = Field(None, description="Financial year start date (e.g., 2024-04-01)")
    financial_year_end: Optional[date] = Field(None, description="Financial year end date (e.g., 2025-03-31)")
    accounting_type: Literal["cash", "accrual"] = Field("cash", description="Accounting method: cash or accrual")


class SocietyResponse(BaseModel):
    """Model for society response"""
    id: str = Field(..., alias="_id")
    name: str
    address: Optional[str] = None  # Legacy field
    registration_no: Optional[str] = None
    pan_no: Optional[str] = None
    reg_cert_url: Optional[str] = None
    pan_card_url: Optional[str] = None
    logo_url: Optional[str] = None
    total_flats: int
    financial_year_start: Optional[date] = None
    financial_year_end: Optional[date] = None
    accounting_type: Literal["cash", "accrual"] = "cash"
    # Address details
    address_line: Optional[str] = None
    pin_code: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    # Contact information
    email: Optional[str] = None
    landline: Optional[str] = None
    mobile: Optional[str] = None
    # GST registration
    gst_registration_applicable: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True


class SocietyUpdate(BaseModel):
    """Model for updating society settings"""
    financial_year_start: Optional[date] = None
    financial_year_end: Optional[date] = None
    accounting_type: Optional[Literal["cash", "accrual"]] = None
    logo_url: Optional[str] = None  # Society logo URL
    # Address details
    address_line: Optional[str] = None
    pin_code: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    # Contact information
    email: Optional[EmailStr] = None
    landline: Optional[str] = None
    mobile: Optional[str] = None
    # GST registration
    gst_registration_applicable: Optional[bool] = None


