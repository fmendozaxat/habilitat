"""
Pydantic schemas for tenant request/response validation.
Defines all schemas for tenant and branding operations.
"""

from datetime import datetime
from typing import Dict, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict
from app.core.schemas import BaseSchema
from app.core.utils import slugify, is_valid_subdomain


# ============================================================================
# Tenant Schemas
# ============================================================================

class TenantCreate(BaseModel):
    """Schema for creating a new tenant."""

    name: str = Field(
        ...,
        min_length=2,
        max_length=200,
        description="Organization name"
    )
    slug: str | None = Field(
        None,
        description="URL-friendly identifier (auto-generated if not provided)"
    )
    subdomain: str | None = Field(
        None,
        description="Subdomain for tenant access"
    )
    contact_email: str | None = Field(
        None,
        description="Contact email for the organization"
    )
    contact_phone: str | None = Field(
        None,
        description="Contact phone number"
    )

    @field_validator('slug', mode='before')
    @classmethod
    def generate_slug(cls, v, info):
        """Generate slug from name if not provided."""
        if v:
            return slugify(v)
        if info.data and 'name' in info.data:
            return slugify(info.data['name'])
        return None

    @field_validator('subdomain')
    @classmethod
    def validate_subdomain(cls, v):
        """Validate subdomain format."""
        if v and not is_valid_subdomain(v):
            raise ValueError(
                'Subdomain inválido. Solo letras minúsculas, números y guiones, mínimo 3 caracteres.'
            )
        return v


class TenantUpdate(BaseModel):
    """Schema for updating tenant information."""

    name: str | None = Field(None, min_length=2, max_length=200)
    contact_email: str | None = None
    contact_phone: str | None = None
    is_active: bool | None = None
    settings: Dict[str, Any] | None = None


class TenantPlanUpdate(BaseModel):
    """Schema for updating tenant plan and limits (admin only)."""

    plan: str | None = Field(
        None,
        description="Subscription plan: free, starter, business, enterprise"
    )
    max_users: int | None = Field(None, ge=1, description="Maximum number of users")
    max_storage_mb: int | None = Field(None, ge=100, description="Maximum storage in MB")


# ============================================================================
# Branding Schemas
# ============================================================================

class TenantBrandingUpdate(BaseModel):
    """Schema for updating tenant branding."""

    logo_url: str | None = None
    logo_dark_url: str | None = None
    favicon_url: str | None = None
    primary_color: str | None = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    secondary_color: str | None = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    accent_color: str | None = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    background_color: str | None = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    text_color: str | None = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    hero_image_url: str | None = None
    background_image_url: str | None = None
    font_family: str | None = Field(None, max_length=100)


# ============================================================================
# Response Schemas
# ============================================================================

class TenantBrandingResponse(BaseSchema):
    """Response schema for tenant branding."""

    id: int
    tenant_id: int
    logo_url: str | None = None
    logo_dark_url: str | None = None
    favicon_url: str | None = None
    primary_color: str
    secondary_color: str
    accent_color: str | None = None
    background_color: str
    text_color: str
    hero_image_url: str | None = None
    background_image_url: str | None = None
    font_family: str | None = None
    created_at: datetime
    updated_at: datetime


class TenantResponse(BaseSchema):
    """Full tenant response schema."""

    id: int
    name: str
    slug: str
    subdomain: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    is_active: bool
    plan: str
    max_users: int
    max_storage_mb: int
    settings: Dict[str, Any]
    branding: TenantBrandingResponse | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TenantListResponse(BaseSchema):
    """Simplified tenant response for list operations."""

    id: int
    name: str
    slug: str
    subdomain: str | None = None
    is_active: bool
    plan: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TenantThemeResponse(BaseModel):
    """Simplified branding response for frontend theme."""

    logo: str | None = None
    logo_dark: str | None = None
    favicon: str | None = None
    colors: Dict[str, str]
    images: Dict[str, str | None]
    typography: Dict[str, str | None]


class TenantStatsResponse(BaseModel):
    """Response schema for tenant statistics."""

    users_count: int
    max_users: int
    storage_used_mb: float
    max_storage_mb: int
    onboarding_flows_count: int
    is_active: bool
    plan: str


# ============================================================================
# Upload Schemas
# ============================================================================

class LogoUploadResponse(BaseSchema):
    """Response schema for logo upload."""

    url: str = Field(..., description="URL of the uploaded logo")


class ImageUploadResponse(BaseSchema):
    """Response schema for image upload."""

    url: str = Field(..., description="URL of the uploaded image")
    type: str = Field(..., description="Type of image: logo, hero, background, favicon")
