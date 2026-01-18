from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class VoucherAttachmentBase(BaseModel):
    file_name: str
    file_url: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None

class VoucherAttachmentCreate(VoucherAttachmentBase):
    journal_entry_id: int

class VoucherAttachmentResponse(VoucherAttachmentBase):
    id: int
    society_id: int
    journal_entry_id: int
    uploaded_by: int
    created_at: datetime

    class Config:
        from_attributes = True
