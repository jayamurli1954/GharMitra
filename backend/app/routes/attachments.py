import os
import shutil
import uuid
from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.database import get_db
from app.models.user import UserResponse
from app.models.voucher_attachment import VoucherAttachmentResponse
from app.models_db import VoucherAttachment, JournalEntry
from app.dependencies import get_current_user, get_current_admin_user

router = APIRouter()

UPLOAD_DIR = "uploads/vouchers"
ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".docx"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

@router.post("/upload/{journal_entry_id}", response_model=VoucherAttachmentResponse, status_code=status.HTTP_201_CREATED)
async def upload_voucher_attachment(
    journal_entry_id: int,
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload a voucher attachment (receipt/bill) for a journal entry"""
    # 1. Verify journal entry exists and belongs to society
    result = await db.execute(
        select(JournalEntry).where(
            JournalEntry.id == journal_entry_id,
            JournalEntry.society_id == current_user.society_id
        )
    )
    journal_entry = result.scalars().first()
    if not journal_entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")

    # 2. Validate file type
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Supported: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # 3. Create upload directory if not exists (safety)
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    # 4. Generate unique file name
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    # 5. Save file and check size
    file_size = 0
    with open(file_path, "wb") as buffer:
        content = await file.read()
        file_size = len(content)
        if file_size > MAX_FILE_SIZE:
            # Delete the file if it's too large
            buffer.close()
            os.remove(file_path)
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size is 5MB."
            )
        buffer.write(content)

    # 6. Create database record
    attachment = VoucherAttachment(
        society_id=current_user.society_id,
        journal_entry_id=journal_entry_id,
        file_name=file.filename,
        file_url=file_path.replace("\\", "/"),  # Normalize for cross-platform
        file_size=file_size,
        mime_type=file.content_type,
        uploaded_by=current_user.id
    )

    db.add(attachment)
    await db.commit()
    await db.refresh(attachment)

    return attachment


@router.get("/{attachment_id}", response_class=FileResponse)
async def get_attachment(
    attachment_id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Securely serve an attachment"""
    result = await db.execute(
        select(VoucherAttachment).where(
            VoucherAttachment.id == attachment_id,
            VoucherAttachment.society_id == current_user.society_id
        )
    )
    attachment = result.scalars().first()
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")

    if not os.path.exists(attachment.file_url):
        raise HTTPException(status_code=404, detail="Physical file not found")

    return FileResponse(
        path=attachment.file_url,
        filename=attachment.file_name,
        media_type=attachment.mime_type
    )


@router.delete("/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_attachment(
    attachment_id: int,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete an attachment"""
    result = await db.execute(
        select(VoucherAttachment).where(
            VoucherAttachment.id == attachment_id,
            VoucherAttachment.society_id == current_user.society_id
        )
    )
    attachment = result.scalars().first()
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")

    # Delete physical file
    if os.path.exists(attachment.file_url):
        os.remove(attachment.file_url)

    # Delete DB record
    await db.delete(attachment)
    await db.commit()

    return None


@router.get("/journal/{journal_entry_id}", response_model=List[VoucherAttachmentResponse])
async def list_journal_attachments(
    journal_entry_id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all attachments for a specific journal entry"""
    result = await db.execute(
        select(VoucherAttachment).where(
            VoucherAttachment.journal_entry_id == journal_entry_id,
            VoucherAttachment.society_id == current_user.society_id
        )
    )
    return result.scalars().all()
