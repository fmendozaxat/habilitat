"""
Content models.
Defines models for content blocks and categories (CMS functionality).
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.models import BaseModel, TimestampMixin, SoftDeleteMixin


class ContentCategory(BaseModel, TimestampMixin):
    """
    Content category model.
    Used to organize content blocks into categories.
    """

    __tablename__ = "content_categories"

    # Tenant relationship
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)

    # Basic info
    name = Column(String(100), nullable=False, comment="Category name")
    slug = Column(String(100), nullable=False, index=True, comment="URL-friendly slug")
    description = Column(String(500), nullable=True, comment="Category description")

    # UI color (hex)
    color = Column(String(7), default="#6B7280", nullable=False, comment="Color for UI (hex format)")

    # Relationships
    tenant = relationship("Tenant")
    content_blocks = relationship("ContentBlock", back_populates="category")

    def __repr__(self):
        return f"<ContentCategory {self.name}>"


class ContentBlock(BaseModel, TimestampMixin, SoftDeleteMixin):
    """
    Content block model.
    Reusable content blocks that can be referenced from onboarding modules.
    """

    __tablename__ = "content_blocks"

    # Tenant relationship
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)

    # Basic info
    title = Column(String(200), nullable=False, comment="Content block title")
    description = Column(Text, nullable=True, comment="Content block description")

    # Content type
    content_type = Column(
        String(50),
        nullable=False,
        comment="Type of content: text, image, video, pdf, link, embed"
    )

    # Content data
    content_text = Column(Text, nullable=True, comment="Text content (for type=text)")
    content_url = Column(String(500), nullable=True, comment="URL for files, videos, links")
    content_metadata = Column(JSON, nullable=True, comment="Content metadata (varies by type)")
    """
    Metadata examples by type:
    - image: {"width": 1920, "height": 1080, "size_bytes": 123456, "alt_text": "Description"}
    - video: {"duration_seconds": 120, "thumbnail_url": "...", "provider": "youtube"}
    - pdf: {"page_count": 10, "size_bytes": 987654}
    - embed: {"provider": "youtube", "embed_code": "..."}
    """

    # Organization
    category_id = Column(
        Integer,
        ForeignKey("content_categories.id", ondelete="SET NULL"),
        nullable=True,
        comment="Category for organization"
    )

    # Tags for search (JSON array)
    tags = Column(JSON, default=[], nullable=False, comment='Tags for searching: ["welcome", "culture", "benefits"]')

    # Status
    is_published = Column(Boolean, default=True, nullable=False, comment="Whether content is published")

    # Relationships
    tenant = relationship("Tenant")
    category = relationship("ContentCategory", back_populates="content_blocks")
    onboarding_modules = relationship(
        "OnboardingModule",
        back_populates="content",
        foreign_keys="OnboardingModule.content_id"
    )

    def __repr__(self):
        return f"<ContentBlock {self.title} ({self.content_type})>"
