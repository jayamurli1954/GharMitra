"""Template API routes for Resource Centre (NO storage approach)"""
from fastapi import APIRouter, HTTPException, Depends, status, Response, Query
from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
import json

from app.database import get_db
from app.models.template import (
    GenerateDocumentRequest,
    TemplateResponse,
    CategoryResponse,
    UsageStatsResponse,
    TemplateDetailsResponse
)
from app.models.user import UserResponse
from app.models_db import (
    DocumentTemplate,
    TemplateCategory,
    TemplateUsageLog,
    User,
    Society,
    Flat
)
from app.dependencies import get_current_user, get_current_admin_user
from app.services.pdf_generator import pdf_generator

router = APIRouter(prefix="/api/templates", tags=["templates"])


# ========================================
# GET ENDPOINTS
# ========================================

@router.get("/categories", response_model=List[CategoryResponse])
async def get_categories(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all template categories with template counts.
    """
    # Get categories with template counts
    result = await db.execute(
        select(
            TemplateCategory,
            func.count(DocumentTemplate.id).label('template_count')
        )
        .outerjoin(
            DocumentTemplate,
            and_(
                TemplateCategory.category_code == DocumentTemplate.category,
                DocumentTemplate.is_active == True,
                DocumentTemplate.society_id == current_user.society_id
            )
        )
        .where(TemplateCategory.is_active == True)
        .group_by(TemplateCategory.id)
        .order_by(TemplateCategory.display_order)
    )
    
    categories = []
    for row in result.all():
        cat, count = row
        categories.append(CategoryResponse(
            category_code=cat.category_code,
            category_name=cat.category_name,
            category_description=cat.category_description,
            icon_name=cat.icon_name,
            template_count=count or 0,
            display_order=cat.display_order
        ))
    
    return categories


@router.get("/", response_model=List[TemplateResponse])
async def get_templates(
    category: Optional[str] = Query(None, description="Filter by category"),
    template_type: Optional[str] = Query(None, description="Filter by type: 'blank_download' or 'auto_fill'"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get templates, optionally filtered by category/type.
    """
    query = select(DocumentTemplate).where(
        and_(
            DocumentTemplate.is_active == True,
            DocumentTemplate.society_id == current_user.society_id
        )
    )
    
    if category:
        query = query.where(DocumentTemplate.category == category)
    
    if template_type:
        query = query.where(DocumentTemplate.template_type == template_type)
    
    # Check user role for access control
    if current_user.role not in ['admin', 'super_admin']:
        # Filter by available_to
        query = query.where(
            or_(
                DocumentTemplate.available_to == 'all',
                DocumentTemplate.available_to == current_user.role
            )
        )
    
    query = query.order_by(DocumentTemplate.display_order, DocumentTemplate.template_name)
    
    result = await db.execute(query)
    templates = result.scalars().all()
    
    response_list = []
    for template in templates:
        # Parse JSON fields
        autofill_fields = None
        if template.autofill_fields:
            try:
                autofill_fields = json.loads(template.autofill_fields)
            except:
                pass
        
        response_list.append(TemplateResponse(
            id=template.id,
            template_name=template.template_name,
            template_code=template.template_code,
            category=template.category,
            description=template.description,
            instructions=template.instructions,
            template_type=template.template_type,
            can_autofill=template.can_autofill,
            autofill_fields=autofill_fields,
            icon_name=template.icon_name,
            available_to=template.available_to,
            display_order=template.display_order
        ))
    
    return response_list


@router.get("/{template_id}", response_model=TemplateDetailsResponse)
async def get_template_details(
    template_id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get single template details including variables.
    """
    result = await db.execute(
        select(DocumentTemplate).where(
            and_(
                DocumentTemplate.id == template_id,
                DocumentTemplate.is_active == True,
                DocumentTemplate.society_id == current_user.society_id
            )
        )
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    # Check access
    if template.available_to not in ('all', current_user.role) and current_user.role not in ['admin', 'super_admin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this template"
        )
    
    # Parse JSON fields
    template_variables = None
    if template.template_variables:
        try:
            template_variables = json.loads(template.template_variables)
        except:
            pass
    
    autofill_fields = None
    if template.autofill_fields:
        try:
            autofill_fields = json.loads(template.autofill_fields)
        except:
            pass
    
    return TemplateDetailsResponse(
        id=template.id,
        template_name=template.template_name,
        template_code=template.template_code,
        category=template.category,
        description=template.description,
        instructions=template.instructions,
        template_type=template.template_type,
        can_autofill=template.can_autofill,
        autofill_fields=autofill_fields,
        template_variables=template_variables,
        icon_name=template.icon_name,
        available_to=template.available_to,
        display_order=template.display_order
    )


@router.get("/{template_id}/download-blank")
async def download_blank_template(
    template_id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Download blank template (for blank_download type).
    Just returns template with placeholder text, no auto-fill.
    """
    # Get template
    result = await db.execute(
        select(DocumentTemplate).where(
            and_(
                DocumentTemplate.id == template_id,
                DocumentTemplate.is_active == True,
                DocumentTemplate.society_id == current_user.society_id
            )
        )
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    # Check access
    if template.available_to not in ('all', current_user.role) and current_user.role not in ['admin', 'super_admin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this template"
        )
    
    # Check it's a blank_download type
    if template.template_type != 'blank_download':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This template requires auto-fill. Use /generate endpoint instead."
        )
    
    # Get society data for header
    society_result = await db.execute(
        select(Society).where(Society.id == current_user.society_id)
    )
    society = society_result.scalar_one_or_none()
    
    # Get template HTML (with {{placeholders}} still there)
    html_content = template.template_html
    
    # Prepare header data for PDF (logo, name, address)
    header_data = {
        'society_name': society.name if society else '',
        'society_address': society.address if society else '',
        'society_logo_url': society.logo_url if society and society.logo_url else None,
    }
    
    # Generate PDF with placeholders still there and header
    # (Member will fill manually)
    pdf_bytes = pdf_generator.html_to_pdf(html_content, header_data)
    
    # Log usage (optional - statistics only)
    await log_template_usage(
        template_id=template.id,
        member_id=int(current_user.id),
        society_id=current_user.society_id,
        template_code=template.template_code,
        db=db
    )
    
    # Return PDF
    filename = f"{template.template_code}_blank.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# ========================================
# POST ENDPOINTS
# ========================================

@router.post("/{template_id}/generate")
async def generate_document(
    template_id: int,
    request: GenerateDocumentRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate document with auto-fill (NO STORAGE!).
    
    This is the CRITICAL endpoint for no-storage approach:
    1. Get template HTML
    2. Auto-fill from user profile
    3. Merge with user input
    4. Generate PDF in memory
    5. Return PDF directly
    6. NO database write of filled data!
    """
    # Get template
    template_result = await db.execute(
        select(DocumentTemplate).where(
            and_(
                DocumentTemplate.id == template_id,
                DocumentTemplate.is_active == True,
                DocumentTemplate.society_id == current_user.society_id
            )
        )
    )
    template = template_result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    # Check access
    if template.available_to not in ('all', current_user.role) and current_user.role not in ['admin', 'super_admin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this template"
        )
    
    # Check it's an auto_fill type
    if template.template_type != 'auto_fill':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This template doesn't support auto-fill. Use /download-blank endpoint instead."
        )
    
    # Get member profile data
    user_result = await db.execute(
        select(User).where(User.id == int(current_user.id))
    )
    user = user_result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get flat data if available
    flat_number = None
    if hasattr(user, 'apartment_number'):
        flat_number = user.apartment_number
    
    # Get society data
    society_result = await db.execute(
        select(Society).where(Society.id == current_user.society_id)
    )
    society = society_result.scalar_one_or_none()
    
    # Auto-fill data from profile
    auto_fill_data = {
        # Member info
        'member_name': user.name or '',
        'flat_number': flat_number or '',
        'member_email': user.email or '',
        'member_phone': user.phone_number or '',
        
        # Society info
        'society_name': society.name if society else '',
        'society_address': society.address if society else '',
        'society_registration': society.registration_no if society else '',
        
        # System info
        'current_date': datetime.now().strftime('%d-%m-%Y'),
        'current_time': datetime.now().strftime('%I:%M %p'),
        'current_year': str(datetime.now().year),
        'current_month': datetime.now().strftime('%B'),
        
        # Add more auto-fill fields as needed
    }
    
    # Merge with user-provided data
    complete_data = {**auto_fill_data, **request.form_data}
    
    # Prepare header data for PDF (logo, name, address)
    header_data = {
        'society_name': society.name if society else '',
        'society_address': society.address if society else '',
        'society_logo_url': society.logo_url if society and society.logo_url else None,
    }
    
    # Generate PDF (in memory!) with header
    pdf_bytes = pdf_generator.generate_document(
        template.template_html,
        complete_data,
        header_data
    )
    
    # Log usage (statistics only - NOT content!)
    await log_template_usage(
        template_id=template.id,
        member_id=int(current_user.id),
        society_id=current_user.society_id,
        template_code=template.template_code,
        db=db
    )
    
    # Return PDF
    filename = f"{template.template_code}_{flat_number or 'doc'}_{datetime.now().strftime('%Y%m%d')}.pdf"
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
    
    # Function ends here
    # Python garbage collector automatically deletes:
    # - complete_data
    # - request.form_data
    # - pdf_bytes (after response sent)
    # NOTHING STORED! ✅


# ========================================
# ADMIN ENDPOINTS
# ========================================

@router.post("/admin/seed-templates")
async def seed_templates_endpoint(
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Manually seed sample templates (admin only).
    Useful if templates weren't seeded during migration.
    """
    from app.database import seed_sample_templates
    from sqlalchemy import text
    
    # Check if templates already exist
    result = await db.execute(text("SELECT COUNT(*) as count FROM document_templates WHERE society_id = ?"), [current_user.society_id])
    count = result.fetchone()[0]
    
    if count > 0:
        return {
            "message": f"Templates already exist ({count} templates). Skipping seed.",
            "existing_count": count
        }
    
    # Seed templates for current user's society
    await seed_sample_templates(db, society_id=current_user.society_id)
    
    # Get new count
    result = await db.execute(text("SELECT COUNT(*) as count FROM document_templates WHERE society_id = ?"), [current_user.society_id])
    new_count = result.fetchone()[0]
    
    return {
        "message": f"Successfully seeded {new_count} sample templates",
        "templates_count": new_count
    }


@router.get("/admin/usage-stats", response_model=List[UsageStatsResponse])
async def get_usage_statistics(
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get usage statistics (admin only).
    Shows WHAT templates are used, not WHAT was in them.
    """
    result = await db.execute(
        select(
            DocumentTemplate.id.label('template_id'),
            DocumentTemplate.template_name,
            func.count(TemplateUsageLog.id).label('total_generated'),
            func.max(TemplateUsageLog.generated_at).label('last_generated')
        )
        .outerjoin(
            TemplateUsageLog,
            and_(
                DocumentTemplate.id == TemplateUsageLog.template_id,
                TemplateUsageLog.society_id == current_user.society_id
            )
        )
        .where(
            and_(
                DocumentTemplate.is_active == True,
                DocumentTemplate.society_id == current_user.society_id
            )
        )
        .group_by(DocumentTemplate.id)
        .order_by(func.count(TemplateUsageLog.id).desc())
    )
    
    stats = []
    for row in result.all():
        stats.append(UsageStatsResponse(
            template_id=row.template_id,
            template_name=row.template_name,
            total_generated=row.total_generated or 0,
            last_generated=row.last_generated
        ))
    
    return stats


# ========================================
# HELPER FUNCTIONS
# ========================================

async def log_template_usage(
    template_id: int,
    member_id: int,
    society_id: int,
    template_code: str,
    db: AsyncSession,
    platform: str = 'mobile'
):
    """
    Log that a template was used (statistics only).
    
    CRITICAL: We only log THAT it was generated,
    NOT what data was in it!
    """
    usage_log = TemplateUsageLog(
        template_id=template_id,
        template_code=template_code,
        society_id=society_id,
        member_id=member_id,
        platform=platform,
        generated_at=datetime.utcnow()
    )
    
    db.add(usage_log)
    await db.commit()

