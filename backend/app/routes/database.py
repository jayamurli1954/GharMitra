from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks
from typing import List, Optional
import os
import shutil
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, engine, perform_automated_backup, create_engine_instance
from app.models.user import UserResponse
from app.dependencies import get_current_admin_user, get_current_user
from app.config import settings

router = APIRouter()

@router.get("/backups")
async def list_backups(current_user: UserResponse = Depends(get_current_admin_user)):
    """List all available database backups"""
    db_url = settings.DATABASE_URL
    if "sqlite" not in db_url:
        raise HTTPException(status_code=400, detail="Backups only supported for SQLite")
        
    db_path = db_url.split("///")[-1]
    backup_dir = os.path.join(os.path.dirname(db_path), "backups")
    
    if not os.path.exists(backup_dir):
        return []
        
    backups = []
    for f in os.listdir(backup_dir):
        if f.startswith("gharmitra_backup_") and f.endswith(".db"):
            file_path = os.path.join(backup_dir, f)
            stats = os.stat(file_path)
            backups.append({
                "filename": f,
                "size_kb": round(stats.st_size / 1024, 2),
                "created_at": datetime.fromtimestamp(stats.st_mtime).isoformat()
            })
            
    # Sort by created_at desc
    backups.sort(key=lambda x: x["created_at"], reverse=True)
    return backups

@router.post("/backup")
async def create_manual_backup(current_user: UserResponse = Depends(get_current_admin_user)):
    """Manually trigger a backup"""
    try:
        await perform_automated_backup()
        return {"message": "Backup created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backup failed: {str(e)}")

@router.post("/backup-on-logout")
async def backup_on_logout(
    current_user: UserResponse = Depends(get_current_user),
    background_tasks: BackgroundTasks = None
):
    """Trigger a backup during logout. Does not require admin rights."""
    if background_tasks:
        background_tasks.add_task(perform_automated_backup)
    else:
        await perform_automated_backup()
    return {"message": "Backup triggered"}

@router.post("/restore")
async def restore_backup(
    filename: str, 
    current_user: UserResponse = Depends(get_current_admin_user)
):
    """
    Restore the database from a backup file.
    WARNING: This overwrites current data and requires server restart to be effective.
    """
    db_url = settings.DATABASE_URL
    db_path = db_url.split("///")[-1]
    backup_dir = os.path.join(os.path.dirname(db_path), "backups")
    backup_path = os.path.join(backup_dir, filename)
    
    if not os.path.exists(backup_path):
        raise HTTPException(status_code=404, detail="Backup file not found")
        
    try:
        # 1. Create a safety backup of current DB before overwriting
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safety_path = os.path.join(backup_dir, f"pre_restore_safety_{timestamp}.db")
        shutil.copy2(db_path, safety_path)
        
        # 2. Perform the restore (must overwrite while DB might be in use, which is risky)
        # SQLite with WAL can sometimes handle this, but it's better if server restarts.
        shutil.copy2(backup_path, db_path)
        
        return {
            "message": "Restore completed. Please restart the backend server to ensure data consistency.",
            "safety_backup": os.path.basename(safety_path)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Restore failed: {str(e)}")
