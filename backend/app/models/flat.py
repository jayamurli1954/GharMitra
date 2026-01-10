"""Flat models"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class FlatCreate(BaseModel):
    """Model for creating a new flat"""
    flat_number: str = Field(..., min_length=1, max_length=20)
    area_sqft: float = Field(..., gt=0)
    bedrooms: int = Field(default=2, ge=1, le=5, description="Number of bedrooms (typically 2 or 3)")
    occupants: int = Field(..., ge=0)
    owner_name: str = Field(..., min_length=1, max_length=100)
    owner_phone: Optional[str] = Field(None, max_length=20)
    owner_email: Optional[str] = None


class FlatUpdate(BaseModel):
    """Model for updating a flat"""
    flat_number: Optional[str] = Field(None, min_length=1, max_length=20, description="Flat number (e.g., A-101)")
    area_sqft: Optional[float] = Field(None, gt=0)
    bedrooms: Optional[int] = Field(None, ge=1, le=5, description="Number of bedrooms (typically 2 or 3)")
    occupants: Optional[int] = Field(None, ge=0)
    owner_name: Optional[str] = Field(None, min_length=1, max_length=100)
    owner_phone: Optional[str] = Field(None, max_length=20)
    owner_email: Optional[str] = None


class FlatResponse(BaseModel):
    """Model for flat response"""
    id: str = Field(..., alias="_id")
    flat_number: str
    area_sqft: float
    bedrooms: int = Field(default=2, description="Number of bedrooms")
    occupants: int
    owner_name: Optional[str] = None  # Can be None for auto-generated flats
    owner_phone: Optional[str] = None
    owner_email: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
