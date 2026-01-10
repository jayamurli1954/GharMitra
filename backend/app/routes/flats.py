"""Flats API routes"""
from fastapi import APIRouter, HTTPException, Depends, status
from typing import List
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete, and_, or_

from app.database import get_db
from app.models.flat import FlatCreate, FlatUpdate, FlatResponse
from app.models.user import UserResponse
from app.models_db import Flat, Member
from app.dependencies import get_current_user, get_current_admin_user

router = APIRouter()


# Test endpoint to verify PUT/DELETE are reachable
@router.get("/test", tags=["Debug"])
async def test_endpoint():
    """Test endpoint to verify routing works"""
    return {"status": "ok", "message": "Flats router is working"}


@router.get("/", response_model=List[FlatResponse])
async def list_flats(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all flats (filtered by user's society) with owner info from Member records"""
    # PRD: Multi-tenancy - Filter by society_id
    from ..models_db import Member
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"Fetching flats for user_id={current_user.id}, society_id={current_user.society_id}")
    
    try:
        # Get flats with left join to Member to get owner information
        result = await db.execute(
            select(Flat, Member)
            .outerjoin(
                Member,
                and_(
                    Member.flat_id == Flat.id,
                    Member.society_id == current_user.society_id,
                    Member.status == "active",
                    or_(
                        Member.move_out_date.is_(None),
                        Member.move_out_date > date.today()
                    )
                )
            )
            .where(Flat.society_id == current_user.society_id)
            .order_by(Flat.flat_number)
        )
        flat_member_pairs = result.all()
        logger.info(f"Found {len(flat_member_pairs)} flats for society_id={current_user.society_id}")
    except Exception as e:
        # If query fails, try simpler query without join first
        logger.warning(f"Error fetching flats with join (possibly missing columns): {e}")
        try:
            # Try simple query without join
            result = await db.execute(
                select(Flat)
                .where(Flat.society_id == current_user.society_id)
                .order_by(Flat.flat_number)
            )
            flats = result.scalars().all()
            flat_member_pairs = [(flat, None) for flat in flats]
        except Exception as e2:
            logger.error(f"Error fetching flats even without join: {e2}")
            # Fallback: use raw SQL to get flats
            from sqlalchemy import text
            result = await db.execute(
                text("""
                    SELECT f.id, f.society_id, f.flat_number, f.area_sqft, f.owner_name, f.owner_phone, 
                           f.owner_email, f.occupants, f.occupancy_status, f.created_at, f.updated_at
                    FROM flats f
                    WHERE f.society_id = :society_id 
                    ORDER BY f.flat_number
                """),
                {"society_id": current_user.society_id}
            )
            # Create Flat-like objects from raw results
            class FlatProxy:
                def __init__(self, row):
                    self.id = row[0]
                    self.society_id = row[1]
                    self.flat_number = row[2]
                    self.area_sqft = row[3] or 0.0
                    self.owner_name = row[4]
                    self.owner_phone = row[5]
                    self.owner_email = row[6]
                    self.occupants = row[7] or 1
                    self.occupancy_status = row[8]
                    self.created_at = row[9]
                    self.updated_at = row[10]
                    # Try to get bedrooms if column exists
                    try:
                        if len(row) > 11:
                            self.bedrooms = row[11] if row[11] is not None else 2
                        else:
                            self.bedrooms = 2
                    except (IndexError, AttributeError):
                        self.bedrooms = 2
            
            flats = [FlatProxy(row) for row in result.fetchall()]
            flat_member_pairs = [(flat, None) for flat in flats]

    result_list = []
    for flat, member in flat_member_pairs:
        # Safely get bedrooms - handle case where column doesn't exist yet
        bedrooms_value = 2  # default
        try:
            if hasattr(flat, 'bedrooms'):
                bedrooms_value = flat.bedrooms if flat.bedrooms is not None else 2
        except (AttributeError, KeyError):
            bedrooms_value = 2
        
        # Get owner name from Member if available, otherwise use flat.owner_name
        owner_name = None
        if member and member.name:
            owner_name = member.name
        elif hasattr(flat, 'owner_name'):
            owner_name = flat.owner_name
        
        # Get occupants from Member.total_occupants if available, otherwise use flat.occupants
        occupants_value = 1
        if member and member.total_occupants:
            occupants_value = member.total_occupants
        elif hasattr(flat, 'occupants') and flat.occupants:
            occupants_value = flat.occupants
        
        result_list.append(
            FlatResponse(
                id=str(flat.id),
                flat_number=flat.flat_number,
                area_sqft=flat.area_sqft,
                bedrooms=bedrooms_value,
                occupants=occupants_value,
                owner_name=owner_name,
                owner_phone=flat.owner_phone if hasattr(flat, 'owner_phone') else None,
                owner_email=flat.owner_email if hasattr(flat, 'owner_email') else None,
                created_at=flat.created_at,
                updated_at=flat.updated_at
            )
        )
    return result_list


@router.post("/", response_model=FlatResponse, status_code=status.HTTP_201_CREATED)
async def create_flat(
    flat_data: FlatCreate,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new flat (admin only)"""
    import logging
    logger = logging.getLogger(__name__)
    
    # PRD: Multi-tenancy - Check if flat number already exists in this society
    result = await db.execute(
        select(Flat).where(
            Flat.flat_number == flat_data.flat_number,
            Flat.society_id == current_user.society_id
        )
    )
    existing_flat = result.scalar_one_or_none()

    if existing_flat:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Flat number {flat_data.flat_number} already exists"
        )
    
    # VALIDATION: Check total flat count against blocks_config
    # Get current flat count
    result = await db.execute(
        select(func.count(Flat.id)).where(Flat.society_id == current_user.society_id)
    )
    current_flat_count = result.scalar() or 0
    
    # Get blocks_config from settings
    from app.models_db import SocietySettings
    result = await db.execute(
        select(SocietySettings).where(SocietySettings.society_id == current_user.society_id)
    )
    settings = result.scalar_one_or_none()
    
    if settings and settings.blocks_config:
        # Calculate expected total flats from blocks_config
        expected_total = 0
        for block in settings.blocks_config:
            floors = int(block.get('floors', 0))
            flats_per_floor = int(block.get('flatsPerFloor', 0))
            excluded_numbers = block.get('excludedNumbers', [])
            
            # Calculate flats for this block (excluding excluded numbers)
            block_flats = floors * flats_per_floor - len(excluded_numbers)
            expected_total += block_flats
        
        # Check if adding this flat would exceed the expected total
        if current_flat_count >= expected_total:
            logger.warning(f"Flat creation rejected: Current count ({current_flat_count}) >= Expected total ({expected_total})")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot create flat. Maximum {expected_total} flats allowed based on blocks configuration ({current_flat_count} already exist). Please use 'Sync Flats' to regenerate flats according to your blocks configuration."
            )

    # Create flat with society_id
    new_flat = Flat(
        society_id=current_user.society_id,  # PRD: Multi-tenancy
        flat_number=flat_data.flat_number,
        area_sqft=flat_data.area_sqft,
        bedrooms=flat_data.bedrooms if hasattr(flat_data, 'bedrooms') else 2,
        occupants=flat_data.occupants,
        owner_name=flat_data.owner_name,
        owner_phone=flat_data.owner_phone,
        owner_email=flat_data.owner_email,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    db.add(new_flat)
    await db.commit()
    await db.refresh(new_flat)

    return FlatResponse(
        id=str(new_flat.id),
        flat_number=new_flat.flat_number,
        area_sqft=new_flat.area_sqft,
        bedrooms=new_flat.bedrooms if hasattr(new_flat, 'bedrooms') else 2,
        occupants=new_flat.occupants,
        owner_name=new_flat.owner_name,
        owner_phone=new_flat.owner_phone,
        owner_email=new_flat.owner_email,
        created_at=new_flat.created_at,
        updated_at=new_flat.updated_at
    )


@router.get("/{flat_id}", response_model=FlatResponse)
async def get_flat(
    flat_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific flat by ID (must belong to user's society)"""
    try:
        flat_id_int = int(flat_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid flat ID"
        )

    # PRD: Multi-tenancy - Filter by society_id for security
    result = await db.execute(
        select(Flat).where(
            Flat.id == flat_id_int,
            Flat.society_id == current_user.society_id
        )
    )
    flat = result.scalar_one_or_none()

    if not flat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Flat not found"
        )

    return FlatResponse(
        id=str(flat.id),
        flat_number=flat.flat_number,
        area_sqft=flat.area_sqft,
        bedrooms=flat.bedrooms if hasattr(flat, 'bedrooms') else 2,
        occupants=flat.occupants,
        owner_name=flat.owner_name,
        owner_phone=flat.owner_phone,
        owner_email=flat.owner_email,
        created_at=flat.created_at,
        updated_at=flat.updated_at
    )


@router.put("/{flat_id}", response_model=FlatResponse)
async def update_flat(
    flat_id: str,
    flat_data: FlatUpdate,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a flat (admin only)"""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"Update flat request - ID: {flat_id}, Type: {type(flat_id)}, User: {current_user.email}, Role: {current_user.role}")
    
    try:
        flat_id_int = int(flat_id)
        logger.info(f"Converted flat_id to int: {flat_id_int}")
    except ValueError as e:
        logger.error(f"Invalid flat ID format: {flat_id}, Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid flat ID: '{flat_id}'. Expected a number."
        )

    # PRD: Multi-tenancy - Get flat and verify it belongs to user's society
    result = await db.execute(
        select(Flat).where(
            Flat.id == flat_id_int,
            Flat.society_id == current_user.society_id
        )
    )
    flat = result.scalar_one_or_none()

    if not flat:
        logger.warning(f"Flat not found with ID: {flat_id_int} in society {current_user.society_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Flat with ID {flat_id_int} not found"
        )
    
    logger.info(f"Found flat: {flat.flat_number} (ID: {flat.id})")

    # Update fields that were provided
    update_data = flat_data.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )

    # CRITICAL: If flat_number is being changed, check if new flat_number already exists
    if 'flat_number' in update_data and update_data['flat_number'] != flat.flat_number:
        new_flat_number = update_data['flat_number']
        logger.info(f"Flat number change requested: {flat.flat_number} -> {new_flat_number}")
        
        # Check if new flat_number already exists (excluding current flat)
        result = await db.execute(
            select(Flat).where(
                Flat.flat_number == new_flat_number,
                Flat.society_id == current_user.society_id,
                Flat.id != flat_id_int  # Exclude current flat
            )
        )
        existing_flat = result.scalar_one_or_none()
        
        if existing_flat:
            logger.warning(f"Flat number {new_flat_number} already exists (ID: {existing_flat.id})")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Flat number '{new_flat_number}' already exists. Cannot update flat number."
            )
        
        logger.info(f"Flat number change validated: {flat.flat_number} -> {new_flat_number}")

    for field, value in update_data.items():
        setattr(flat, field, value)

    flat.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(flat)

    return FlatResponse(
        id=str(flat.id),
        flat_number=flat.flat_number,
        area_sqft=flat.area_sqft,
        bedrooms=flat.bedrooms if hasattr(flat, 'bedrooms') else 2,
        occupants=flat.occupants,
        owner_name=flat.owner_name,
        owner_phone=flat.owner_phone,
        owner_email=flat.owner_email,
        created_at=flat.created_at,
        updated_at=flat.updated_at
    )


@router.delete("/{flat_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_flat(
    flat_id: str,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a flat (admin only)"""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"Delete flat request - ID: {flat_id}, Type: {type(flat_id)}, User: {current_user.email}, Role: {current_user.role}")
    
    try:
        flat_id_int = int(flat_id)
        logger.info(f"Converted flat_id to int: {flat_id_int}")
    except ValueError as e:
        logger.error(f"Invalid flat ID format: {flat_id}, Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid flat ID: '{flat_id}'. Expected a number."
        )

    # PRD: Multi-tenancy - Get flat first to check for members
    result = await db.execute(
        select(Flat).where(
            and_(
                Flat.id == flat_id_int,
                Flat.society_id == current_user.society_id
            )
        )
    )
    flat = result.scalar_one_or_none()
    
    if not flat:
        logger.warning(f"Flat not found with ID: {flat_id_int} in society {current_user.society_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Flat with ID {flat_id_int} not found"
        )
    
    # SAFEGUARD: Check if flat has active members before deletion
    from sqlalchemy import func, or_
    from datetime import date
    result = await db.execute(
        select(func.count(Member.id)).where(
            and_(
                Member.flat_id == flat_id_int,
                Member.society_id == current_user.society_id,
                Member.status == "active",
                or_(
                    Member.move_out_date.is_(None),
                    Member.move_out_date > date.today()
                )
            )
        )
    )
    active_members_count = result.scalar() or 0
    
    if active_members_count > 0:
        logger.warning(f"Cannot delete flat {flat.flat_number} (ID: {flat_id_int}) - has {active_members_count} active members")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete flat '{flat.flat_number}' because it has {active_members_count} active member(s). Please move out or delete members first."
        )
    
    # Delete the flat
    result = await db.execute(
        delete(Flat).where(
            and_(
                Flat.id == flat_id_int,
                Flat.society_id == current_user.society_id
            )
        )
    )
    await db.commit()
    
    logger.info(f"Successfully deleted flat with ID: {flat_id_int} (Flat: {flat.flat_number})")

    return None


