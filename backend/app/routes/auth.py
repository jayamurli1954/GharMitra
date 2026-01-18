"""
Authentication routes
User registration, login, and token management
"""
from fastapi import APIRouter, HTTPException, status, Depends, Request
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import UserCreate, UserLogin, Token, UserResponse, UserProfileUpdate
from app.utils.security import get_password_hash, verify_password, create_access_token
from app.database import get_db
from app.models_db import User, Society
from app.dependencies import get_current_user
from app.config import settings

router = APIRouter()


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, request: Request, db: AsyncSession = Depends(get_db)):
    """
    Register a new user

    - **email**: Valid email address (unique)
    - **password**: Minimum 6 characters
    - **name**: User's full name
    - **apartment_number**: Flat/apartment number
    - **role**: 'admin' or 'member' (default: member)
    - **phone_number**: Optional contact number
    - **terms_accepted**: Must accept Terms of Service (required in SaaS mode)
    - **privacy_accepted**: Must accept Privacy Policy (required in SaaS mode)
    - **consent_version**: Version of legal documents accepted
    """
    # Validate consent (required in SaaS mode, optional in standalone)
    if settings.DEPLOYMENT_MODE == "saas":
        if not user_data.terms_accepted or not user_data.privacy_accepted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You must accept both Terms of Service and Privacy Policy to register"
            )
    
    # Check if user already exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Check if apartment number is already taken
    result = await db.execute(
        select(User).where(User.apartment_number == user_data.apartment_number)
    )
    existing_apartment = result.scalar_one_or_none()

    if existing_apartment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Apartment number already registered"
        )

    # Hash password
    hashed_password = get_password_hash(user_data.password)

    # Get client IP address for consent tracking
    client_ip = request.client.host if request.client else None
    # Handle proxy/load balancer (X-Forwarded-For header)
    if request.headers.get("x-forwarded-for"):
        client_ip = request.headers.get("x-forwarded-for").split(",")[0].strip()

    # Create user
    new_user = User(
        email=user_data.email,
        password_hash=hashed_password,
        name=user_data.name,
        apartment_number=user_data.apartment_number,
        role=user_data.role,
        phone_number=user_data.phone_number,
        # Legal consent fields (DPDP Act 2023 compliance)
        terms_accepted=user_data.terms_accepted,
        privacy_accepted=user_data.privacy_accepted,
        consent_timestamp=datetime.utcnow() if (user_data.terms_accepted and user_data.privacy_accepted) else None,
        consent_ip_address=client_ip,
        consent_version=user_data.consent_version or "1.0",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    # Send email with legal documents (SaaS mode only)
    if settings.DEPLOYMENT_MODE == "saas" and new_user.terms_accepted and new_user.privacy_accepted:
        # TODO: Implement email sending service
        # await send_legal_documents_email(new_user.email, new_user.name)
        pass

    # Create access token
    access_token = create_access_token(data={"sub": str(new_user.id)})

    # Return token and user info
    user_response = UserResponse(
        id=str(new_user.id),
        email=new_user.email,
        name=new_user.name,
        apartment_number=new_user.apartment_number,
        phone_number=new_user.phone_number,
        role=new_user.role,
        society_id=new_user.society_id,
        terms_accepted=new_user.terms_accepted,
        privacy_accepted=new_user.privacy_accepted,
        consent_timestamp=new_user.consent_timestamp,
        created_at=new_user.created_at,
        updated_at=new_user.updated_at
    )

    return Token(
        access_token=access_token,
        user=user_response
    )


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    """
    Login with email and password

    Returns JWT access token and user information
    """
    # Find user by email
    result = await db.execute(select(User).where(User.email == credentials.email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    # Verify password
    if not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    # Create access token
    access_token = create_access_token(data={"sub": str(user.id)})
    
    # Fetch Society Name
    society_result = await db.execute(select(Society).where(Society.id == user.society_id))
    society = society_result.scalar_one_or_none()
    society_name = society.name if society else "GharMitra Society"

    # Prepare user response
    user_response = UserResponse(
        id=str(user.id),
        email=user.email,
        name=user.name,
        apartment_number=user.apartment_number,
        phone_number=user.phone_number,
        role=user.role.value if hasattr(user.role, 'value') else str(user.role),
        society_id=user.society_id,
        society_name=society_name, # Added field
        terms_accepted=user.terms_accepted,
        privacy_accepted=user.privacy_accepted,
        consent_timestamp=user.consent_timestamp,
        created_at=user.created_at,
        updated_at=user.updated_at
    )

    return Token(
        access_token=access_token,
        user=user_response
    )


@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: UserResponse = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """
    Get current user profile
    """
    # Fetch society name
    society_result = await db.execute(select(Society).where(Society.id == current_user.society_id))
    society = society_result.scalar_one_or_none()
    
    # We need to construct a new UserResponse because current_user might be a dict or Pydantic model
    # and we want to ensure society_name is populated.
    # If current_user is already a UserResponse, we can copy it.
    
    user_dict = current_user.dict()
    user_dict['society_name'] = society.name if society else "GharMitra Society"
    
    return user_dict


@router.post("/refresh", response_model=Token)
async def refresh_token(current_user: UserResponse = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """
    Refresh access token
    """
    # Fetch society name again for consistency
    society_result = await db.execute(select(Society).where(Society.id == current_user.society_id))
    society = society_result.scalar_one_or_none()
    current_user_dict = current_user.dict()
    current_user_dict['society_name'] = society.name if society else "GharMitra Society"

    access_token = create_access_token(data={"sub": current_user.id})

    return Token(
        access_token=access_token,
        user=current_user_dict
    )

@router.put("/me", response_model=UserResponse)
async def update_profile(
    update_data: UserProfileUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update current user profile (Name, Phone, Password)
    """
    # Get DB user instance
    result = await db.execute(select(User).where(User.id == int(current_user.id)))
    db_user = result.scalar_one_or_none()
    
    if not db_user:
         raise HTTPException(status_code=404, detail="User not found")

    # Update fields
    if update_data.name:
        db_user.name = update_data.name
    if update_data.phone_number is not None:
        db_user.phone_number = update_data.phone_number
    if update_data.apartment_number:
        db_user.apartment_number = update_data.apartment_number
        
    # Handle Password Change
    if update_data.new_password:
        if not update_data.current_password:
            raise HTTPException(status_code=400, detail="Current password required to set new password")
        if not verify_password(update_data.current_password, db_user.password_hash):
             raise HTTPException(status_code=400, detail="Incorrect current password")
        
        db_user.password_hash = get_password_hash(update_data.new_password)
        
    db_user.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(db_user)
    
    # Fetch society name for response
    society_result = await db.execute(select(Society).where(Society.id == db_user.society_id))
    society = society_result.scalar_one_or_none()
    
    response_data = UserResponse(
        id=str(db_user.id),
        email=db_user.email,
        name=db_user.name,
        apartment_number=db_user.apartment_number,
        phone_number=db_user.phone_number,
        role=db_user.role,
        society_id=db_user.society_id,
        society_name=society.name if society else "GharMitra Society",
        terms_accepted=db_user.terms_accepted,
        privacy_accepted=db_user.privacy_accepted,
        consent_timestamp=db_user.consent_timestamp,
        created_at=db_user.created_at,
        updated_at=db_user.updated_at
    )
    
    return response_data

@router.post("/reset-password")
async def reset_password(
    data: dict,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Reset user password
    """
    current_password = data.get("current_password")
    new_password = data.get("new_password")
    
    if not current_password or not new_password:
        raise HTTPException(status_code=400, detail="Current and new password are required")
        
    # Get DB user instance
    result = await db.execute(select(User).where(User.id == int(current_user.id)))
    db_user = result.scalar_one_or_none()
    
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # Verify current password
    if not verify_password(current_password, db_user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect current password")
        
    # Hash and save new password
    db_user.password_hash = get_password_hash(new_password)
    db_user.updated_at = datetime.utcnow()
    
    await db.commit()
    return {"message": "Password updated successfully"}
