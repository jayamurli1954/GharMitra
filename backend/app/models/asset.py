from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional, List
from decimal import Decimal
from app.models_db import AssetCategory, AcquisitionType, DepreciationMethod

class AssetBase(BaseModel):
    name: str = Field(..., description="Name of the asset")
    category: AssetCategory = Field(..., description="Category of the asset")
    account_code: Optional[str] = Field(None, description="Linked account code from Chart of Accounts")
    quantity: int = Field(1, ge=1)
    location: Optional[str] = None
    status: str = Field("Active")
    acquisition_type: AcquisitionType = Field(..., description="Builder Handover or Society Purchase")
    handover_date: Optional[date] = None
    purchase_date: Optional[date] = None
    original_cost: Decimal = Field(Decimal("0.00"), ge=0)
    depreciation_method: DepreciationMethod = Field(DepreciationMethod.STRAIGHT_LINE)
    depreciation_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    useful_life_years: Optional[int] = Field(None, ge=0)
    residual_value: Decimal = Field(Decimal("1.00"), ge=0)
    amc_vendor: Optional[str] = None
    amc_expiry: Optional[date] = None
    insurance_policy_no: Optional[str] = None
    insurance_expiry: Optional[date] = None
    vendor_name: Optional[str] = None
    invoice_no: Optional[str] = None
    notes: Optional[str] = None

class AssetCreate(AssetBase):
    pass

class AssetUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    amc_vendor: Optional[str] = None
    amc_expiry: Optional[date] = None
    insurance_policy_no: Optional[str] = None
    insurance_expiry: Optional[date] = None
    notes: Optional[str] = None
    is_scrapped: Optional[bool] = None

class AssetResponse(AssetBase):
    id: int
    society_id: int
    asset_code: Optional[str] = None
    is_scrapped: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
