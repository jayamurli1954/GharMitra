"""Users API routes"""
from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete

from app.database import get_db
from app.models.user import UserResponse, UserRole
from app.models_db import User
from app.dependencies import get_current_user, get_current_admin_user

router = APIRouter()


@router.get("/", response_model=List[UserResponse])
async def list_users(
    role: Optional[str] = None,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all users (optionally filter by role) - filtered by user's society"""
    # PRD: Multi-tenancy - Filter by society_id
    query = select(User).where(User.society_id == current_user.society_id).order_by(User.name)

    if role:
        if role not in ["admin", "member"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role must be 'admin' or 'member'"
            )
        query = query.where(User.role == role)

    result = await db.execute(query)
    users = result.scalars().all()

    return [
        UserResponse(
            id=str(user.id),
            email=user.email,
            name=user.name,
            apartment_number=user.apartment_number,
            phone_number=user.phone_number,
            role=user.role,
            created_at=user.created_at
        )
        for user in users
    ]


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific user by ID (must belong to user's society)"""
    try:
        user_id_int = int(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID"
        )

    # PRD: Multi-tenancy - Filter by society_id for security
    result = await db.execute(
        select(User).where(
            User.id == user_id_int,
            User.society_id == current_user.society_id
        )
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return UserResponse(
        id=str(user.id),
        email=user.email,
        name=user.name,
        apartment_number=user.apartment_number,
        phone_number=user.phone_number,
        role=user.role,
        created_at=user.created_at
    )


@router.patch("/{user_id}/role")
async def update_user_role(
    user_id: str,
    new_role: UserRole,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a user's role (admin only)"""
    # Don't allow changing own role
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own role"
        )

    try:
        user_id_int = int(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID"
        )

    # PRD: Multi-tenancy - Verify user belongs to same society
    result = await db.execute(
        select(User).where(
            User.id == user_id_int,
            User.society_id == current_user.society_id
        )
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    user.role = new_role
    user.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(user)

    return UserResponse(
        id=str(user.id),
        email=user.email,
        name=user.name,
        apartment_number=user.apartment_number,
        phone_number=user.phone_number,
        role=user.role,
        created_at=user.created_at
    )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a user (admin only)"""
    # Don't allow deleting own account
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )

    try:
        user_id_int = int(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID"
        )

    # PRD: Multi-tenancy - Delete user only if belongs to same society
    result = await db.execute(
        delete(User).where(
            User.id == user_id_int,
            User.society_id == current_user.society_id
        )
    )
    await db.commit()

    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return None


@router.get("/statistics/summary")
async def get_users_summary(
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get summary statistics for users (admin only) - filtered by user's society"""
    # PRD: Multi-tenancy - Filter by society_id
    result = await db.execute(
        select(User.role, func.count(User.id).label("count"))
        .where(User.society_id == current_user.society_id)
        .group_by(User.role)
    )

    role_counts = result.all()

    summary = {
        "total_users": 0,
        "admin_count": 0,
        "member_count": 0
    }

    for role, count in role_counts:
        summary["total_users"] += count
        if role == UserRole.ADMIN:
            summary["admin_count"] = count
        elif role == UserRole.MEMBER:
            summary["member_count"] = count

    return summary
