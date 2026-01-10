"""Supplementary billing models"""
from pydantic import BaseModel, Field
from typing import Optional, List
import datetime


class SupplementaryChargeCreate(BaseModel):
    """Model to create a charge for a specific flat"""
    flat_id: int
    amount: float = Field(..., gt=0)


class SupplementaryBillCreate(BaseModel):
    """Model to create a supplementary bill (special charge)"""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    date: datetime.date = Field(default_factory=datetime.date.today)
    approved_by: Optional[str] = None
    charges: List[SupplementaryChargeCreate]


class SupplementaryBillFlatResponse(BaseModel):
    id: int
    flat_id: int
    flat_number: str
    amount: float
    is_included_in_monthly: bool
    status: str

    class Config:
        from_attributes = True


class SupplementaryBillResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    date: datetime.date
    approved_by: Optional[str]
    status: str
    flats: List[SupplementaryBillFlatResponse]
    created_at: datetime.datetime

    class Config:
        from_attributes = True
