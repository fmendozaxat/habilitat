"""
Content service for business logic operations.
Handles CRUD for content blocks and categories.
"""

from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.utils import slugify
from app.content.models import ContentBlock, ContentCategory
from app.content import schemas
from app.content.exceptions import (
    ContentBlockNotFoundException,
    CategoryNotFoundException,
    CategoryAlreadyExistsException,
    CategoryHasContentException
)


class ContentService:
    """Service class for content management operations."""

    # =========================================================================
    # Category Operations
    # =========================================================================

    @staticmethod
    def create_category(
        db: Session,
        tenant_id: int,
        data: schemas.ContentCategoryCreate
    ) -> ContentCategory:
        """Create a content category."""
        # Auto-generate slug if not provided
        slug = data.slug or slugify(data.name)

        # Check for duplicate slug
        existing = db.query(ContentCategory).filter(
            ContentCategory.tenant_id == tenant_id,
            ContentCategory.slug == slug
        ).first()

        if existing:
            raise CategoryAlreadyExistsException(slug)

        category = ContentCategory(
            tenant_id=tenant_id,
            name=data.name,
            slug=slug,
            description=data.description,
            color=data.color
        )

        db.add(category)
        db.commit()
        db.refresh(category)

        return category

    @staticmethod
    def get_category(db: Session, category_id: int, tenant_id: int) -> ContentCategory:
        """Get category by ID."""
        category = db.query(ContentCategory).filter(
            ContentCategory.id == category_id,
            ContentCategory.tenant_id == tenant_id
        ).first()

        if not category:
            raise CategoryNotFoundException()

        return category

    @staticmethod
    def list_categories(db: Session, tenant_id: int) -> list[ContentCategory]:
        """List all categories for a tenant."""
        return db.query(ContentCategory).filter(
            ContentCategory.tenant_id == tenant_id
        ).order_by(ContentCategory.name).all()

    @staticmethod
    def update_category(
        db: Session,
        category_id: int,
        tenant_id: int,
        data: schemas.ContentCategoryUpdate
    ) -> ContentCategory:
        """Update a category."""
        category = ContentService.get_category(db, category_id, tenant_id)

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(category, field, value)

        db.commit()
        db.refresh(category)

        return category

    @staticmethod
    def delete_category(db: Session, category_id: int, tenant_id: int) -> bool:
        """Delete a category."""
        category = ContentService.get_category(db, category_id, tenant_id)

        # Check for associated content
        content_count = db.query(ContentBlock).filter(
            ContentBlock.category_id == category_id,
            ContentBlock.deleted_at.is_(None)
        ).count()

        if content_count > 0:
            raise CategoryHasContentException()

        db.delete(category)
        db.commit()

        return True

    # =========================================================================
    # Content Block Operations
    # =========================================================================

    @staticmethod
    def create_content_block(
        db: Session,
        tenant_id: int,
        data: schemas.ContentBlockCreate
    ) -> ContentBlock:
        """Create a content block."""
        block = ContentBlock(
            tenant_id=tenant_id,
            title=data.title,
            description=data.description,
            content_type=data.content_type,
            content_text=data.content_text,
            content_url=data.content_url,
            content_metadata=data.content_metadata,
            category_id=data.category_id,
            tags=data.tags or [],
            is_published=data.is_published
        )

        db.add(block)
        db.commit()
        db.refresh(block)

        return block

    @staticmethod
    def get_content_block(db: Session, block_id: int, tenant_id: int) -> ContentBlock:
        """Get content block by ID."""
        block = db.query(ContentBlock).filter(
            ContentBlock.id == block_id,
            ContentBlock.tenant_id == tenant_id,
            ContentBlock.deleted_at.is_(None)
        ).first()

        if not block:
            raise ContentBlockNotFoundException()

        return block

    @staticmethod
    def list_content_blocks(
        db: Session,
        tenant_id: int,
        filters: schemas.ContentFilterParams
    ) -> tuple[list[ContentBlock], int]:
        """List content blocks with filters and pagination."""
        query = db.query(ContentBlock).filter(
            ContentBlock.tenant_id == tenant_id,
            ContentBlock.deleted_at.is_(None)
        )

        # Apply filters
        if filters.search:
            search_term = f"%{filters.search}%"
            query = query.filter(
                or_(
                    ContentBlock.title.ilike(search_term),
                    ContentBlock.description.ilike(search_term),
                    ContentBlock.content_text.ilike(search_term)
                )
            )

        if filters.content_type:
            query = query.filter(ContentBlock.content_type == filters.content_type)

        if filters.category_id:
            query = query.filter(ContentBlock.category_id == filters.category_id)

        if filters.is_published is not None:
            query = query.filter(ContentBlock.is_published == filters.is_published)

        # Get total count
        total = query.count()

        # Apply pagination
        blocks = query.order_by(
            ContentBlock.created_at.desc()
        ).offset(filters.offset).limit(filters.page_size).all()

        return blocks, total

    @staticmethod
    def update_content_block(
        db: Session,
        block_id: int,
        tenant_id: int,
        data: schemas.ContentBlockUpdate
    ) -> ContentBlock:
        """Update a content block."""
        block = ContentService.get_content_block(db, block_id, tenant_id)

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(block, field, value)

        db.commit()
        db.refresh(block)

        return block

    @staticmethod
    def delete_content_block(db: Session, block_id: int, tenant_id: int) -> bool:
        """Soft delete a content block."""
        block = ContentService.get_content_block(db, block_id, tenant_id)

        block.deleted_at = datetime.now(timezone.utc)
        db.commit()

        return True

    @staticmethod
    def duplicate_content_block(
        db: Session,
        block_id: int,
        tenant_id: int,
        new_title: str
    ) -> ContentBlock:
        """Duplicate a content block."""
        original = ContentService.get_content_block(db, block_id, tenant_id)

        new_block = ContentBlock(
            tenant_id=tenant_id,
            title=new_title,
            description=original.description,
            content_type=original.content_type,
            content_text=original.content_text,
            content_url=original.content_url,
            content_metadata=original.content_metadata.copy() if original.content_metadata else None,
            category_id=original.category_id,
            tags=original.tags.copy() if original.tags else [],
            is_published=False  # Start as unpublished
        )

        db.add(new_block)
        db.commit()
        db.refresh(new_block)

        return new_block

    @staticmethod
    def search_content(
        db: Session,
        tenant_id: int,
        query: str,
        limit: int = 20
    ) -> list[ContentBlock]:
        """Search content by text."""
        search_term = f"%{query}%"

        return db.query(ContentBlock).filter(
            ContentBlock.tenant_id == tenant_id,
            ContentBlock.deleted_at.is_(None),
            ContentBlock.is_published == True,
            or_(
                ContentBlock.title.ilike(search_term),
                ContentBlock.description.ilike(search_term),
                ContentBlock.content_text.ilike(search_term)
            )
        ).limit(limit).all()
