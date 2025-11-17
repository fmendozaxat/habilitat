"""User schemas for request/response validation."""

from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime
from app.core.schemas import BaseSchema, PaginationParams
from app.core.enums import UserRole
from app.core.utils import validate_password_strength


# ============================================================================
# User Create/Update Schemas
# ============================================================================

class UserCreate(BaseModel):
    """Schema for creating a new user."""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    role: UserRole = UserRole.EMPLOYEE
    tenant_id: int

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        is_valid, message = validate_password_strength(v)
        if not is_valid:
            raise ValueError(message)
        return v


class UserUpdate(BaseModel):
    """Schema for updating user profile (by user themselves)."""
    first_name: str | None = Field(None, min_length=1, max_length=100)
    last_name: str | None = Field(None, min_length=1, max_length=100)
    phone: str | None = Field(None, max_length=50)
    job_title: str | None = Field(None, max_length=100)
    department: str | None = Field(None, max_length=100)
    avatar_url: str | None = Field(None, max_length=500)


class UserUpdateByAdmin(UserUpdate):
    """Schema for updating user by admin (more fields)."""
    email: EmailStr | None = None
    role: UserRole | None = None
    is_active: bool | None = None


class ChangePasswordRequest(BaseModel):
    """Schema for changing password."""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)

    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v):
        is_valid, message = validate_password_strength(v)
        if not is_valid:
            raise ValueError(message)
        return v


# ============================================================================
# Invitation Schemas
# ============================================================================

class InviteUserRequest(BaseModel):
    """Schema for inviting a user to the tenant."""
    email: EmailStr
    role: UserRole = UserRole.EMPLOYEE
    first_name: str | None = Field(None, max_length=100)
    last_name: str | None = Field(None, max_length=100)


class AcceptInvitationRequest(BaseModel):
    """Schema for accepting an invitation."""
    token: str
    password: str = Field(..., min_length=8, max_length=100)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        is_valid, message = validate_password_strength(v)
        if not is_valid:
            raise ValueError(message)
        return v


# ============================================================================
# Filter Schemas
# ============================================================================

class UserFilterParams(PaginationParams):
    """Schema for filtering users."""
    search: str | None = None  # Search by name or email
    role: UserRole | None = None
    is_active: bool | None = None
    department: str | None = None


# ============================================================================
# Response Schemas
# ============================================================================

class UserResponse(BaseSchema):
    """Full user response schema."""
    id: int
    email: str
    first_name: str
    last_name: str
    full_name: str
    avatar_url: str | None
    phone: str | None
    job_title: str | None
    department: str | None
    role: str
    is_active: bool
    is_email_verified: bool
    tenant_id: int
    created_at: str
    updated_at: str


class UserListResponse(BaseSchema):
    """Simplified user response for lists."""
    id: int
    email: str
    first_name: str
    last_name: str
    full_name: str
    avatar_url: str | None
    job_title: str | None
    department: str | None
    role: str
    is_active: bool


class UserInvitationResponse(BaseSchema):
    """User invitation response schema."""
    id: int
    email: str
    role: str
    is_accepted: bool
    expires_at: str
    created_at: str
    invited_by: int | None


class AvatarUploadResponse(BaseSchema):
    """Response after uploading avatar."""
    url: str
