"""Complaint Management API Routes"""
from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel

from app.database import get_db
from app.models_db import Complaint, ComplaintStatus, ComplaintType, ComplaintPriority, User, UserRole
from app.dependencies import get_current_user, get_current_active_user

router = APIRouter()

# --- Pydantic Models ---
class ComplaintCreate(BaseModel):
    title: str
    description: str
    type: ComplaintType = ComplaintType.OTHER
    priority: ComplaintPriority = ComplaintPriority.MEDIUM

class ComplaintUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    type: Optional[ComplaintType] = None
    status: Optional[ComplaintStatus] = None
    priority: Optional[ComplaintPriority] = None
    assigned_to: Optional[str] = None
    resolution_notes: Optional[str] = None

class ComplaintResponse(BaseModel):
    id: int
    title: str
    description: str
    type: ComplaintType
    status: ComplaintStatus
    priority: ComplaintPriority
    created_at: datetime
    updated_at: datetime
    assigned_to: Optional[str] = None
    resolution_notes: Optional[str] = None
    user_name: str
    flat_number: Optional[str] = None

    class Config:
        orm_mode = True

# --- Routes ---

@router.post("/", response_model=ComplaintResponse, status_code=status.HTTP_201_CREATED)
async def create_complaint(
    complaint_data: ComplaintCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new complaint (Resident)
    """
    new_complaint = Complaint(
        society_id=current_user.society_id,
        user_id=current_user.id,
        title=complaint_data.title,
        description=complaint_data.description,
        type=complaint_data.type,
        priority=complaint_data.priority,
        status=ComplaintStatus.OPEN
    )
    
    db.add(new_complaint)
    await db.commit()
    await db.refresh(new_complaint)
    
    return map_to_response(new_complaint, current_user)

@router.get("/", response_model=List[ComplaintResponse])
async def list_complaints(
    status: Optional[ComplaintStatus] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List complaints. 
    - Admin/Committee: See all complaints for society.
    - Resident: See only their own complaints.
    """
    query = select(Complaint).where(Complaint.society_id == current_user.society_id)
    
    # Permission Check: Residents only see their own
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.CHAIRMAN, UserRole.SECRETARY]:
        query = query.where(Complaint.user_id == current_user.id)
        
    if status:
        query = query.where(Complaint.status == status)
        
    query = query.order_by(desc(Complaint.created_at))
    
    result = await db.execute(query)
    complaints = result.scalars().all()
    
    # Eager load user for names (optimize in future with join)
    response_list = []
    for c in complaints:
        # Fetch user details for each complaint to show "Opened By"
        # In a real app, use joinedload
        user_result = await db.execute(select(User).where(User.id == c.user_id))
        user = user_result.scalar_one_or_none()
        response_list.append(map_to_response(c, user))
        
    return response_list

@router.patch("/{complaint_id}", response_model=ComplaintResponse)
async def update_complaint(
    complaint_id: int,
    update_data: ComplaintUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update complaint status/details.
    - Admin: Can update any field.
    - Resident: Can only mark 'CLOSED' or 'RESOLVED' if satisfied (or maybe cancel).
    """
    # Get complaint and verify it belongs to the user's society
    result = await db.execute(
        select(Complaint).where(
            Complaint.id == complaint_id,
            Complaint.society_id == current_user.society_id
        )
    )
    complaint = result.scalar_one_or_none()
    
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
        
    # Permission Check
    is_admin = current_user.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.CHAIRMAN, UserRole.SECRETARY]
    is_owner = complaint.user_id == current_user.id
    
    if not (is_admin or is_owner):
         raise HTTPException(status_code=403, detail="Not authorized")

    # Update logic - use model_dump to get only fields that were set
    try:
        # Try Pydantic v2 method first
        update_dict = update_data.model_dump(exclude_unset=True)
    except AttributeError:
        # Fallback for Pydantic v1
        update_dict = update_data.dict(exclude_unset=True)
    
    if is_owner and complaint.status == ComplaintStatus.OPEN:
        # Residents can only edit details if status is OPEN
        if 'title' in update_dict and update_dict['title']:
            complaint.title = update_dict['title']
        if 'description' in update_dict and update_dict['description']:
            complaint.description = update_dict['description']
        if 'type' in update_dict and update_dict['type']:
            complaint.type = update_dict['type']

    # Update status (can be set by both admin and owner)
    if 'status' in update_dict and update_dict['status'] is not None:
        complaint.status = update_dict['status']
        
    if is_admin:
        # Admin overrides - can update any field
        if 'title' in update_dict and update_dict['title']:
            complaint.title = update_dict['title']
        if 'description' in update_dict and update_dict['description']:
            complaint.description = update_dict['description']
        if 'type' in update_dict and update_dict['type'] is not None:
            complaint.type = update_dict['type']
        if 'priority' in update_dict and update_dict['priority'] is not None:
            complaint.priority = update_dict['priority']
        if 'assigned_to' in update_dict:
            complaint.assigned_to = update_dict['assigned_to']
        if 'resolution_notes' in update_dict:
            complaint.resolution_notes = update_dict['resolution_notes']
             
    complaint.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(complaint)
    
    # Fetch owner for response
    user_result = await db.execute(select(User).where(User.id == complaint.user_id))
    user = user_result.scalar_one_or_none()
    
    return map_to_response(complaint, user)

def map_to_response(complaint, user):
    return ComplaintResponse(
        id=complaint.id,
        title=complaint.title,
        description=complaint.description,
        type=complaint.type,
        status=complaint.status,
        priority=complaint.priority,
        created_at=complaint.created_at,
        updated_at=complaint.updated_at,
        assigned_to=complaint.assigned_to,
        resolution_notes=complaint.resolution_notes,
        user_name=user.name if user else "Unknown",
        flat_number=user.apartment_number if user else ""
    )
