"""
Member Onboarding API routes - Admin creates profiles, users claim them

LEGAL COMPLIANCE: We DO NOT collect or store:
- Aadhaar documents or Aadhaar numbers
- PAN card documents or PAN numbers
- Sale Deed documents
- Rental Agreement documents

We ONLY collect for PRIMARY MEMBER:
- name: Member's full name
- phone_number: Mobile number (unique identifier for login)
- email: Email address
- member_type: Owner or Tenant status
- move_in_date: Date when member moved in
- total_occupants: Number of occupants declared
"""
from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, date
from typing import List, Optional
import csv
import io

from app.database import get_db
from app.models.user import UserResponse
from app.models_db import Member, Flat, User, Society
from app.dependencies import get_current_admin_user, get_current_user
from app.utils.audit import log_action
from pydantic import BaseModel, Field, EmailStr

router = APIRouter()


# ============ PYDANTIC MODELS ============
class MemberCreate(BaseModel):
    """
    Model for creating a single member (admin)
    """
    flat_number: str = Field(..., description="Flat number (e.g., '101', 'A-201')")
    name: str = Field(..., min_length=1, max_length=100, description="Primary member name only")
    phone_number: str = Field(..., min_length=10, max_length=20, description="Mobile number - unique identifier for login")
    email: EmailStr = Field(..., description="Primary member email only")
    member_type: str = Field(..., description="'owner' or 'tenant' - member status")
    occupation: Optional[str] = Field(None, description="Occupation: Employed, Business, Professional, etc.")
    is_mobile_public: bool = Field(False, description="Is mobile number visible to other members?")
    move_in_date: date = Field(..., description="Date when member moved in")
    total_occupants: int = Field(1, ge=1, description="Total number of occupants declared")
    is_primary: bool = Field(True, description="Is this the primary member?")


class MemberBulkImport(BaseModel):
    """Model for bulk import response"""
    total_rows: int
    successful: int
    failed: int
    errors: List[str]
    warnings: Optional[List[str]] = Field(default_factory=list, description="Warnings for successful imports")
    summary: Optional[str] = Field(None, description="Summary message")


class MemberResponse(BaseModel):
    """Model for member response"""
    id: str
    flat_id: str
    flat_number: str
    name: str
    phone_number: Optional[str] # Optional because it can be masked
    email: Optional[str] # Optional for privacy
    member_type: str
    occupation: Optional[str] = None
    status: str
    is_mobile_public: bool
    move_in_date: date
    move_out_date: Optional[date] = None
    total_occupants: int
    is_primary: bool
    clerk_user_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ClaimProfileRequest(BaseModel):
    """Model for claiming a profile (after OTP verification)"""
    phone_number: str = Field(..., description="Mobile number used for OTP")
    clerk_user_id: str = Field(..., description="Clerk user ID after OTP verification")


class MemberUpdate(BaseModel):
    """Model for updating member details (admin only)"""
    flat_number: Optional[str] = Field(None, description="Flat number (e.g., '101', 'A-201') - for reassigning member to different flat")
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone_number: Optional[str] = Field(None, min_length=10, max_length=20)
    email: Optional[EmailStr] = None
    occupation: Optional[str] = None
    is_mobile_public: Optional[bool] = None
    total_occupants: Optional[int] = Field(None, ge=1)
    status: Optional[str] = Field(None, description="active, inactive, moved_out")
    move_out_date: Optional[date] = Field(None, description="Date when member moved out")


