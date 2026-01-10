"""Admin Guidelines API routes - Do's and Don'ts"""
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from typing import List, Optional

from app.database import get_db
from app.models.admin_guidelines import (
    AdminGuidelinesResponse,
    AdminAcknowledgmentRequest,
    AdminAcknowledgmentResponse
)
from app.models.user import UserResponse
from app.models_db import (
    User,
    AdminGuidelinesAcknowledgment,
    UserRole
)
from app.dependencies import get_current_user, get_current_admin_user
from app.utils.admin_guidelines import get_guidelines, get_guidelines_version

router = APIRouter()


@router.get("/guidelines", response_model=AdminGuidelinesResponse)
async def get_admin_guidelines(
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get Admin Guidelines - Do's and Don'ts (Admin only)
    All admins must read and acknowledge these guidelines
    """
    guidelines = get_guidelines()
    
    return AdminGuidelinesResponse(
        version=guidelines["version"],
        last_updated=guidelines["last_updated"],
        content=guidelines,
        requires_acknowledgment=guidelines.get("acknowledgment_required", True)
    )


@router.post("/guidelines/acknowledge", response_model=AdminAcknowledgmentResponse)
async def acknowledge_guidelines(
    acknowledgment: AdminAcknowledgmentRequest,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Acknowledge that you have read and understood the Admin Guidelines (Admin only)
    This is required for all admin users
    """
    current_version = get_guidelines_version()
    
    if acknowledgment.version != current_version:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Guidelines version mismatch. Current version is {current_version}"
        )
    
    # Check if already acknowledged
    result = await db.execute(
        select(AdminGuidelinesAcknowledgment).where(
            AdminGuidelinesAcknowledgment.user_id == int(current_user.id)
        )
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        # Update existing acknowledgment
        existing.acknowledged_version = acknowledgment.version
        existing.acknowledged_at = datetime.utcnow()
        existing.updated_at = datetime.utcnow()
    else:
        # Create new acknowledgment
        new_ack = AdminGuidelinesAcknowledgment(
            user_id=int(current_user.id),
            society_id=current_user.society_id,
            acknowledged_version=acknowledgment.version,
            acknowledged_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(new_ack)
    
    await db.commit()
    
    # Get user details
    result = await db.execute(
        select(User).where(User.id == int(current_user.id))
    )
    user = result.scalar_one()
    
    return AdminAcknowledgmentResponse(
        user_id=str(user.id),
        user_name=user.name,
        acknowledged=True,
        acknowledged_at=datetime.utcnow(),
        acknowledged_version=acknowledgment.version
    )


@router.get("/guidelines/acknowledgment-status", response_model=AdminAcknowledgmentResponse)
async def get_acknowledgment_status(
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Check if current admin has acknowledged the guidelines (Admin only)
    """
    result = await db.execute(
        select(AdminGuidelinesAcknowledgment).where(
            AdminGuidelinesAcknowledgment.user_id == int(current_user.id)
        )
    )
    acknowledgment = result.scalar_one_or_none()
    
    # Get user details
    result = await db.execute(
        select(User).where(User.id == int(current_user.id))
    )
    user = result.scalar_one()
    
    if acknowledgment:
        return AdminAcknowledgmentResponse(
            user_id=str(user.id),
            user_name=user.name,
            acknowledged=True,
            acknowledged_at=acknowledgment.acknowledged_at,
            acknowledged_version=acknowledgment.acknowledged_version
        )
    else:
        return AdminAcknowledgmentResponse(
            user_id=str(user.id),
            user_name=user.name,
            acknowledged=False,
            acknowledged_at=None,
            acknowledged_version=None
        )


@router.get("/guidelines/all-acknowledgments", response_model=List[AdminAcknowledgmentResponse])
async def get_all_acknowledgments(
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get acknowledgment status for all admin users in the society (Admin only)
    Useful for tracking which admins have read the guidelines
    """
    # Get all admin users in the society
    result = await db.execute(
        select(User).where(
            User.society_id == current_user.society_id,
            User.role.in_([UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.CHAIRMAN, UserRole.SECRETARY, UserRole.TREASURER])
        )
    )
    admin_users = result.scalars().all()
    
    # Get all acknowledgments
    result = await db.execute(
        select(AdminGuidelinesAcknowledgment).where(
            AdminGuidelinesAcknowledgment.society_id == current_user.society_id
        )
    )
    acknowledgments = {ack.user_id: ack for ack in result.scalars().all()}
    
    response_list = []
    for user in admin_users:
        ack = acknowledgments.get(user.id)
        response_list.append(AdminAcknowledgmentResponse(
            user_id=str(user.id),
            user_name=user.name,
            acknowledged=ack is not None,
            acknowledged_at=ack.acknowledged_at if ack else None,
            acknowledged_version=ack.acknowledged_version if ack else None
        ))
    
    return response_list

