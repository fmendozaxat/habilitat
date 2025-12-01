"""
Pydantic schemas for Users module.
Request/Response validation schemas for user operations.
"""

from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator
from app.core.schemas import BaseSchema, PaginationParams
from app.core.enums import UserRole


# =============================================================================
# Request Schemas
# =============================================================================

class UserCreate(BaseModel):
    """Schema for creating a new user."""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    role: UserRole = UserRole.EMPLOYEE
    tenant_id: int | None = None

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError('Debe contener al menos una mayúscula')
        if not any(c.islower() for c in v):
            raise ValueError('Debe contener al menos una minúscula')
        if not any(c.isdigit() for c in v):
            raise ValueError('Debe contener al menos un número')
        return v


class UserUpdate(BaseModel):
    """Schema for updating user profile (by user)."""

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
    def validate_password(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError('Debe contener al menos una mayúscula')
        if not any(c.islower() for c in v):
            raise ValueError('Debe contener al menos una minúscula')
        if not any(c.isdigit() for c in v):
            raise ValueError('Debe contener al menos un número')
        return v


class InviteUserRequest(BaseModel):
    """Schema for inviting a user to tenant."""

    email: EmailStr
    role: UserRole = UserRole.EMPLOYEE
    first_name: str | None = Field(None, max_length=100)
    last_name: str | None = Field(None, max_length=100)


class AcceptInvitationRequest(BaseModel):
    """Schema for accepting an invitation."""

    token: str
    password: str = Field(..., min_length=8)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError('Debe contener al menos una mayúscula')
        if not any(c.islower() for c in v):
            raise ValueError('Debe contener al menos una minúscula')
        if not any(c.isdigit() for c in v):
            raise ValueError('Debe contener al menos un número')
        return v


class ResendInvitationRequest(BaseModel):
    """Schema for resending an invitation."""

    invitation_id: int


class UserFilterParams(PaginationParams):
    """Filter parameters for listing users."""

    search: str | None = Field(None, description="Search by name or email")
    role: UserRole | None = Field(None, description="Filter by role")
    is_active: bool | None = Field(None, description="Filter by active status")
    department: str | None = Field(None, description="Filter by department")


# =============================================================================
# Response Schemas
# =============================================================================

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
    tenant_id: int | None
    created_at: datetime
    updated_at: datetime


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
    created_at: datetime


class UserInvitationResponse(BaseSchema):
    """User invitation response schema."""

    id: int
    email: str
    role: str
    is_accepted: bool
    expires_at: datetime
    created_at: datetime
    invited_by: int | None
    is_expired: bool


class AvatarUploadResponse(BaseSchema):
    """Avatar upload response."""

    url: str
