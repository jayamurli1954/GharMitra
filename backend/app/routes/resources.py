"""Resource Center API routes"""
from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File, Form
from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import os
import uuid

from app.database import get_db
from app.models.resource import ResourceFileCreate, ResourceFileResponse, NOCGenerateRequest, NOCResponse
from app.models.user import UserResponse
from app.models_db import ResourceFile, NOCDocument, Flat, User
from app.dependencies import get_current_user, get_current_admin_user

router = APIRouter()

UPLOAD_DIR_RESOURCES = "uploads/resources"
ALLOWED_EXTENSIONS_RESOURCES = {".pdf", ".jpg", ".jpeg", ".png", ".docx", ".xlsx", ".xls"}
MAX_SIZE_RESOURCES = 10 * 1024 * 1024  # 10MB


@router.get("/files", response_model=List[ResourceFileResponse])
async def list_resource_files(
    category: Optional[str] = None,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all resource files (optionally filter by category)"""
    query = select(ResourceFile).where(ResourceFile.society_id == current_user.society_id)
    
    if category:
        query = query.where(ResourceFile.category == category)
    
    query = query.order_by(ResourceFile.created_at.desc())
    
    result = await db.execute(query)
    files = result.scalars().all()
    
    return [
        ResourceFileResponse(
            id=str(file.id),
            society_id=file.society_id,
            file_name=file.file_name,
            description=file.description,
            category=file.category,
            file_url=file.file_url,
            file_size=file.file_size,
            mime_type=file.mime_type,
            created_at=file.created_at,
            updated_at=file.updated_at
        )
        for file in files
    ]


@router.post("/files/upload", response_model=ResourceFileResponse, status_code=status.HTTP_201_CREATED)
async def upload_resource_file(
    file: UploadFile = File(...),
    category: str = Form(...),
    description: Optional[str] = Form(None),
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload a new resource file with actual file upload (admin only)"""
    # 1. Validate extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS_RESOURCES:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Supported: {', '.join(ALLOWED_EXTENSIONS_RESOURCES)}"
        )
    
    # 2. Create directory
    os.makedirs(UPLOAD_DIR_RESOURCES, exist_ok=True)
    
    # 3. Generate unique filename
    unique_filename = f"resource_{current_user.society_id}_{category}_{uuid.uuid4().hex}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR_RESOURCES, unique_filename)
    
    # 4. Save file
    try:
        content = await file.read()
        file_size = len(content)
        if file_size > MAX_SIZE_RESOURCES:
            raise HTTPException(status_code=400, detail="File too large (max 10MB)")
        
        with open(file_path, "wb") as buffer:
            buffer.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    # 5. Create database record
    new_file = ResourceFile(
        society_id=current_user.society_id,
        file_name=file.filename,
        description=description,
        category=category,
        file_url=file_path.replace("\\", "/"),  # Normalize for cross-platform
        file_size=file_size,
        mime_type=file.content_type,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        created_by=current_user.id
    )
    
    db.add(new_file)
    await db.commit()
    await db.refresh(new_file)
    
    return ResourceFileResponse(
        id=str(new_file.id),
        society_id=new_file.society_id,
        file_name=new_file.file_name,
        description=new_file.description,
        category=new_file.category,
        file_url=new_file.file_url,
        file_size=new_file.file_size,
        mime_type=new_file.mime_type,
        created_at=new_file.created_at,
        updated_at=new_file.updated_at
    )


