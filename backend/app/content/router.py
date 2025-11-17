"""
Content router.
Defines REST endpoints for content categories and blocks (CMS functionality).
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.auth.dependencies import get_current_user, require_tenant_admin
from app.users.models import User
from app.content import schemas
from app.content.service import ContentService
from app.core.exceptions import NotFoundException, AlreadyExistsException, ValidationException

router = APIRouter(prefix="/content", tags=["Content"])


# =========================================================================
# Category Endpoints
# =========================================================================

@router.post(
    "/categories",
    response_model=schemas.ContentCategoryResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_tenant_admin)]
)
def create_category(
    data: schemas.ContentCategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create content category.

    Requires tenant admin role.
    Auto-generates slug from name if not provided.
    """
    try:
        category = ContentService.create_category(db, current_user.tenant_id, data)
        return category
    except AlreadyExistsException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/categories",
    response_model=List[schemas.ContentCategoryResponse]
)
def list_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all content categories for current tenant.

    Returns categories ordered by name.
    """
    return ContentService.list_categories(db, current_user.tenant_id)


@router.get(
    "/categories/{category_id}",
    response_model=schemas.ContentCategoryResponse
)
def get_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get content category by ID."""
    try:
        return ContentService.get_category(db, category_id, current_user.tenant_id)
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch(
    "/categories/{category_id}",
    response_model=schemas.ContentCategoryResponse,
    dependencies=[Depends(require_tenant_admin)]
)
def update_category(
    category_id: int,
    data: schemas.ContentCategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update content category.

    Requires tenant admin role.
    """
    try:
        return ContentService.update_category(db, category_id, current_user.tenant_id, data)
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete(
    "/categories/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_tenant_admin)]
)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete content category.

    Requires tenant admin role.
    Cannot delete if category has associated content blocks.
    """
    try:
        ContentService.delete_category(db, category_id, current_user.tenant_id)
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# =========================================================================
# Content Block Endpoints
# =========================================================================

@router.post(
    "/blocks",
    response_model=schemas.ContentBlockResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_tenant_admin)]
)
def create_content_block(
    data: schemas.ContentBlockCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create content block.

    Requires tenant admin role.
    """
    block = ContentService.create_content_block(db, current_user.tenant_id, data)
    return block


@router.get(
    "/blocks",
    response_model=schemas.ContentBlockListResponse
)
def list_content_blocks(
    search: str = Query(None, description="Search in title, description, content"),
    content_type: str = Query(None, description="Filter by content type"),
    category_id: int = Query(None, description="Filter by category ID"),
    is_published: bool = Query(None, description="Filter by published status"),
    tags: List[str] = Query(None, description="Filter by tags"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List content blocks with filters and pagination.

    Supports:
    - Full-text search in title, description, and content
    - Filter by content type, category, published status, tags
    - Pagination
    """
    # Build filters
    filters = schemas.ContentFilterParams(
        search=search,
        content_type=content_type,
        category_id=category_id,
        is_published=is_published,
        tags=tags or [],
        page=page,
        page_size=page_size
    )

    blocks, total = ContentService.list_content_blocks(db, current_user.tenant_id, filters)

    return schemas.ContentBlockListResponse(
        items=blocks,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.get(
    "/blocks/{block_id}",
    response_model=schemas.ContentBlockResponse
)
def get_content_block(
    block_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get content block by ID."""
    try:
        return ContentService.get_content_block(db, block_id, current_user.tenant_id)
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch(
    "/blocks/{block_id}",
    response_model=schemas.ContentBlockResponse,
    dependencies=[Depends(require_tenant_admin)]
)
def update_content_block(
    block_id: int,
    data: schemas.ContentBlockUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update content block.

    Requires tenant admin role.
    """
    try:
        return ContentService.update_content_block(db, block_id, current_user.tenant_id, data)
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete(
    "/blocks/{block_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_tenant_admin)]
)
def delete_content_block(
    block_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Soft delete content block.

    Requires tenant admin role.
    Sets deleted_at timestamp instead of hard delete.
    """
    try:
        ContentService.delete_content_block(db, block_id, current_user.tenant_id)
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/blocks/{block_id}/duplicate",
    response_model=schemas.ContentBlockResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_tenant_admin)]
)
def duplicate_content_block(
    block_id: int,
    data: schemas.DuplicateContentBlockRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Duplicate content block.

    Requires tenant admin role.
    Creates a copy with a new title. The duplicate starts as unpublished.
    """
    try:
        return ContentService.duplicate_content_block(
            db, block_id, current_user.tenant_id, data.new_title
        )
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# =========================================================================
# Search Endpoint
# =========================================================================

@router.get(
    "/search",
    response_model=List[schemas.ContentBlockResponse]
)
def search_content(
    q: str = Query(..., min_length=2, description="Search query"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Search published content by text.

    Searches in title, description, and content_text.
    Returns published content only (max 20 results).
    """
    return ContentService.search_content(db, current_user.tenant_id, q)