# ============ ADMIN ENDPOINTS ============
@router.post("/", response_model=MemberResponse, status_code=status.HTTP_201_CREATED)
async def create_member(
    member_data: MemberCreate,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a single member profile (admin only)
    """
    # Find flat by flat_number
    result = await db.execute(
        select(Flat).where(
            and_(
                Flat.flat_number == member_data.flat_number,
                Flat.society_id == current_user.society_id
            )
        )
    )
    flat = result.scalar_one_or_none()
    
    if not flat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Flat '{member_data.flat_number}' not found in your society"
        )
    
    # Check if phone number already exists in this society
    result = await db.execute(
        select(Member).where(
            and_(
                Member.phone_number == member_data.phone_number,
                Member.society_id == current_user.society_id
            )
        )
    )
    existing_member = result.scalar_one_or_none()
    
    if existing_member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Member with phone number '{member_data.phone_number}' already exists"
        )
    
    # ============ FLAT OCCUPANCY VALIDATION ============
    # Check if flat is already occupied by an active member
    result = await db.execute(
        select(Member).where(
            and_(
                Member.flat_id == flat.id,
                Member.society_id == current_user.society_id,
                Member.status == "active",  # Only check active members
                or_(
                    Member.move_out_date.is_(None),  # No move-out date (still occupying)
                    Member.move_out_date > datetime.utcnow().date()  # Move-out date is in the future
                )
            )
        )
    )
    existing_active_member = result.scalar_one_or_none()
    
    if existing_active_member:
        # Business Rule 1: Only one owner per flat at a time
        if member_data.member_type == "owner":
            if existing_active_member.member_type.value == "owner":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Flat {member_data.flat_number} is already occupied by owner '{existing_active_member.name}'. "
                           f"A new owner can only be assigned after the current owner completes the move-out/NOC process. "
                           f"Please mark the current owner as 'moved_out' first."
                )
            else:
                # Existing tenant, trying to add owner - this is allowed only if tenant moves out first
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Flat {member_data.flat_number} is currently occupied by tenant '{existing_active_member.name}'. "
                           f"An owner can only be assigned after the tenant completes the move-out/NOC process."
                )
        
        # Business Rule 2: Can only add tenant if flat is vacant (no active owner or tenant)
        if member_data.member_type == "tenant":
            if existing_active_member.member_type.value == "owner":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Flat {member_data.flat_number} is owned by '{existing_active_member.name}'. "
                           f"A tenant can only be added if the flat is vacant. "
                           f"If the owner wants to rent it out, the flat must be vacant (owner must move out or mark as available for rent)."
                )
            else:
                # Existing tenant, trying to add another tenant
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Flat {member_data.flat_number} is already occupied by tenant '{existing_active_member.name}'. "
                           f"A new tenant can only be assigned after the current tenant completes the move-out/NOC process."
                )
    
    # Create member
    new_member = Member(
        society_id=current_user.society_id,
        flat_id=flat.id,
        name=member_data.name,
        phone_number=member_data.phone_number,
        email=member_data.email,
        member_type=member_data.member_type,
        occupation=member_data.occupation,
        is_mobile_public=member_data.is_mobile_public,
        is_primary=member_data.is_primary,
        move_in_date=member_data.move_in_date,
        total_occupants=member_data.total_occupants,
        status="active",  # New members should be active by default
        clerk_user_id=None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    # Sync flat occupants
    if member_data.total_occupants:
        flat.occupants = member_data.total_occupants

    db.add(new_member)
    await db.flush() 

    # Initialize Document Checklist
    from app.models_db import DocumentChecklist
    new_checklist = DocumentChecklist(
        society_id=current_user.society_id,
        member_id=new_member.id,
        flat_id=flat.id,
        created_at=datetime.utcnow()
    )
    db.add(new_checklist)

    await db.commit()
    await db.refresh(new_member)
    
    # Log action
    await log_action(
        db=db,
        society_id=current_user.society_id,
        user_id=int(current_user.id),
        action_type="create",
        entity_type="member",
        entity_id=new_member.id,
        new_values={
            "name": new_member.name,
            "flat_number": flat.flat_number
        },
    )
    
    return MemberResponse(
        id=str(new_member.id),
        flat_id=str(flat.id),
        flat_number=flat.flat_number,
        name=new_member.name,
        phone_number=new_member.phone_number,
        email=new_member.email,
        member_type=new_member.member_type.value if hasattr(new_member.member_type, 'value') else str(new_member.member_type),
        status=new_member.status,
        occupation=new_member.occupation,
        is_mobile_public=new_member.is_mobile_public,
        move_in_date=new_member.move_in_date,
        move_out_date=new_member.move_out_date,
        total_occupants=new_member.total_occupants,
        is_primary=new_member.is_primary,
        clerk_user_id=new_member.clerk_user_id,
        created_at=new_member.created_at,
        updated_at=new_member.updated_at
    )

@router.patch("/{member_id}", response_model=MemberResponse)
async def update_member(
    member_id: int,
    member_data: MemberUpdate,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Update member details (Admin Only)"""
    result = await db.execute(select(Member).where(Member.id == member_id))
    member = result.scalar_one_or_none()
    
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
        
    if member.society_id != current_user.society_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # CRITICAL: Handle flat_number change if provided (for reassigning member to different flat)
    new_flat_id = None
    if hasattr(member_data, 'flat_number') and member_data.flat_number:
        # Find the new flat by flat_number
        result_new_flat = await db.execute(
            select(Flat).where(
                and_(
                    Flat.flat_number == member_data.flat_number,
                    Flat.society_id == current_user.society_id
                )
            )
        )
        new_flat = result_new_flat.scalar_one_or_none()
        if not new_flat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Flat '{member_data.flat_number}' not found in your society"
            )
        new_flat_id = new_flat.id
        
        # Validate that the new flat is not already occupied by another active member
        existing_active_member_result = await db.execute(
            select(Member).where(
                and_(
                    Member.flat_id == new_flat.id,
                    Member.society_id == current_user.society_id,
                    Member.status == "active",
                    Member.id != member_id,  # Exclude the current member
                    or_(
                        Member.move_out_date.is_(None),
                        Member.move_out_date > datetime.utcnow().date()
                    )
                )
            )
        )
        existing_active_member = existing_active_member_result.scalar_one_or_none()
        
        if existing_active_member:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot reassign member! Flat {member_data.flat_number} is already occupied by {existing_active_member.member_type.value} '{existing_active_member.name}' (ID: {existing_active_member.id}). "
                       f"Please select a different flat number."
            )
    
    # Update fields
    if member_data.name: member.name = member_data.name
    if member_data.phone_number: member.phone_number = member_data.phone_number
    if member_data.email: member.email = member_data.email
    if member_data.occupation: member.occupation = member_data.occupation
    if member_data.occupation: member.occupation = member_data.occupation
    if member_data.total_occupants: 
        member.total_occupants = member_data.total_occupants
        # Sync flat occupants
        result_flat = await db.execute(select(Flat).where(Flat.id == member.flat_id))
        flat = result_flat.scalar_one_or_none()
        if flat:
            flat.occupants = member_data.total_occupants
    
    # Update flat_id if flat_number was changed
    if new_flat_id is not None:
        member.flat_id = new_flat_id
    
    # CRITICAL: If status is being changed to 'active', validate flat occupancy
    if member_data.status and member_data.status == 'active':
        # Check if flat is already occupied by another active member
        result_flat = await db.execute(select(Flat).where(Flat.id == member.flat_id))
        flat = result_flat.scalar_one_or_none()
        if flat:
            existing_active_member_result = await db.execute(
                select(Member).where(
                    and_(
                        Member.flat_id == flat.id,
                        Member.society_id == current_user.society_id,
                        Member.status == "active",
                        Member.id != member_id,  # Exclude the current member
                        or_(
                            Member.move_out_date.is_(None),
                            Member.move_out_date > datetime.utcnow().date()
                        )
                    )
                )
            )
            existing_active_member = existing_active_member_result.scalar_one_or_none()
            
            if existing_active_member:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot activate member! Flat {flat.flat_number} is already occupied by {existing_active_member.member_type.value} '{existing_active_member.name}' (ID: {existing_active_member.id}). "
                           f"Please reassign a different flat number before activating this member."
                )
    
    # If flat_id is being changed (via flat_number in update), validate the new flat
    # Note: We need to check if flat_number is in the update data
    # For now, we'll validate when status changes to active (above)
    # Additional validation for flat_id changes would require checking member_data.flat_id or flat_number
    
    if member_data.status:
        # Check for outstanding dues if marking as inactive
        if member_data.status == 'inactive':
            from app.models_db import MaintenanceBill, BillStatus
            from sqlalchemy import func
            
            # Calculate total outstanding dues for the flat
            # Note: This logic assumes bills are flat-based. 
            # Ideally, we should check if the bills belong to THIS member's tenure.
            # For now, simplistic check: If Flat has ANY unpaid bills, block Clean Exit (inactive).
            # MaintenanceBill doesn't have paid_amount field - if bill is unpaid, full total_amount is outstanding
            outstanding_result = await db.execute(
                select(func.coalesce(func.sum(MaintenanceBill.total_amount), 0))
                .where(
                    and_(
                        MaintenanceBill.flat_id == member.flat_id,
                        MaintenanceBill.status == BillStatus.UNPAID,
                        MaintenanceBill.society_id == current_user.society_id
                    )
                )
            )
            total_outstanding = outstanding_result.scalar() or 0
            
            if total_outstanding > 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, 
                    detail=f"Cannot mark member as 'inactive' due to outstanding dues of ₹{total_outstanding}. Please mark as 'moved_out' (Moved Out with Dues) or clear dues first."
                )
                
        member.status = member_data.status
    if member_data.move_out_date is not None:
        member.move_out_date = member_data.move_out_date
    if member_data.is_mobile_public is not None: member.is_mobile_public = member_data.is_mobile_public
        
    member.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(member)
    
    result_flat = await db.execute(select(Flat).where(Flat.id == member.flat_id))
    flat = result_flat.scalar_one()

    return MemberResponse(
        id=str(member.id),
        flat_id=str(member.flat_id),
        flat_number=flat.flat_number,
        name=member.name,
        phone_number=member.phone_number,
        email=member.email,
        member_type=member.member_type.value if hasattr(member.member_type, 'value') else str(member.member_type),
        occupation=member.occupation,
        is_mobile_public=member.is_mobile_public,
        status=member.status,
        move_in_date=member.move_in_date,
        move_out_date=member.move_out_date,
        total_occupants=member.total_occupants,
        is_primary=member.is_primary,
        clerk_user_id=member.clerk_user_id,
        created_at=member.created_at,
        updated_at=member.updated_at
    )

