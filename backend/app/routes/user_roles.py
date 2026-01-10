"""User Role Assignment API routes"""
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime
from typing import List, Optional

from app.database import get_db
from app.models.user import UserResponse
from app.models_db import (
    User, CustomRole, UserRoleAssignment
)
from app.dependencies import get_current_admin_user
from app.utils.audit import log_action

router = APIRouter()


@router.post("/users/{user_id}/roles/{role_id}", status_code=status.HTTP_201_CREATED)
async def assign_role_to_user(
    user_id: int,
    role_id: int,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Assign a role to a user (admin only)
    IMPORTANT: Be careful when assigning Auditor role - only assign to external auditor user IDs
    """
    # Verify user belongs to same society
    user_result = await db.execute(
        select(User).where(
            and_(
                User.id == user_id,
                User.society_id == current_user.society_id
            )
        )
    )
    user = user_result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify role belongs to same society
    role_result = await db.execute(
        select(CustomRole).where(
            and_(
                CustomRole.id == role_id,
                CustomRole.society_id == current_user.society_id,
                CustomRole.is_active == True
            )
        )
    )
    role = role_result.scalar_one_or_none()
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found or inactive"
        )
    
    # Check if assignment already exists
    existing_result = await db.execute(
        select(UserRoleAssignment).where(
            and_(
                UserRoleAssignment.user_id == user_id,
                UserRoleAssignment.role_id == role_id,
                UserRoleAssignment.is_active == True
            )
        )
    )
    existing = existing_result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has this role assigned"
        )
    
    # Create assignment
    assignment = UserRoleAssignment(
        user_id=user_id,
        role_id=role_id,
        assigned_by=int(current_user.id),
        is_active=True
    )
    db.add(assignment)
    await db.commit()
    await db.refresh(assignment)
    
    # Log action with warning if auditor role
    warning_note = ""
    if role.role_code == "auditor":
        warning_note = "WARNING: Auditor role assigned. This user can only view transactions and reports, cannot modify records."
    
    await log_action(
        db=db,
        society_id=current_user.society_id,
        user_id=int(current_user.id),
        action_type="create",
        entity_type="user_role_assignment",
        entity_id=assignment.id,
        new_values={
            "user_id": user_id,
            "user_name": user.name,
            "role_id": role_id,
            "role_name": role.role_name,
            "role_code": role.role_code
        },
    )
    
    return {
        "message": f"Role '{role.role_name}' assigned to user '{user.name}'",
        "assignment_id": str(assignment.id),
        "user_id": str(user_id),
        "user_name": user.name,
        "role_id": str(role_id),
        "role_name": role.role_name,
        "warning": warning_note if warning_note else None
    }


@router.delete("/users/{user_id}/roles/{role_id}")
async def remove_role_from_user(
    user_id: int,
    role_id: int,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Remove a role from a user (admin only)"""
    # Verify user belongs to same society
    user_result = await db.execute(
        select(User).where(
            and_(
                User.id == user_id,
                User.society_id == current_user.society_id
            )
        )
    )
    user = user_result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Find assignment
    assignment_result = await db.execute(
        select(UserRoleAssignment).where(
            and_(
                UserRoleAssignment.user_id == user_id,
                UserRoleAssignment.role_id == role_id,
                UserRoleAssignment.is_active == True
            )
        )
    )
    assignment = assignment_result.scalar_one_or_none()
    
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role assignment not found"
        )
    
    # Get role name for logging
    role_result = await db.execute(
        select(CustomRole).where(CustomRole.id == role_id)
    )
    role = role_result.scalar_one_or_none()
    role_name = role.role_name if role else "Unknown"
    
    # Deactivate assignment (soft delete)
    assignment.is_active = False
    await db.commit()
    
    # Log action
    await log_action(
        db=db,
        society_id=current_user.society_id,
        user_id=int(current_user.id),
        action_type="delete",
        entity_type="user_role_assignment",
        entity_id=assignment.id,
        old_values={
            "user_id": user_id,
            "user_name": user.name,
            "role_id": role_id,
            "role_name": role_name
        },
    )
    
    return {
        "message": f"Role '{role_name}' removed from user '{user.name}'"
    }


@router.get("/users/{user_id}/roles", response_model=List[dict])
async def get_user_roles(
    user_id: int,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all roles assigned to a user (admin only)"""
    # Verify user belongs to same society
    user_result = await db.execute(
        select(User).where(
            and_(
                User.id == user_id,
                User.society_id == current_user.society_id
            )
        )
    )
    user = user_result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get active role assignments
    result = await db.execute(
        select(UserRoleAssignment, CustomRole)
        .join(CustomRole, UserRoleAssignment.role_id == CustomRole.id)
        .where(
            and_(
                UserRoleAssignment.user_id == user_id,
                UserRoleAssignment.is_active == True
            )
        )
    )
    assignments = result.all()
    
    return [
        {
            "assignment_id": str(assignment.id),
            "role_id": str(role.id),
            "role_name": role.role_name,
            "role_code": role.role_code,
            "is_system_role": role.is_system_role,
            "assigned_at": assignment.assigned_at.isoformat(),
            "assigned_by": str(assignment.assigned_by) if assignment.assigned_by else None
        }
        for assignment, role in assignments
    ]


@router.get("/roles/{role_id}/users", response_model=List[dict])
async def get_role_users(
    role_id: int,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all users assigned to a role (admin only)"""
    # Verify role belongs to same society
    role_result = await db.execute(
        select(CustomRole).where(
            and_(
                CustomRole.id == role_id,
                CustomRole.society_id == current_user.society_id
            )
        )
    )
    role = role_result.scalar_one_or_none()
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    # Get active role assignments
    result = await db.execute(
        select(UserRoleAssignment, User)
        .join(User, UserRoleAssignment.user_id == User.id)
        .where(
            and_(
                UserRoleAssignment.role_id == role_id,
                UserRoleAssignment.is_active == True
            )
        )
    )
    assignments = result.all()
    
    return [
        {
            "assignment_id": str(assignment.id),
            "user_id": str(user.id),
            "user_name": user.name,
            "user_email": user.email,
            "apartment_number": user.apartment_number,
            "assigned_at": assignment.assigned_at.isoformat(),
            "assigned_by": str(assignment.assigned_by) if assignment.assigned_by else None
        }
        for assignment, user in assignments
    ]