@router.post("/files", response_model=ResourceFileResponse, status_code=status.HTTP_201_CREATED)
async def create_resource_file(
    file_data: ResourceFileCreate,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a resource file record with existing URL (admin only)"""
    new_file = ResourceFile(
        society_id=current_user.society_id,
        file_name=file_data.file_name,
        description=file_data.description,
        category=file_data.category or "other",
        file_url=file_data.file_url,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        created_by=current_user.id
    )
    
    db.add(new_file)
    await db.commit()
    await db.refresh(new_file)
    
    return ResourceFileResponse(
        id=str(new_file.id),
        society_id=new_file.society_id,
        file_name=new_file.file_name,
        description=new_file.description,
        category=new_file.category,
        file_url=new_file.file_url,
        file_size=new_file.file_size,
        mime_type=new_file.mime_type,
        created_at=new_file.created_at,
        updated_at=new_file.updated_at
    )


@router.get("/files/{file_id}/download")
async def download_resource_file(
    file_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Download a resource file"""
    from fastapi.responses import FileResponse
    
    try:
        file_id_int = int(file_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file ID"
        )
    
    result = await db.execute(
        select(ResourceFile).where(
            ResourceFile.id == file_id_int,
            ResourceFile.society_id == current_user.society_id
        )
    )
    file = result.scalar_one_or_none()
    
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource file not found"
        )
    
    if not os.path.exists(file.file_url):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on server"
        )
    
    return FileResponse(
        path=file.file_url,
        filename=file.file_name,
        media_type=file.mime_type or "application/octet-stream"
    )


@router.delete("/files/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resource_file(
    file_id: str,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a resource file (admin only)"""
    try:
        file_id_int = int(file_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file ID"
        )
    
    result = await db.execute(
        select(ResourceFile).where(
            ResourceFile.id == file_id_int,
            ResourceFile.society_id == current_user.society_id
        )
    )
    file = result.scalar_one_or_none()
    
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource file not found"
        )
    
    # Delete physical file if it exists
    if os.path.exists(file.file_url):
        try:
            os.remove(file.file_url)
        except Exception as e:
            # Log error but continue with DB deletion
            pass
    
    await db.delete(file)
    await db.commit()
    
    return None


@router.post("/noc/generate", response_model=NOCResponse, status_code=status.HTTP_201_CREATED)
async def generate_noc(
    noc_data: NOCGenerateRequest,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate a NOC document (admin only)"""
    import logging
    logger = logging.getLogger(__name__)
    
    # Validate flat exists
    result = await db.execute(select(Flat).where(Flat.id == noc_data.flat_id))
    flat = result.scalar_one_or_none()
    
    if not flat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Flat not found"
        )
    
    # Validate member exists
    result = await db.execute(select(User).where(User.id == noc_data.member_id))
    member = result.scalar_one_or_none()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )
    
    # Generate unique NOC number
    noc_number = f"NOC-{flat.flat_number}-{datetime.utcnow().strftime('%Y%m%d')}-{noc_data.member_id}"
    
    # TODO: Generate PDF document and upload to Cloudinary
    # For now, we'll create a placeholder URL
    # In production, this should:
    # 1. Generate PDF using the template
    # 2. Add QR code for verification
    # 3. Upload to Cloudinary
    # 4. Return the file URL
    
    file_url = f"https://placeholder.com/noc/{noc_number}.pdf"  # Placeholder
    qr_code_url = f"https://placeholder.com/qr/{noc_number}.png"  # Placeholder
    
    new_noc = NOCDocument(
        society_id=current_user.society_id,
        flat_id=noc_data.flat_id,
        member_id=noc_data.member_id,
        noc_type=noc_data.noc_type,
        noc_number=noc_number,
        file_url=file_url,
        qr_code_url=qr_code_url,
        move_out_date=datetime.strptime(noc_data.move_out_date, "%Y-%m-%d").date() if noc_data.move_out_date else None,
        move_in_date=datetime.strptime(noc_data.move_in_date, "%Y-%m-%d").date() if noc_data.move_in_date else None,
        new_owner_name=noc_data.new_owner_name,
        new_tenant_name=noc_data.new_tenant_name,
        lease_start_date=datetime.strptime(noc_data.lease_start_date, "%Y-%m-%d").date() if noc_data.lease_start_date else None,
        lease_duration_months=noc_data.lease_duration_months,
        status="pending",
        generated_at=datetime.utcnow()
    )
    
    db.add(new_noc)
    await db.commit()
    await db.refresh(new_noc)
    
    logger.info(f"Generated NOC {noc_number} for flat {flat.flat_number}, member {member.name}")
    
    return NOCResponse(
        id=str(new_noc.id),
        flat_id=new_noc.flat_id,
        member_id=new_noc.member_id,
        noc_type=new_noc.noc_type,
        noc_number=new_noc.noc_number,
        file_url=new_noc.file_url,
        qr_code_url=new_noc.qr_code_url,
        generated_at=new_noc.generated_at,
        status=new_noc.status
    )


