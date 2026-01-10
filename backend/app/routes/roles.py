"""Role Management API routes"""
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime
from typing import List, Optional

from app.database import get_db
from app.models.user import UserResponse
from app.models_db import (
    CustomRole, Permission, RolePermission, UserRoleAssignment, 
    User, Society
)
from app.dependencies import get_current_admin_user
from app.utils.permissions import SYSTEM_PERMISSIONS, initialize_permissions
from app.utils.audit import log_action

router = APIRouter()


# Default system roles with flexible naming
DEFAULT_SYSTEM_ROLES = [
    {
        "role_name": "Chairman/President",
        "role_code": "chairman",
        "description": "Overall governance, strategic oversight, final escalation point for major decisions",
        "is_system_role": True
    },
    {
        "role_name": "Secretary",
        "role_code": "secretary",
        "description": "Records management, communication, administrative support",
        "is_system_role": True
    },
    {
        "role_name": "Treasurer",
        "role_code": "treasurer",
        "description": "Financial management, reporting, budget oversight",
        "is_system_role": True
    },
    {
        "role_name": "Auditor",
        "role_code": "auditor",
        "description": "Independent verification of records, internal control assessment",
        "is_system_role": True
    }
]


@router.post("/initialize", status_code=status.HTTP_201_CREATED)
async def initialize_default_roles(
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Initialize default system roles for the society (admin only)
    Can be called during initial setup
    Assigns default permissions: all permissions to Chairman/President, Secretary, and Treasurer
    """
    # Check if roles already exist
    result = await db.execute(
        select(CustomRole).where(CustomRole.society_id == current_user.society_id)
    )
    existing_roles = result.scalars().all()
    
    if existing_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Roles already initialized for this society"
        )
    
    # Initialize system permissions
    await initialize_permissions(db)
    
    # Get "all" permission
    all_perm_result = await db.execute(
        select(Permission).where(Permission.permission_code == "all")
    )
    all_permission = all_perm_result.scalar_one_or_none()
    
    created_roles = []
    for role_data in DEFAULT_SYSTEM_ROLES:
        new_role = CustomRole(
            society_id=current_user.society_id,
            **role_data
        )
        db.add(new_role)
        created_roles.append(new_role)
    
    await db.commit()
    
    # Refresh to get IDs
    for role in created_roles:
        await db.refresh(role)
    
    # Assign "all" permissions to Chairman/President, Secretary, and Treasurer
    # Auditor gets only view permissions
    if all_permission:
        for role in created_roles:
            if role.role_code in ["chairman", "secretary", "treasurer"]:
                # Assign "all" permission
                role_perm = RolePermission(
                    role_id=role.id,
                    permission_id=all_permission.id,
                    access_level="all"
                )
                db.add(role_perm)
            elif role.role_code == "auditor":
                # Assign only view permissions for auditor
                view_perms_result = await db.execute(
                    select(Permission).where(
                        Permission.permission_code.in_([
                            "transactions.view",
                            "billing.view",
                            "accounting.view",
                            "members.view",
                            "reports.view",
                            "audit.view"
                        ])
                    )
                )
                view_permissions = view_perms_result.scalars().all()
                for perm in view_permissions:
                    role_perm = RolePermission(
                        role_id=role.id,
                        permission_id=perm.id,
                        access_level="view"
                    )
                    db.add(role_perm)
        
        await db.commit()
    
    # Log action
    await log_action(
        db=db,
        society_id=current_user.society_id,
        user_id=int(current_user.id),
        action_type="create",
        entity_type="roles",
        new_values={"roles_initialized": len(created_roles)},
    )
    
    return {
        "message": f"Initialized {len(created_roles)} default roles with permissions",
        "roles_created": len(created_roles),
        "roles": [
            {
                "id": str(role.id),
                "role_name": role.role_name,
                "role_code": role.role_code,
                "description": role.description
            }
            for role in created_roles
        ],
        "permissions_assigned": {
            "chairman": "All permissions (view, create, edit, delete)",
            "secretary": "All permissions (view, create, edit, delete)",
            "treasurer": "All permissions (view, create, edit, delete)",
            "auditor": "View-only permissions (cannot create, edit, or delete)"
        },
        "warning": "IMPORTANT: Only assign Auditor role to external auditor user IDs. Auditors can only view transactions and reports, they cannot modify any records."
    }


@router.get("/", response_model=List[dict])
async def list_roles(
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """List all roles for the society (admin only)"""
    result = await db.execute(
        select(CustomRole)
        .where(CustomRole.society_id == current_user.society_id)
        .order_by(CustomRole.is_system_role.desc(), CustomRole.role_name)
    )
    roles = result.scalars().all()
    
    role_list = []
    for role in roles:
        # Count users with this role
        user_count_result = await db.execute(
            select(UserRoleAssignment)
            .where(
                and_(
                    UserRoleAssignment.role_id == role.id,
                    UserRoleAssignment.is_active == True
                )
            )
        )
        user_count = len(user_count_result.scalars().all())
        
        role_list.append({
            "id": str(role.id),
            "role_name": role.role_name,
            "role_code": role.role_code,
            "description": role.description,
            "is_active": role.is_active,
            "is_system_role": role.is_system_role,
            "user_count": user_count,
            "created_at": role.created_at.isoformat(),
            "updated_at": role.updated_at.isoformat()
        })
    
    return role_list


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_role(
    role_data: dict,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new custom role (admin only)"""
    role_name = role_data.get("role_name")
    role_code = role_data.get("role_code")
    description = role_data.get("description", "")
    
    if not role_name or not role_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="role_name and role_code are required"
        )
    
    # Check if role_code already exists for this society
    existing = await db.execute(
        select(CustomRole).where(
            and_(
                CustomRole.society_id == current_user.society_id,
                CustomRole.role_code == role_code
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role with code '{role_code}' already exists"
        )
    
    new_role = CustomRole(
        society_id=current_user.society_id,
        role_name=role_name,
        role_code=role_code,
        description=description,
        is_system_role=False
    )
    
    db.add(new_role)
    await db.commit()
    await db.refresh(new_role)
    
    return {
        "id": str(new_role.id),
        "role_name": new_role.role_name,
        "role_code": new_role.role_code,
        "description": new_role.description,
        "is_system_role": new_role.is_system_role,
        "created_at": new_role.created_at.isoformat()
    }


@router.patch("/{role_id}")
async def update_role(
    role_id: int,
    role_data: dict,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a role (admin only) - can update name and description, not system roles' codes"""
    result = await db.execute(
        select(CustomRole).where(
            and_(
                CustomRole.id == role_id,
                CustomRole.society_id == current_user.society_id
            )
        )
    )
    role = result.scalar_one_or_none()
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    # Update allowed fields
    if "role_name" in role_data:
        role.role_name = role_data["role_name"]
    if "description" in role_data:
        role.description = role_data["description"]
    
    # Allow updating role_code only for non-system roles
    if "role_code" in role_data and not role.is_system_role:
        # Check if new code already exists
        existing = await db.execute(
            select(CustomRole).where(
                and_(
                    CustomRole.society_id == current_user.society_id,
                    CustomRole.role_code == role_data["role_code"],
                    CustomRole.id != role_id
                )
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Role with code '{role_data['role_code']}' already exists"
            )
        role.role_code = role_data["role_code"]
    
    role.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(role)
    
    return {
        "id": str(role.id),
        "role_name": role.role_name,
        "role_code": role.role_code,
        "description": role.description,
        "is_system_role": role.is_system_role,
        "updated_at": role.updated_at.isoformat()
    }


@router.delete("/{role_id}")
async def delete_role(
    role_id: int,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a custom role (admin only) - cannot delete system roles"""
    result = await db.execute(
        select(CustomRole).where(
            and_(
                CustomRole.id == role_id,
                CustomRole.society_id == current_user.society_id
            )
        )
    )
    role = result.scalar_one_or_none()
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    if role.is_system_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete system roles. You can deactivate them instead."
        )
    
    # Check if role is assigned to any users
    assignments_result = await db.execute(
        select(UserRoleAssignment).where(
            and_(
                UserRoleAssignment.role_id == role_id,
                UserRoleAssignment.is_active == True
            )
        )
    )
    active_assignments = assignments_result.scalars().all()
    
    if active_assignments:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete role. It is assigned to {len(active_assignments)} user(s). Please remove assignments first."
        )
    
    await db.delete(role)
    await db.commit()
    
    return {"message": "Role deleted successfully"}


@router.patch("/{role_id}/toggle")
async def toggle_role_status(
    role_id: int,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Activate or deactivate a role (admin only)"""
    result = await db.execute(
        select(CustomRole).where(
            and_(
                CustomRole.id == role_id,
                CustomRole.society_id == current_user.society_id
            )
        )
    )
    role = result.scalar_one_or_none()
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    role.is_active = not role.is_active
    role.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(role)
    
    return {
        "id": str(role.id),
        "role_name": role.role_name,
        "is_active": role.is_active,
        "updated_at": role.updated_at.isoformat()
    }

