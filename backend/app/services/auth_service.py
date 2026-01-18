"""
Authentication service
Handles user authentication, registration, and user management
"""
from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models_db import User, UserRole, Society
from app.utils.security import get_password_hash as _get_password_hash, verify_password as _verify_password, create_access_token
from app.models.user import UserCreate, UserResponse


class AuthService:
    """Service for handling authentication operations."""

    @staticmethod
    async def create_user(db: AsyncSession, user_data: dict, client_ip: Optional[str] = None) -> User:
        """
        Create a new user.

        Args:
            db: Database session
            user_data: User creation data
            client_ip: Client IP address for consent tracking

        Returns:
            Created user instance

        Raises:
            HTTPException: If user already exists or validation fails
        """
        # Check if user already exists
        result = await db.execute(select(User).where(User.email == user_data["email"]))
        existing_user = result.scalar_one_or_none()

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Check if apartment number is already taken
        result = await db.execute(
            select(User).where(User.apartment_number == user_data["apartment_number"])
        )
        existing_apartment = result.scalar_one_or_none()

        if existing_apartment:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Apartment number already registered"
            )

        # Hash password
        hashed_password = _get_password_hash(user_data["password"])

        # Create user
        new_user = User(
            email=user_data["email"],
            password_hash=hashed_password,
            name=user_data["name"],
            apartment_number=user_data["apartment_number"],
            role=user_data.get("role", UserRole.RESIDENT),
            phone_number=user_data.get("phone_number"),
            # Legal consent fields
            terms_accepted=user_data.get("terms_accepted", False),
            privacy_accepted=user_data.get("privacy_accepted", False),
            consent_timestamp=datetime.utcnow() if (user_data.get("terms_accepted") and user_data.get("privacy_accepted")) else None,
            consent_ip_address=client_ip,
            consent_version=user_data.get("consent_version", "1.0"),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        return new_user

    @staticmethod
    async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[User]:
        """
        Authenticate a user with email and password.

        Args:
            db: Database session
            email: User email
            password: User password

        Returns:
            User instance if authentication successful, None otherwise
        """
        # Find user by email
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if not user:
            return None

        # Verify password
        if not _verify_password(password, user.password_hash):
            return None

        return user

    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """
        Get user by email address.

        Args:
            db: Database session
            email: User email

        Returns:
            User instance if found, None otherwise
        """
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
        """
        Get user by ID.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            User instance if found, None otherwise
        """
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    def get_password_hash(password: str) -> str:
        """
        Hash a password.

        Args:
            password: Plain text password

        Returns:
            Hashed password
        """
        return _get_password_hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.

        Args:
            plain_password: Plain text password
            hashed_password: Hashed password

        Returns:
            True if password matches, False otherwise
        """
        return _verify_password(plain_password, hashed_password)

    @staticmethod
    async def create_access_token_for_user(user: User) -> str:
        """
        Create JWT access token for a user.

        Args:
            user: User instance

        Returns:
            JWT access token
        """
        return create_access_token(data={"sub": str(user.id)})

    @staticmethod
    async def get_user_with_society(db: AsyncSession, user_id: int) -> Optional[dict]:
        """
        Get user with society information.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            User data with society info if found, None otherwise
        """
        result = await db.execute(
            select(User, Society)
            .join(Society, User.society_id == Society.id)
            .where(User.id == user_id)
        )
        row = result.first()

        if not row:
            return None

        user, society = row
        return {
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "apartment_number": user.apartment_number,
            "phone_number": user.phone_number,
            "role": user.role.value if hasattr(user.role, 'value') else str(user.role),
            "society_id": user.society_id,
            "society_name": society.name if society else "GharMitra Society",
            "terms_accepted": user.terms_accepted,
            "privacy_accepted": user.privacy_accepted,
            "consent_timestamp": user.consent_timestamp,
            "created_at": user.created_at,
            "updated_at": user.updated_at
        }


# Create singleton instance
auth_service = AuthService()

# Export methods for backward compatibility
create_user = auth_service.create_user
authenticate_user = auth_service.authenticate_user
get_user_by_email = auth_service.get_user_by_email
get_user_by_id = auth_service.get_user_by_id
get_password_hash = auth_service.get_password_hash
verify_password = auth_service.verify_password
create_access_token_for_user = auth_service.create_access_token_for_user
get_user_with_society = auth_service.get_user_with_society