"""Society registration routes"""
from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.society import SocietyCreate, SocietyResponse, SocietyUpdate
from app.models.user import UserResponse, Token
from app.models_db import Society, User, UserRole
from app.utils.security import get_password_hash, create_access_token
from app.database import get_db
from app.dependencies import get_current_user, get_current_admin_user

router = APIRouter()


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register_society(
    society_data: SocietyCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Self-service society registration
    
    Creates a new society and the first Super Admin user.
    This is the entry point for new societies joining the platform.
    
    Flow:
    1. User fills form with admin and society details
    2. OTP verification should be done on frontend (Clerk)
    3. Backend creates society and super admin
    4. Returns token for immediate login
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Check if email already exists
    result = await db.execute(select(User).where(User.email == society_data.admin_email))
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if society name already exists (optional - can allow duplicates)
    result = await db.execute(select(Society).where(Society.name == society_data.society_name))
    existing_society = result.scalar_one_or_none()
    
    if existing_society:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Society with this name already exists"
        )
    
    try:
        # Create new society
        from app.models_db import AccountingType
        accounting_type_enum = AccountingType.CASH if society_data.accounting_type == "cash" else AccountingType.ACCRUAL
        
        new_society = Society(
            name=society_data.society_name,
            address=society_data.society_address,
            registration_no=society_data.registration_no,
            pan_no=society_data.pan_no,
            reg_cert_url=society_data.reg_cert_url,
            pan_card_url=society_data.pan_card_url,
            logo_url=society_data.logo_url,
            financial_year_start=society_data.financial_year_start,
            financial_year_end=society_data.financial_year_end,
            accounting_type=accounting_type_enum,
            total_flats=0,  # Start with 0 flats
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(new_society)
        await db.flush()  # Flush to get the society ID
        
        logger.info(f"Created new society: {new_society.name} (ID: {new_society.id})")
        
        # Create Super Admin user
        password_hash = get_password_hash(society_data.admin_password)
        
        new_user = User(
            society_id=new_society.id,
            email=society_data.admin_email,
            password_hash=password_hash,
            name=society_data.admin_name,
            apartment_number="ADMIN",  # Placeholder for super admin
            phone_number=society_data.admin_phone,
            role=UserRole.SUPER_ADMIN,  # Set as Super Admin
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(new_user)
        await db.flush()  # Flush to get the user ID
        
        logger.info(f"Created Super Admin: {new_user.name} (ID: {new_user.id}) for society {new_society.id}")
        
        # Commit both transactions
        await db.commit()
        
        # Refresh to get latest data
        await db.refresh(new_society)
        await db.refresh(new_user)
        
        # Create access token
        access_token = create_access_token(data={"sub": str(new_user.id), "email": new_user.email})
        
        # Build user response
        # Handle role enum conversion
        user_role = new_user.role.value if hasattr(new_user.role, 'value') else str(new_user.role)
        
        user_response = UserResponse(
            id=str(new_user.id),
            email=new_user.email,
            name=new_user.name,
            apartment_number=new_user.apartment_number,
            role=user_role,
            phone_number=new_user.phone_number,
            society_id=new_user.society_id,
            created_at=new_user.created_at,
            updated_at=new_user.updated_at
        )
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            user=user_response
        )
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating society: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create society: {str(e)}"
        )


@router.get("/{society_id}", response_model=SocietyResponse)
async def get_society(
    society_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get society details (only for users of that society)"""
    try:
        society_id_int = int(society_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid society ID"
        )
    
    # Verify user belongs to this society
    if current_user.society_id != society_id_int:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this society"
        )
    
    result = await db.execute(select(Society).where(Society.id == society_id_int))
    society = result.scalar_one_or_none()
    
    if not society:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Society not found"
        )
    
    return SocietyResponse(
        id=str(society.id),
        name=society.name,
        address=society.address,
        registration_no=society.registration_no,
        pan_no=society.pan_no,
        reg_cert_url=society.reg_cert_url,
        pan_card_url=society.pan_card_url,
        logo_url=society.logo_url,
        total_flats=society.total_flats,
        financial_year_start=society.financial_year_start,
        financial_year_end=society.financial_year_end,
        accounting_type=society.accounting_type.value if hasattr(society.accounting_type, 'value') else str(society.accounting_type),
        address_line=society.address_line,
        pin_code=society.pin_code,
        city=society.city,
        state=society.state,
        email=society.email,
        landline=society.landline,
        mobile=society.mobile,
        gst_registration_applicable=society.gst_registration_applicable if society.gst_registration_applicable is not None else False,
        created_at=society.created_at,
        updated_at=society.updated_at
    )


@router.patch("/settings", response_model=SocietyResponse)
async def update_society_settings(
    settings_data: SocietyUpdate,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Update society financial year and accounting type settings (admin only)"""
    result = await db.execute(select(Society).where(Society.id == current_user.society_id))
    society = result.scalar_one_or_none()
    
    if not society:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Society not found"
        )
    
    # Update fields if provided
    if settings_data.financial_year_start is not None:
        society.financial_year_start = settings_data.financial_year_start
    if settings_data.financial_year_end is not None:
        society.financial_year_end = settings_data.financial_year_end
    if settings_data.accounting_type is not None:
        from app.models_db import AccountingType
        society.accounting_type = AccountingType.CASH if settings_data.accounting_type == "cash" else AccountingType.ACCRUAL
    if settings_data.logo_url is not None:
        society.logo_url = settings_data.logo_url
    if settings_data.address_line is not None:
        society.address_line = settings_data.address_line
    if settings_data.pin_code is not None:
        society.pin_code = settings_data.pin_code
    if settings_data.city is not None:
        society.city = settings_data.city
    if settings_data.state is not None:
        society.state = settings_data.state
    if settings_data.email is not None:
        society.email = settings_data.email
    if settings_data.landline is not None:
        society.landline = settings_data.landline
    if settings_data.mobile is not None:
        society.mobile = settings_data.mobile
    if settings_data.gst_registration_applicable is not None:
        society.gst_registration_applicable = settings_data.gst_registration_applicable
    
    society.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(society)
    
    return SocietyResponse(
        id=str(society.id),
        name=society.name,
        address=society.address,
        registration_no=society.registration_no,
        pan_no=society.pan_no,
        reg_cert_url=society.reg_cert_url,
        pan_card_url=society.pan_card_url,
        logo_url=society.logo_url,
        total_flats=society.total_flats,
        financial_year_start=society.financial_year_start,
        financial_year_end=society.financial_year_end,
        accounting_type=society.accounting_type.value if hasattr(society.accounting_type, 'value') else str(society.accounting_type),
        address_line=society.address_line,
        pin_code=society.pin_code,
        city=society.city,
        state=society.state,
        email=society.email,
        landline=society.landline,
        mobile=society.mobile,
        gst_registration_applicable=society.gst_registration_applicable if society.gst_registration_applicable is not None else False,
        created_at=society.created_at,
        updated_at=society.updated_at
    )

