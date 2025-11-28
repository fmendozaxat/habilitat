"""
FastAPI router for Content module.
Provides endpoints for content blocks and categories.
"""

from fastapi import APIRouter, Depends, status, UploadFile, File, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.schemas import SuccessResponse, PaginatedResponse
from app.core.enums import UserRole
from app.core.storage import storage_service
from app.auth.dependencies import get_current_active_user, require_any_role
from app.tenants.dependencies import get_current_tenant
from app.tenants.models import Tenant
from app.users.models import User
from app.content import schemas
from app.content.service import ContentService
from app.content.exceptions import InvalidFileTypeException, FileTooLargeException


router = APIRouter(prefix="/content", tags=["Content"])

ALLOWED_FILE_TYPES = [
    "image/png", "image/jpeg", "image/gif", "image/webp",
    "application/pdf",
    "video/mp4", "video/webm"
]
MAX_FILE_SIZE_MB = 10


# =============================================================================
# Category Endpoints
# =============================================================================

@router.post("/categories", response_model=schemas.ContentCategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    data: schemas.ContentCategoryCreate,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(require_any_role(UserRole.TENANT_ADMIN, UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Create a content category.

    - Requires TENANT_ADMIN or SUPER_ADMIN role
    """
    category = ContentService.create_category(db, tenant.id, data)
    return category


@router.get("/categories", response_model=list[schemas.ContentCategoryResponse])
async def list_categories(
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List all content categories.
    """
    categories = ContentService.list_categories(db, tenant.id)
    return categories


@router.get("/categories/{category_id}", response_model=schemas.ContentCategoryResponse)
async def get_category(
    category_id: int,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get a category by ID.
    """
    category = ContentService.get_category(db, category_id, tenant.id)
    return category


@router.patch("/categories/{category_id}", response_model=schemas.ContentCategoryResponse)
async def update_category(
    category_id: int,
    data: schemas.ContentCategoryUpdate,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(require_any_role(UserRole.TENANT_ADMIN, UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Update a category.

    - Requires TENANT_ADMIN or SUPER_ADMIN role
    """
    category = ContentService.update_category(db, category_id, tenant.id, data)
    return category


@router.delete("/categories/{category_id}", response_model=SuccessResponse)
async def delete_category(
    category_id: int,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(require_any_role(UserRole.TENANT_ADMIN, UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Delete a category.

    - Requires TENANT_ADMIN or SUPER_ADMIN role
    - Cannot delete categories with associated content
    """
    ContentService.delete_category(db, category_id, tenant.id)
    return SuccessResponse(message="Categoría eliminada exitosamente")


# =============================================================================
# Content Block Endpoints
# =============================================================================

@router.post("/blocks", response_model=schemas.ContentBlockResponse, status_code=status.HTTP_201_CREATED)
async def create_content_block(
    data: schemas.ContentBlockCreate,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(require_any_role(UserRole.TENANT_ADMIN, UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Create a content block.

    - Requires TENANT_ADMIN or SUPER_ADMIN role
    """
    block = ContentService.create_content_block(db, tenant.id, data)
    return _build_block_response(block)


@router.get("/blocks", response_model=PaginatedResponse[schemas.ContentBlockListResponse])
async def list_content_blocks(
    filters: schemas.ContentFilterParams = Depends(),
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List content blocks with filters and pagination.
    """
    blocks, total = ContentService.list_content_blocks(db, tenant.id, filters)

    return PaginatedResponse.create(
        data=[_build_block_list_response(b) for b in blocks],
        total=total,
        page=filters.page,
        page_size=filters.page_size
    )


@router.get("/blocks/{block_id}", response_model=schemas.ContentBlockResponse)
async def get_content_block(
    block_id: int,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get a content block by ID.
    """
    block = ContentService.get_content_block(db, block_id, tenant.id)
    return _build_block_response(block)


@router.patch("/blocks/{block_id}", response_model=schemas.ContentBlockResponse)
async def update_content_block(
    block_id: int,
    data: schemas.ContentBlockUpdate,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(require_any_role(UserRole.TENANT_ADMIN, UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Update a content block.

    - Requires TENANT_ADMIN or SUPER_ADMIN role
    """
    block = ContentService.update_content_block(db, block_id, tenant.id, data)
    return _build_block_response(block)


@router.delete("/blocks/{block_id}", response_model=SuccessResponse)
async def delete_content_block(
    block_id: int,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(require_any_role(UserRole.TENANT_ADMIN, UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Delete a content block (soft delete).

    - Requires TENANT_ADMIN or SUPER_ADMIN role
    """
    ContentService.delete_content_block(db, block_id, tenant.id)
    return SuccessResponse(message="Bloque eliminado exitosamente")


@router.post("/blocks/{block_id}/duplicate", response_model=schemas.ContentBlockResponse)
async def duplicate_content_block(
    block_id: int,
    data: schemas.DuplicateBlockRequest,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(require_any_role(UserRole.TENANT_ADMIN, UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Duplicate a content block.

    - Requires TENANT_ADMIN or SUPER_ADMIN role
    """
    block = ContentService.duplicate_content_block(db, block_id, tenant.id, data.new_title)
    return _build_block_response(block)


# =============================================================================
# Search and Upload Endpoints
# =============================================================================

@router.get("/search", response_model=list[schemas.ContentBlockListResponse])
async def search_content(
    q: str = Query(..., min_length=1, description="Search query"),
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Search content blocks by title, description, or text.
    """
    results = ContentService.search_content(db, tenant.id, q)
    return [_build_block_list_response(b) for b in results]


@router.post("/upload", response_model=schemas.FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(require_any_role(UserRole.TENANT_ADMIN, UserRole.SUPER_ADMIN)),
):
    """
    Upload a file (image, PDF, video).

    - Max 10MB
    - Allowed: PNG, JPG, GIF, WEBP, PDF, MP4, WEBM
    - Requires TENANT_ADMIN or SUPER_ADMIN role
    """
    # Read file
    file_data = await file.read()
    size_bytes = len(file_data)

    # Validate size
    if size_bytes > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise FileTooLargeException(MAX_FILE_SIZE_MB)

    # Validate type
    if file.content_type not in ALLOWED_FILE_TYPES:
        raise InvalidFileTypeException(ALLOWED_FILE_TYPES)

    # Upload
    url = await storage_service.upload_file(
        file_data,
        file.filename or "file",
        folder=f"tenants/{tenant.id}/content",
        content_type=file.content_type
    )

    metadata = {
        "original_filename": file.filename,
        "size_bytes": size_bytes
    }

    return schemas.FileUploadResponse(
        url=url,
        content_type=file.content_type,
        size_bytes=size_bytes,
        metadata=metadata
    )


# =============================================================================
# Helper Functions
# =============================================================================

def _build_block_response(block) -> schemas.ContentBlockResponse:
    """Build full content block response."""
    category_response = None
    if block.category:
        category_response = schemas.ContentCategoryResponse(
            id=block.category.id,
            name=block.category.name,
            slug=block.category.slug,
            description=block.category.description,
            color=block.category.color,
            created_at=block.category.created_at
        )

    return schemas.ContentBlockResponse(
        id=block.id,
        tenant_id=block.tenant_id,
        title=block.title,
        description=block.description,
        content_type=block.content_type,
        content_text=block.content_text,
        content_url=block.content_url,
        content_metadata=block.content_metadata,
        category_id=block.category_id,
        category=category_response,
        tags=block.tags or [],
        is_published=block.is_published,
        created_at=block.created_at,
        updated_at=block.updated_at
    )


def _build_block_list_response(block) -> schemas.ContentBlockListResponse:
    """Build simplified content block response for lists."""
    return schemas.ContentBlockListResponse(
        id=block.id,
        title=block.title,
        description=block.description,
        content_type=block.content_type,
        category_id=block.category_id,
        category_name=block.category.name if block.category else None,
        tags=block.tags or [],
        is_published=block.is_published,
        created_at=block.created_at
    )
