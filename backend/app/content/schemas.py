"""Content schemas for request/response validation."""

from pydantic import BaseModel, Field
from app.core.schemas import BaseSchema, PaginationParams
from app.core.enums import ContentType


# ============================================================================
# ContentCategory Schemas
# ============================================================================

class ContentCategoryCreate(BaseModel):
    """Schema for creating a content category."""
    name: str = Field(..., min_length=1, max_length=100)
    slug: str | None = None  # Auto-generated if not provided
    description: str | None = Field(None, max_length=500)
    color: str = Field("#6B7280", pattern=r'^#[0-9A-Fa-f]{6}$')


class ContentCategoryUpdate(BaseModel):
    """Schema for updating a content category."""
    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = None
    color: str | None = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')


# ============================================================================
# ContentBlock Schemas
# ============================================================================

class ContentBlockCreate(BaseModel):
    """Schema for creating a content block."""
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    content_type: ContentType
    content_text: str | None = None
    content_url: str | None = Field(None, max_length=500)
    content_metadata: dict | None = None
    category_id: int | None = None
    tags: list[str] = []
    is_published: bool = True


class ContentBlockUpdate(BaseModel):
    """Schema for updating a content block."""
    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    content_text: str | None = None
    content_url: str | None = Field(None, max_length=500)
    content_metadata: dict | None = None
    category_id: int | None = None
    tags: list[str] | None = None
    is_published: bool | None = None


class DuplicateContentBlockRequest(BaseModel):
    """Schema for duplicating a content block."""
    new_title: str = Field(..., min_length=1, max_length=200)


# ============================================================================
# Filter Schemas
# ============================================================================

class ContentFilterParams(PaginationParams):
    """Schema for filtering content blocks."""
    search: str | None = None
    content_type: ContentType | None = None
    category_id: int | None = None
    tags: list[str] | None = None
    is_published: bool | None = None


# ============================================================================
# Response Schemas
# ============================================================================

class ContentCategoryResponse(BaseSchema):
    """Response schema for content category."""
    id: int
    tenant_id: int
    name: str
    slug: str
    description: str | None
    color: str
    created_at: str
    updated_at: str


class ContentBlockResponse(BaseSchema):
    """Full response schema for content block."""
    id: int
    tenant_id: int
    title: str
    description: str | None
    content_type: str
    content_text: str | None
    content_url: str | None
    content_metadata: dict | None
    category_id: int | None
    category: ContentCategoryResponse | None
    tags: list[str]
    is_published: bool
    created_at: str
    updated_at: str


class ContentBlockListResponse(BaseSchema):
    """Simplified response schema for content block lists."""
    id: int
    title: str
    content_type: str
    category_id: int | None
    category_name: str | None
    tags: list[str]
    is_published: bool
    created_at: str


class FileUploadResponse(BaseSchema):
    """Response schema for file upload."""
    url: str
    content_type: str
    size_bytes: int
    metadata: dict