@router.get("/statistics/summary")
async def get_flats_summary(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get summary statistics for all flats (filtered by user's society)"""
    # PRD: Multi-tenancy - Filter by society_id
    result = await db.execute(
        select(
            func.count(Flat.id).label("total_flats"),
            func.sum(Flat.area_sqft).label("total_area"),
            func.sum(Flat.occupants).label("total_occupants"),
            func.avg(Flat.area_sqft).label("avg_area"),
            func.avg(Flat.occupants).label("avg_occupants")
        ).where(Flat.society_id == current_user.society_id)
    )

    stats = result.one()

    return {
        "total_flats": stats.total_flats or 0,
        "total_area": float(stats.total_area or 0),
        "total_occupants": stats.total_occupants or 0,
        "avg_area": float(stats.avg_area or 0),
        "avg_occupants": float(stats.avg_occupants or 0)
    }

@router.get("/debug", tags=["Debug"])
async def debug_flats(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Debug endpoint to check flats data and society_id"""
    import logging
    logger = logging.getLogger(__name__)
    from sqlalchemy import text
    
    # Get user's society_id
    user_society_id = current_user.society_id
    
    # Count all flats in database (any society_id) - using raw SQL to be sure
    result_all = await db.execute(text("SELECT COUNT(*) FROM flats"))
    total_flats_all = result_all.scalar()
    
    # Count flats for user's society_id
    result_user = await db.execute(
        select(func.count(Flat.id)).where(Flat.society_id == user_society_id)
    )
    total_flats_user = result_user.scalar()
    
    # Get distinct society_ids in flats table with counts
    result_societies = await db.execute(
        text("SELECT society_id, COUNT(*) as count FROM flats GROUP BY society_id")
    )
    society_ids_with_counts = [{"society_id": row[0], "count": row[1]} for row in result_societies.all()]
    
    # Get sample flats for user's society_id
    result_sample = await db.execute(
        select(Flat.flat_number, Flat.society_id)
        .where(Flat.society_id == user_society_id)
        .limit(5)
    )
    sample_flats = [{"flat_number": row[0], "society_id": row[1]} for row in result_sample.all()]
    
    # Get sample flats from ALL society_ids (first 10)
    result_all_sample = await db.execute(
        text("SELECT flat_number, society_id FROM flats LIMIT 10")
    )
    all_sample_flats = [{"flat_number": row[0], "society_id": row[1]} for row in result_all_sample.all()]
    
    # Check user's actual society_id from database
    result_user_db = await db.execute(
        text("SELECT id, email, society_id FROM users WHERE id = :user_id"),
        {"user_id": int(current_user.id)}
    )
    user_db_row = result_user_db.fetchone()
    user_db_society_id = user_db_row[2] if user_db_row else None
    
    return {
        "user_id": current_user.id,
        "user_email": current_user.email,
        "user_society_id_from_token": user_society_id,
        "user_society_id_from_db": user_db_society_id,
        "total_flats_all_societies": total_flats_all,
        "total_flats_for_user_society": total_flats_user,
        "society_ids_in_database": society_ids_with_counts,
        "sample_flats_for_user_society": sample_flats,
        "sample_flats_all_societies": all_sample_flats,
        "message": f"User has society_id={user_society_id}, found {total_flats_user} flats for this society. Total flats in DB: {total_flats_all}"
    }
