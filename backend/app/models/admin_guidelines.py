"""Admin Guidelines and Do's & Don'ts models"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class AdminGuidelinesResponse(BaseModel):
    """Response model for admin guidelines"""
    version: str
    last_updated: str
    content: dict  # Structured content with sections
    requires_acknowledgment: bool = True


class AdminAcknowledgmentRequest(BaseModel):
    """Request model for acknowledging guidelines"""
    version: str = Field(..., description="Version of guidelines being acknowledged")


class AdminAcknowledgmentResponse(BaseModel):
    """Response model for acknowledgment status"""
    user_id: str
    user_name: str
    acknowledged: bool
    acknowledged_at: Optional[datetime] = None
    acknowledged_version: Optional[str] = None

