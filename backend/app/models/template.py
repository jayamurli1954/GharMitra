"""Template models for Resource Centre"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime


# ============ REQUEST MODELS ============

class GenerateDocumentRequest(BaseModel):
    """Request to generate document (no storage)"""
    form_data: Dict[str, str] = Field(..., description="User-filled fields only")


# ============ RESPONSE MODELS ============

class TemplateResponse(BaseModel):
    """Template details"""
    id: int
    template_name: str
    template_code: str
    category: str
    description: Optional[str] = None
    instructions: Optional[str] = None
    template_type: str  # 'blank_download' or 'auto_fill'
    can_autofill: bool
    autofill_fields: Optional[List[str]] = None
    icon_name: Optional[str] = None
    available_to: str = "all"
    display_order: int = 0


class CategoryResponse(BaseModel):
    """Category with template count"""
    category_code: str
    category_name: str
    category_description: Optional[str] = None
    icon_name: Optional[str] = None
    template_count: int = 0
    display_order: int = 0


class UsageStatsResponse(BaseModel):
    """Usage statistics (no content!)"""
    template_id: int
    template_name: str
    total_generated: int
    last_generated: Optional[datetime] = None


class TemplateDetailsResponse(BaseModel):
    """Complete template details including variables"""
    id: int
    template_name: str
    template_code: str
    category: str
    description: Optional[str] = None
    instructions: Optional[str] = None
    template_type: str
    can_autofill: bool
    autofill_fields: Optional[List[str]] = None
    template_variables: Optional[List[str]] = None
    icon_name: Optional[str] = None
    available_to: str
    display_order: int





