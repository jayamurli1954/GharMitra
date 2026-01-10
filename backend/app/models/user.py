"""
Pydantic models for User-related requests and responses
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    ACCOUNTANT = "accountant"
    RESIDENT = "resident"


class UserBase(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=100)
    apartment_number: str = Field(..., min_length=1, max_length=20)
    role: UserRole = UserRole.RESIDENT
    phone_number: Optional[str] = Field(None, max_length=20)


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=100)
    # Legal consent fields (DPDP Act 2023 compliance)
    terms_accepted: bool = Field(False, description="User must accept Terms of Service")
    privacy_accepted: bool = Field(False, description="User must accept Privacy Policy")
    consent_version: Optional[str] = Field(None, description="Version of terms/privacy accepted")


class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    apartment_number: Optional[str] = Field(None, min_length=1, max_length=20)
    phone_number: Optional[str] = Field(None, max_length=20)
    role: Optional[UserRole] = None


class UserResponse(UserBase):
    id: str  # Changed from alias="_id" to match database model
    society_id: int = Field(default=1, description="Society ID for multi-tenancy")
    society_name: Optional[str] = None  # Added for UI display
    terms_accepted: bool = Field(default=False)
    privacy_accepted: bool = Field(default=False)
    consent_timestamp: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        use_enum_values = True

class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[EmailStr] = None
    current_password: Optional[str] = None
    new_password: Optional[str] = None

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "_id": "507f1f77bcf86cd799439011",
                "email": "john.doe@example.com",
                "name": "John Doe",
                "apartment_number": "101",
                "role": "member",
                "phone_number": "+91-9876543210",
                "created_at": "2024-01-15T10:30:00",
                "updated_at": "2024-01-15T10:30:00"
            }
        }


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenData(BaseModel):
    user_id: Optional[str] = None
    email: Optional[str] = None