@router.get("/debug", tags=["Debug"])
async def debug_members(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Debug endpoint to check members data and society_id"""
    import logging
    logger = logging.getLogger(__name__)
    from sqlalchemy import text
    
    # Get user's society_id
    user_society_id = current_user.society_id
    
    # Count all members in database (any society_id) - using raw SQL to be sure
    result_all = await db.execute(text("SELECT COUNT(*) FROM members"))
    total_members_all = result_all.scalar()
    
    # Count members for user's society_id
    result_user = await db.execute(
        select(func.count(Member.id)).where(Member.society_id == user_society_id)
    )
    total_members_user = result_user.scalar()
    
    # Get distinct society_ids in members table with counts
    result_societies = await db.execute(
        text("SELECT society_id, COUNT(*) as count FROM members GROUP BY society_id")
    )
    society_ids_with_counts = [{"society_id": row[0], "count": row[1]} for row in result_societies.all()]
    
    # Get sample members for user's society_id
    result_sample = await db.execute(
        select(Member.name, Member.flat_id, Member.society_id, Flat.flat_number)
        .join(Flat, Member.flat_id == Flat.id)
        .where(Member.society_id == user_society_id)
        .limit(5)
    )
    sample_members = [{"name": row[0], "flat_id": row[1], "society_id": row[2], "flat_number": row[3]} for row in result_sample.all()]
    
    # Get sample members from ALL society_ids (first 10)
    result_all_sample = await db.execute(
        text("SELECT m.name, m.flat_id, m.society_id, f.flat_number FROM members m LEFT JOIN flats f ON m.flat_id = f.id LIMIT 10")
    )
    all_sample_members = [{"name": row[0], "flat_id": row[1], "society_id": row[2], "flat_number": row[3]} for row in result_all_sample.all()]
    
    return {
        "user_id": current_user.id,
        "user_email": current_user.email,
        "user_society_id": user_society_id,
        "total_members_all_societies": total_members_all,
        "total_members_for_user_society": total_members_user,
        "society_ids_in_database": society_ids_with_counts,
        "sample_members_for_user_society": sample_members,
        "sample_members_all_societies": all_sample_members,
        "message": f"User has society_id={user_society_id}, found {total_members_user} members for this society. Total members in DB: {total_members_all}"
    }

@router.get("/", response_model=List[MemberResponse])
async def list_members(
    status_filter: Optional[str] = None,
    flat_number: Optional[str] = None,
    current_user: UserResponse = Depends(get_current_user), # Allow all users
    db: AsyncSession = Depends(get_db)
):
    """
    List all members. 
    Non-admins only see Name, Flat, and Mobile (if is_mobile_public=True).
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Fetching members for user_id={current_user.id}, society_id={current_user.society_id}, status={status_filter}, flat_number={flat_number}")
    
    isAdmin = current_user.role == 'admin'
    
    query = select(Member, Flat).join(Flat, Member.flat_id == Flat.id).where(
        Member.society_id == current_user.society_id
    )
    
    if status_filter:
        query = query.where(Member.status == status_filter)
    
    if flat_number:
        query = query.where(Flat.flat_number == flat_number)
    
    result = await db.execute(query)
    members_data = result.all()
    logger.info(f"Found {len(members_data)} members for society_id={current_user.society_id}")
    
    response = []
    for member, flat in members_data:
        # Privacy Logic
        should_show_phone = isAdmin or member.is_mobile_public or (member.user_id == int(current_user.id) if member.user_id else False)
        should_show_email = isAdmin or (member.user_id == int(current_user.id) if member.user_id else False)
        
        response.append(MemberResponse(
            id=str(member.id),
            flat_id=str(member.flat_id),
            flat_number=flat.flat_number,
            name=member.name,
            phone_number=member.phone_number if should_show_phone else "Private",
            email=member.email if should_show_email else None,
            member_type=member.member_type.value if hasattr(member.member_type, 'value') else str(member.member_type),
            occupation=member.occupation,
            is_mobile_public=member.is_mobile_public,
            status=member.status,
            move_in_date=member.move_in_date,
            move_out_date=member.move_out_date,
            total_occupants=member.total_occupants,
            is_primary=member.is_primary,
            clerk_user_id=member.clerk_user_id,
            created_at=member.created_at,
            updated_at=member.updated_at
        ))
        
    return response


# ============ USER ENDPOINTS ============
@router.post("/claim-profile", response_model=MemberResponse)
async def claim_profile(
    claim_data: ClaimProfileRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Claim a member profile after OTP verification
    This is called after Clerk OTP verification succeeds
    """
    # Find member by phone number
    result = await db.execute(
        select(Member).where(Member.phone_number == claim_data.phone_number)
    )
    member = result.scalar_one_or_none()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="This number is not linked to any flat. Please contact your Society Admin."
        )
    
    # Check if profile already claimed
    if member.status == "active" and member.clerk_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This profile has already been claimed"
        )
    
    # Update member to active and link clerk_user_id
    member.status = "active"
    member.clerk_user_id = claim_data.clerk_user_id
    member.updated_at = datetime.utcnow()
    
    # Also create/update User record if needed
    result = await db.execute(
        select(User).where(User.id == member.user_id) if member.user_id else select(User).where(False)
    )
    user = result.scalar_one_or_none()
    
    if not user and member.user_id:
        # Create user record if member has user_id but user doesn't exist
        # This shouldn't happen, but handle it gracefully
        pass
    
    await db.commit()
    await db.refresh(member)
    
    # Get flat for response
    result = await db.execute(select(Flat).where(Flat.id == member.flat_id))
    flat = result.scalar_one()
    
    # Log action
    await log_action(
        db=db,
        society_id=member.society_id,
        user_id=None,  # User not logged in yet
        action_type="update",
        entity_type="member",
        entity_id=member.id,
        old_values={"status": "inactive", "clerk_user_id": None},
        new_values={"status": "active", "clerk_user_id": claim_data.clerk_user_id},
    )
    
    return MemberResponse(
        id=str(member.id),
        flat_id=str(member.flat_id),
        flat_number=flat.flat_number,
        name=member.name,
        phone_number=member.phone_number,
        email=member.email,
        member_type=member.member_type.value if hasattr(member.member_type, 'value') else str(member.member_type),
        status=member.status,
        move_in_date=member.move_in_date,
        move_out_date=member.move_out_date,
        total_occupants=member.total_occupants,
        is_primary=member.is_primary,
        clerk_user_id=member.clerk_user_id,
        created_at=member.created_at,
        updated_at=member.updated_at
    )


@router.get("/my-profile", response_model=MemberResponse)
async def get_my_profile(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's member profile"""
    # Find member by clerk_user_id or user_id
    result = await db.execute(
        select(Member).where(
            or_(
                Member.user_id == int(current_user.id),
                Member.clerk_user_id == current_user.id  # Assuming current_user.id is clerk_user_id
            )
        )
    )
    member = result.scalar_one_or_none()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member profile not found. Please contact your Society Admin."
        )
    
    # Get flat
    result = await db.execute(select(Flat).where(Flat.id == member.flat_id))
    flat = result.scalar_one()
    
    return MemberResponse(
        id=str(member.id),
        flat_id=str(member.flat_id),
        flat_number=flat.flat_number,
        name=member.name,
        phone_number=member.phone_number,
        email=member.email,
        member_type=member.member_type.value if hasattr(member.member_type, 'value') else str(member.member_type),
        occupation=member.occupation,
        status=member.status,
        move_in_date=member.move_in_date,
        move_out_date=member.move_out_date,
        total_occupants=member.total_occupants,
        is_primary=member.is_primary,
        clerk_user_id=member.clerk_user_id,
        created_at=member.created_at,
        updated_at=member.updated_at
    )


# ============ CHECKLIST ENDPOINTS ============

class ChecklistUpdate(BaseModel):
    aadhaar_status: str
    pan_card_status: str
    sale_deed_status: str
    rental_agreement_status: str
    notes: Optional[str] = None

@router.patch("/{member_id}/checklist")
async def update_checklist(
    member_id: int,
    checklist_data: ChecklistUpdate,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update document checklist status (Physically Submitted / Pending)
    """
    from app.models_db import DocumentChecklist
    
    # Check if checklist exists
    result = await db.execute(select(DocumentChecklist).where(DocumentChecklist.member_id == member_id))
    checklist = result.scalar_one_or_none()
    
    if not checklist:
        # Create if missing (shouldn't happen for new members, but possible for old)
        result_member = await db.execute(select(Member).where(Member.id == member_id))
        member = result_member.scalar_one_or_none()
        if not member:
            raise HTTPException(status_code=404, detail="Member not found")
            
        checklist = DocumentChecklist(
            society_id=current_user.society_id,
            member_id=member_id,
            flat_id=member.flat_id,
            created_at=datetime.utcnow()
        )
        db.add(checklist)
    
    # Update fields
    if checklist.aadhaar_status != checklist_data.aadhaar_status:
        checklist.aadhaar_status = checklist_data.aadhaar_status
        if checklist_data.aadhaar_status == 'submitted':
            checklist.aadhaar_submitted_date = date.today()
            
    if checklist.pan_card_status != checklist_data.pan_card_status:
        checklist.pan_card_status = checklist_data.pan_card_status
        if checklist_data.pan_card_status == 'submitted':
            checklist.pan_card_submitted_date = date.today()

    if checklist.sale_deed_status != checklist_data.sale_deed_status:
        checklist.sale_deed_status = checklist_data.sale_deed_status
        if checklist_data.sale_deed_status == 'submitted':
            checklist.sale_deed_submitted_date = date.today()

    if checklist.rental_agreement_status != checklist_data.rental_agreement_status:
        checklist.rental_agreement_status = checklist_data.rental_agreement_status
        if checklist_data.rental_agreement_status == 'submitted':
            checklist.rental_agreement_submitted_date = date.today()
            
    checklist.notes = checklist_data.notes
    checklist.last_updated_by = int(current_user.id)
    checklist.updated_at = datetime.utcnow()
    
    await db.commit()
    return {"message": "Checklist updated successfully"}

@router.get("/{member_id}/checklist")
async def get_checklist(
    member_id: int,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    from app.models_db import DocumentChecklist
    result = await db.execute(select(DocumentChecklist).where(DocumentChecklist.member_id == member_id))
    checklist = result.scalar_one_or_none()
    
    if not checklist:
        return {
            "aadhaar_status": "pending",
            "pan_card_status": "pending", 
            "sale_deed_status": "pending",
            "rental_agreement_status": "pending",
            "notes": ""
        }
    
    return checklist

