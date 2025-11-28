"""
Pydantic schemas for Content module.
"""

from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field
from app.core.schemas import BaseSchema, PaginationParams


# =============================================================================
# Category Schemas
# =============================================================================

class ContentCategoryCreate(BaseModel):
    """Schema for creating a category."""

    name: str = Field(..., min_length=1, max_length=100)
    slug: str | None = None
    description: str | None = Field(None, max_length=500)
    color: str = Field("#6B7280", pattern=r'^#[0-9A-Fa-f]{6}$')


class ContentCategoryUpdate(BaseModel):
    """Schema for updating a category."""

    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = None
    color: str | None = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')


class ContentCategoryResponse(BaseSchema):
    """Response schema for a category."""

    id: int
    name: str
    slug: str
    description: str | None
    color: str
    created_at: datetime


# =============================================================================
# Content Block Schemas
# =============================================================================

class ContentBlockCreate(BaseModel):
    """Schema for creating a content block."""

    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    content_type: str = Field(..., pattern=r'^(text|image|video|pdf|link|embed)$')
    content_text: str | None = None
    content_url: str | None = Field(None, max_length=500)
    content_metadata: dict[str, Any] | None = None
    category_id: int | None = None
    tags: list[str] = Field(default_factory=list)
    is_published: bool = True


class ContentBlockUpdate(BaseModel):
    """Schema for updating a content block."""

    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    content_text: str | None = None
    content_url: str | None = Field(None, max_length=500)
    content_metadata: dict[str, Any] | None = None
    category_id: int | None = None
    tags: list[str] | None = None
    is_published: bool | None = None


class DuplicateBlockRequest(BaseModel):
    """Schema for duplicating a block."""

    new_title: str = Field(..., min_length=1, max_length=200)


class ContentFilterParams(PaginationParams):
    """Filter parameters for listing content."""

    search: str | None = Field(None, description="Search in title and description")
    content_type: str | None = Field(None, description="Filter by content type")
    category_id: int | None = Field(None, description="Filter by category")
    is_published: bool | None = Field(None, description="Filter by publication status")


class ContentBlockResponse(BaseSchema):
    """Full response schema for a content block."""

    id: int
    tenant_id: int
    title: str
    description: str | None
    content_type: str
    content_text: str | None
    content_url: str | None
    content_metadata: dict[str, Any] | None
    category_id: int | None
    category: ContentCategoryResponse | None = None
    tags: list[str]
    is_published: bool
    created_at: datetime
    updated_at: datetime


class ContentBlockListResponse(BaseSchema):
    """Simplified response for content listings."""

    id: int
    title: str
    description: str | None
    content_type: str
    category_id: int | None
    category_name: str | None = None
    tags: list[str]
    is_published: bool
    created_at: datetime


class FileUploadResponse(BaseSchema):
    """Response for file upload."""

    url: str
    content_type: str
    size_bytes: int
    metadata: dict[str, Any]
