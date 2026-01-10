"""Permissions and Audit Log API routes"""
from fastapi import APIRouter, HTTPException, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime
from typing import Optional, List

from app.database import get_db
from app.models.user import UserResponse
from app.models_db import Permission, RolePermission, CustomRole, AuditLog, User
from app.dependencies import get_current_admin_user, get_current_user
from app.utils.permissions import SYSTEM_PERMISSIONS, initialize_permissions
from app.utils.audit import get_audit_logs

router = APIRouter()


@router.get("/system", response_model=List[dict])
async def list_system_permissions(
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """List all available system permissions (admin only)"""
    # Ensure permissions are initialized
    await initialize_permissions(db)
    
    result = await db.execute(select(Permission).order_by(Permission.category, Permission.permission_code))
    permissions = result.scalars().all()
    
    return [
        {
            "id": str(perm.id),
            "permission_code": perm.permission_code,
            "permission_name": perm.permission_name,
            "category": perm.category,
            "description": perm.description
        }
        for perm in permissions
    ]


@router.get("/roles/{role_id}", response_model=dict)
async def get_role_permissions(
    role_id: int,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get permissions for a specific role (admin only)"""
    # Verify role belongs to society
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
    
    # Get role permissions
    result = await db.execute(
        select(RolePermission, Permission)
        .join(Permission, RolePermission.permission_id == Permission.id)
        .where(RolePermission.role_id == role_id)
    )
    role_perms = result.all()
    
    permissions = {}
    for role_perm, perm in role_perms:
        permissions[perm.permission_code] = {
            "permission_id": str(perm.id),
            "permission_code": perm.permission_code,
            "permission_name": perm.permission_name,
            "access_level": role_perm.access_level
        }
    
    return {
        "role_id": str(role.id),
        "role_name": role.role_name,
        "permissions": permissions
    }


@router.post("/roles/{role_id}/permissions")
async def update_role_permissions(
    role_id: int,
    permissions_data: dict,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update permissions for a role (admin only)
    permissions_data format: {
        "permission_code": "access_level",  # e.g., "transactions.view": "view", "transactions.create": "create"
        "all": "all"  # Special: grants all permissions
    }
    """
    # Verify role belongs to society
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
    
    # Ensure permissions are initialized
    await initialize_permissions(db)
    
    # Delete existing permissions for this role
    await db.execute(
        select(RolePermission).where(RolePermission.role_id == role_id)
    )
    existing_result = await db.execute(
        select(RolePermission).where(RolePermission.role_id == role_id)
    )
    existing_perms = existing_result.scalars().all()
    for perm in existing_perms:
        await db.delete(perm)
    
    # Add new permissions
    for perm_code, access_level in permissions_data.items():
        # Get permission
        perm_result = await db.execute(
            select(Permission).where(Permission.permission_code == perm_code)
        )
        permission = perm_result.scalar_one_or_none()
        
        if not permission:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Permission '{perm_code}' not found"
            )
        
        # Create role permission
        role_perm = RolePermission(
            role_id=role_id,
            permission_id=permission.id,
            access_level=access_level
        )
        db.add(role_perm)
    
    await db.commit()
    
    # Log action
    await log_action(
        db=db,
        society_id=current_user.society_id,
        user_id=current_user.id,
        action_type="update",
        entity_type="role_permissions",
        entity_id=role_id,
        new_values={"permissions": permissions_data},
    )
    
    return {
        "message": "Permissions updated successfully",
        "role_id": str(role_id),
        "permissions_count": len(permissions_data)
    }


@router.get("/audit-logs", response_model=List[dict])
async def get_audit_logs_endpoint(
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    action_type: Optional[str] = Query(None, description="Filter by action type"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get audit logs (admin only)
    Can filter by user_id, entity_type, action_type, and date range
    """
    # Parse dates
    start_dt = None
    end_dt = None
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid start_date format. Use YYYY-MM-DD or ISO format"
            )
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid end_date format. Use YYYY-MM-DD or ISO format"
            )
    
    logs, users = await get_audit_logs(
        db=db,
        society_id=current_user.society_id,
        user_id=user_id,
        entity_type=entity_type,
        action_type=action_type,
        start_date=start_dt,
        end_date=end_dt,
        limit=limit,
        offset=offset
    )
    
    return [
        {
            "id": str(log.id),
            "user_id": str(log.user_id) if log.user_id else None,
            "user_name": users.get(log.user_id) if log.user_id else "System",
            "action_type": log.action_type,
            "entity_type": log.entity_type,
            "entity_id": str(log.entity_id) if log.entity_id else None,
            "old_values": log.old_values,
            "new_values": log.new_values,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "notes": log.notes,
            "created_at": log.created_at.isoformat()
        }
        for log in logs
    ]


@router.get("/audit-logs/export")
async def export_audit_logs(
    user_id: Optional[int] = Query(None),
    entity_type: Optional[str] = Query(None),
    action_type: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Export audit logs as CSV (admin only)
    """
    from fastapi.responses import StreamingResponse
    import csv
    import io
    
    # Parse dates
    start_dt = None
    end_dt = None
    if start_date:
        start_dt = datetime.fromisoformat(start_date)
    if end_date:
        end_dt = datetime.fromisoformat(end_date)
    
    logs, users = await get_audit_logs(
        db=db,
        society_id=current_user.society_id,
        user_id=user_id,
        entity_type=entity_type,
        action_type=action_type,
        start_date=start_dt,
        end_date=end_dt,
        limit=10000,  # Large limit for export
        offset=0
    )
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        "Date/Time", "User ID", "User Name", "Action", "Entity Type", 
        "Entity ID", "Old Values", "New Values", "IP Address", "Notes"
    ])
    
    # Data rows
    for log in logs:
        writer.writerow([
            log.created_at.isoformat(),
            str(log.user_id) if log.user_id else "",
            users.get(log.user_id, "System") if log.user_id else "System",
            log.action_type,
            log.entity_type,
            str(log.entity_id) if log.entity_id else "",
            str(log.old_values) if log.old_values else "",
            str(log.new_values) if log.new_values else "",
            log.ip_address or "",
            log.notes or ""
        ])
    
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=audit_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        }
    )

