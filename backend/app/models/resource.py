"""Resource Center models"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ResourceFileCreate(BaseModel):
    """Model for creating a resource file"""
    file_name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = Field(None, description="Category: 'noc', 'form', 'template', 'other'")
    file_url: str = Field(..., description="URL to the file (Cloudinary or other storage)")


class ResourceFileResponse(BaseModel):
    """Model for resource file response"""
    id: str = Field(..., alias="_id")
    society_id: int
    file_name: str
    description: Optional[str] = None
    category: Optional[str] = None
    file_url: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        from_attributes = True


class NOCGenerateRequest(BaseModel):
    """Model for generating NOC"""
    flat_id: int
    member_id: int
    move_out_date: str = Field(..., description="Move-out date in YYYY-MM-DD format")
    move_in_date: Optional[str] = Field(None, description="Move-in date in YYYY-MM-DD format")
    noc_type: str = Field(..., description="Type: 'society_move_out' or 'owner_tenant_move_in'")
    new_owner_name: Optional[str] = None
    new_tenant_name: Optional[str] = None
    lease_start_date: Optional[str] = None
    lease_duration_months: Optional[int] = None
    tenant_family_members: Optional[int] = None


class NOCResponse(BaseModel):
    """Model for NOC response"""
    id: str = Field(..., alias="_id")
    flat_id: int
    member_id: int
    noc_type: str
    noc_number: str
    file_url: str
    qr_code_url: Optional[str] = None
    generated_at: datetime
    status: str = Field(..., description="Status: 'pending', 'approved', 'issued'")

    class Config:
        populate_by_name = True








