"""Audit logging utilities"""
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models_db import AuditLog, User


async def log_action(
    db: AsyncSession,
    society_id: int,
    user_id: Optional[int],
    action_type: str,  # "create", "update", "delete", "view", "approve"
    entity_type: str,  # "transaction", "bill", "user", "settings", etc.
    entity_id: Optional[int] = None,
    old_values: Optional[Dict[str, Any]] = None,
    new_values: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
):
    """
    Log an action to the audit trail
    """
    audit_log = AuditLog(
        society_id=society_id,
        user_id=user_id,
        action_type=action_type,
        entity_type=entity_type,
        entity_id=entity_id,
        old_values=old_values,
        new_values=new_values,
        ip_address=ip_address,
        user_agent=user_agent,
        created_at=datetime.utcnow()
    )
    
    db.add(audit_log)
    await db.commit()
    await db.refresh(audit_log)
    
    return audit_log


async def get_audit_logs(
    db: AsyncSession,
    society_id: int,
    user_id: Optional[int] = None,
    entity_type: Optional[str] = None,
    action_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 100,
    offset: int = 0
):
    """
    Get audit logs with filters
    """
    query = select(AuditLog).where(AuditLog.society_id == society_id)
    
    if user_id:
        query = query.where(AuditLog.user_id == user_id)
    if entity_type:
        query = query.where(AuditLog.entity_type == entity_type)
    if action_type:
        query = query.where(AuditLog.action_type == action_type)
    if start_date:
        query = query.where(AuditLog.created_at >= start_date)
    if end_date:
        query = query.where(AuditLog.created_at <= end_date)
    
    query = query.order_by(AuditLog.created_at.desc()).limit(limit).offset(offset)
    
    result = await db.execute(query)
    logs = result.scalars().all()
    
    # Get user names for logs
    user_ids = {log.user_id for log in logs if log.user_id}
    users = {}
    if user_ids:
        user_result = await db.execute(
            select(User).where(User.id.in_(user_ids))
        )
        for user in user_result.scalars().all():
            users[user.id] = user.name
    
    return logs, users

