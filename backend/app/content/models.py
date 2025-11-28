"""
Content models for CMS functionality.
ContentBlock and ContentCategory for reusable content management.
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.models import BaseTenantModel, SoftDeleteMixin


class ContentCategory(BaseTenantModel):
    """
    Category for organizing content blocks.

    Attributes:
        name: Category name
        slug: URL-friendly identifier
        description: Category description
        color: Hex color for UI display
    """

    __tablename__ = "content_categories"

    # Override tenant_id with explicit FK
    tenant_id = Column(
        Integer,
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    name = Column(String(100), nullable=False)
    slug = Column(String(100), nullable=False, index=True)
    description = Column(String(500), nullable=True)
    color = Column(String(7), default="#6B7280", nullable=False)

    # Relationships
    content_blocks = relationship("ContentBlock", back_populates="category")

    def __repr__(self):
        return f"<ContentCategory {self.name}>"


class ContentBlock(BaseTenantModel, SoftDeleteMixin):
    """
    Reusable content block.

    Attributes:
        title: Block title
        description: Block description
        content_type: Type of content (text, image, video, pdf, link, embed)
        content_text: Text content (for text type)
        content_url: URL for media content
        content_metadata: Additional metadata (JSON)
        category_id: Optional category
        tags: List of tags for search
        is_published: Publication status
    """

    __tablename__ = "content_blocks"

    # Override tenant_id with explicit FK
    tenant_id = Column(
        Integer,
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Basic info
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Content
    content_type = Column(String(50), nullable=False)  # text, image, video, pdf, link, embed
    content_text = Column(Text, nullable=True)
    content_url = Column(String(500), nullable=True)
    content_metadata = Column(JSON, nullable=True)

    # Organization
    category_id = Column(
        Integer,
        ForeignKey("content_categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Tags
    tags = Column(JSON, default=list, nullable=False)

    # Status
    is_published = Column(Boolean, default=True, nullable=False)

    # Relationships
    category = relationship("ContentCategory", back_populates="content_blocks")

    def __repr__(self):
        return f"<ContentBlock {self.title} ({self.content_type})>"
