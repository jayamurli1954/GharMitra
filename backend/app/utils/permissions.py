"""Permission checking utilities"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from app.models_db import (
    User, CustomRole, RolePermission, Permission, UserRoleAssignment
)


# Define all system permissions
SYSTEM_PERMISSIONS = [
    # Transactions
    {"code": "transactions.view", "name": "View Transactions", "category": "transactions"},
    {"code": "transactions.create", "name": "Create Transactions", "category": "transactions"},
    {"code": "transactions.edit", "name": "Edit Transactions", "category": "transactions"},
    {"code": "transactions.delete", "name": "Delete Transactions", "category": "transactions"},
    {"code": "transactions.approve", "name": "Approve Transactions", "category": "transactions"},
    
    # Billing
    {"code": "billing.view", "name": "View Bills", "category": "billing"},
    {"code": "billing.create", "name": "Create Bills", "category": "billing"},
    {"code": "billing.edit", "name": "Edit Bills", "category": "billing"},
    {"code": "billing.delete", "name": "Delete Bills", "category": "billing"},
    {"code": "billing.approve", "name": "Approve Bills", "category": "billing"},
    
    # Accounting
    {"code": "accounting.view", "name": "View Accounts", "category": "accounting"},
    {"code": "accounting.create", "name": "Create Accounts", "category": "accounting"},
    {"code": "accounting.edit", "name": "Edit Accounts", "category": "accounting"},
    {"code": "accounting.delete", "name": "Delete Accounts", "category": "accounting"},
    
    # Members
    {"code": "members.view", "name": "View Members", "category": "members"},
    {"code": "members.create", "name": "Create Members", "category": "members"},
    {"code": "members.edit", "name": "Edit Members", "category": "members"},
    {"code": "members.delete", "name": "Delete Members", "category": "members"},
    
    # Settings
    {"code": "settings.view", "name": "View Settings", "category": "settings"},
    {"code": "settings.edit", "name": "Edit Settings", "category": "settings"},
    
    # Reports
    {"code": "reports.view", "name": "View Reports", "category": "reports"},
    {"code": "reports.export", "name": "Export Reports", "category": "reports"},
    
    # Audit
    {"code": "audit.view", "name": "View Audit Logs", "category": "audit"},
    
    # All permissions (special permission)
    {"code": "all", "name": "All Permissions", "category": "system"},
]


async def initialize_permissions(db: AsyncSession):
    """Initialize system permissions if they don't exist"""
    for perm_data in SYSTEM_PERMISSIONS:
        result = await db.execute(
            select(Permission).where(Permission.permission_code == perm_data["code"])
        )
        existing = result.scalar_one_or_none()
        
        if not existing:
            from app.models_db import Permission
            new_perm = Permission(**perm_data)
            db.add(new_perm)
    
    await db.commit()


async def get_user_permissions(
    user_id: int,
    db: AsyncSession
) -> List[str]:
    """
    Get all permissions for a user based on their role assignments
    Returns list of permission codes
    """
    # Get user's role assignments
    result = await db.execute(
        select(UserRoleAssignment)
        .where(
            and_(
                UserRoleAssignment.user_id == user_id,
                UserRoleAssignment.is_active == True
            )
        )
    )
    assignments = result.scalars().all()
    
    if not assignments:
        return []
    
    role_ids = [assignment.role_id for assignment in assignments]
    
    # Get permissions for these roles
    result = await db.execute(
        select(RolePermission, Permission)
        .join(Permission, RolePermission.permission_id == Permission.id)
        .where(RolePermission.role_id.in_(role_ids))
    )
    role_permissions = result.all()
    
    permissions = set()
    for role_perm, perm in role_permissions:
        permissions.add(perm.permission_code)
        # If user has "all" permission, return all permissions
        if perm.permission_code == "all":
            return [p["code"] for p in SYSTEM_PERMISSIONS]
    
    return list(permissions)


async def check_permission(
    user_id: int,
    permission_code: str,
    db: AsyncSession,
    require_all: bool = False
) -> bool:
    """
    Check if user has a specific permission
    If require_all=True, checks if user has "all" permission
    
    Note: Admin and Super Admin users have all permissions by default
    """
    # Get user to check their role
    from app.models_db import User, UserRole
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    # Admin and Super Admin have all permissions
    if user and user.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        return True
    
    user_permissions = await get_user_permissions(user_id, db)
    
    if "all" in user_permissions:
        return True
    
    if require_all:
        return False
    
    return permission_code in user_permissions


async def has_any_permission(
    user_id: int,
    permission_codes: List[str],
    db: AsyncSession
) -> bool:
    """Check if user has any of the specified permissions"""
    user_permissions = await get_user_permissions(user_id, db)
    
    if "all" in user_permissions:
        return True
    
    return any(code in user_permissions for code in permission_codes)

