"""
FastAPI dependencies for authentication and authorization
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.utils.security import decode_access_token
from app.models.user import UserResponse, UserRole
from app.models_db import User

# HTTP Bearer token scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """
    Dependency to get the current authenticated user from JWT token

    Args:
        credentials: HTTP Authorization header with Bearer token
        db: Database session

    Returns:
        UserResponse object

    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Decode token
    token = credentials.credentials
    payload = decode_access_token(token)

    if payload is None:
        raise credentials_exception

    user_id_str: str = payload.get("sub")
    if user_id_str is None:
        raise credentials_exception

    # Convert user_id to integer
    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        raise credentials_exception

    # Get user from database using SQLAlchemy
    try:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error fetching user from database: {e}")
        raise credentials_exception

    if user is None:
        raise credentials_exception

    # Convert SQLAlchemy model to Pydantic response
    # Handle role enum conversion
    user_role = user.role.value if hasattr(user.role, 'value') else str(user.role)
    
    # Get society_id - use user's society_id if set, otherwise default to 1
    user_society_id = getattr(user, 'society_id', None)
    if user_society_id is None:
        # If user has no society_id, default to 1 for backward compatibility
        user_society_id = 1
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"User {user.id} ({user.email}) has no society_id, defaulting to 1")
    
    return UserResponse(
        id=str(user.id),
        email=user.email,
        name=user.name,
        apartment_number=user.apartment_number,
        phone_number=user.phone_number,
        role=user_role,
        society_id=user_society_id,  # PRD: Multi-tenancy
        created_at=user.created_at
    )


async def get_current_active_user(
    current_user: UserResponse = Depends(get_current_user)
) -> UserResponse:
    """
    Dependency to ensure user is active
    (Can add is_active field to user model if needed)
    """
    return current_user


async def get_current_admin_user(
    current_user: UserResponse = Depends(get_current_user)
) -> UserResponse:
    """
    Dependency to ensure user has admin or super admin role

    Raises:
        HTTPException: If user is not an admin or super admin
    """
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Admin access required."
        )
    return current_user


async def get_current_super_admin_user(
    current_user: UserResponse = Depends(get_current_user)
) -> UserResponse:
    """
    Dependency to ensure user has super admin role

    Raises:
        HTTPException: If user is not a super admin
    """
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Super Admin access required."
        )
    return current_user


async def get_current_accountant_user(
    current_user: UserResponse = Depends(get_current_user)
) -> UserResponse:
    """
    Dependency to ensure user has accountant, admin, or super admin role

    Raises:
        HTTPException: If user doesn't have required permissions
    """
    if current_user.role not in [UserRole.ACCOUNTANT, UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Accountant, Admin, or Super Admin access required."
        )
    return current_user


# Optional: Get current user without raising exception
async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: AsyncSession = Depends(get_db)
) -> Optional[UserResponse]:
    """
    Get current user if authenticated, None otherwise
    Useful for endpoints that work with or without authentication
    """
    if credentials is None:
        return None

    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None