@router.get("/noc", response_model=List[NOCResponse])
async def list_noc_documents(
    flat_id: Optional[int] = None,
    member_id: Optional[int] = None,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get NOC documents (filtered by flat or member if specified)"""
    query = select(NOCDocument).where(NOCDocument.society_id == current_user.society_id)
    
    if flat_id:
        query = query.where(NOCDocument.flat_id == flat_id)
    
    if member_id:
        query = query.where(NOCDocument.member_id == member_id)
    
    # Non-admin users can only see their own NOCs
    if current_user.role != "admin":
        query = query.where(NOCDocument.member_id == int(current_user.id))
    
    query = query.order_by(NOCDocument.generated_at.desc())
    
    result = await db.execute(query)
    nocs = result.scalars().all()
    
    return [
        NOCResponse(
            id=str(noc.id),
            flat_id=noc.flat_id,
            member_id=noc.member_id,
            noc_type=noc.noc_type,
            noc_number=noc.noc_number,
            file_url=noc.file_url,
            qr_code_url=noc.qr_code_url,
            generated_at=noc.generated_at,
            status=noc.status
        )
        for noc in nocs
    ]


@router.get("/noc/{noc_id}", response_model=NOCResponse)
async def get_noc_document(
    noc_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific NOC document"""
    try:
        noc_id_int = int(noc_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid NOC ID"
        )
    
    query = select(NOCDocument).where(
        NOCDocument.id == noc_id_int,
        NOCDocument.society_id == current_user.society_id
    )
    
    # Non-admin users can only see their own NOCs
    if current_user.role != "admin":
        query = query.where(NOCDocument.member_id == int(current_user.id))
    
    result = await db.execute(query)
    noc = result.scalar_one_or_none()
    
    if not noc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="NOC document not found"
        )
    
    return NOCResponse(
        id=str(noc.id),
        flat_id=noc.flat_id,
        member_id=noc.member_id,
        noc_type=noc.noc_type,
        noc_number=noc.noc_number,
        file_url=noc.file_url,
        qr_code_url=noc.qr_code_url,
        generated_at=noc.generated_at,
        status=noc.status
    )


@router.put("/noc/{noc_id}/issue", response_model=NOCResponse)
async def issue_noc(
    noc_id: str,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Issue/approve a NOC document (admin only)"""
    try:
        noc_id_int = int(noc_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid NOC ID"
        )
    
    result = await db.execute(
        select(NOCDocument).where(
            NOCDocument.id == noc_id_int,
            NOCDocument.society_id == current_user.society_id
        )
    )
    noc = result.scalar_one_or_none()
    
    if not noc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="NOC document not found"
        )
    
    # Update status and issue details
    noc.status = "issued"
    noc.issued_at = datetime.utcnow()
    noc.issued_by = int(current_user.id)
    
    await db.commit()
    await db.refresh(noc)
    
    return NOCResponse(
        id=str(noc.id),
        flat_id=noc.flat_id,
        member_id=noc.member_id,
        noc_type=noc.noc_type,
        noc_number=noc.noc_number,
        file_url=noc.file_url,
        qr_code_url=noc.qr_code_url,
        generated_at=noc.generated_at,
        status=noc.status
    )








