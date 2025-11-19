"""
Tenant models for multitenant functionality.
Defines Tenant and TenantBranding models for organization management.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.core.models import BaseModel, TimestampMixin, SoftDeleteMixin


class Tenant(BaseModel, TimestampMixin, SoftDeleteMixin):
    """
    Main organization/company model.
    Each tenant is a separate organization with its own users, content, and branding.
    """

    __tablename__ = "tenants"

    # Basic info
    name = Column(String(200), nullable=False, comment="Organization name")
    slug = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        comment="URL-friendly identifier"
    )
    subdomain = Column(
        String(100),
        unique=True,
        nullable=True,
        index=True,
        comment="Subdomain for tenant-specific access"
    )

    # Contact information
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(50), nullable=True)

    # Status
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether the tenant is active"
    )

    # Plan & Limits (for future billing)
    plan = Column(
        String(50),
        default="free",
        nullable=False,
        comment="Subscription plan: free, starter, business, enterprise"
    )
    max_users = Column(
        Integer,
        default=10,
        nullable=False,
        comment="Maximum number of users allowed"
    )
    max_storage_mb = Column(
        Integer,
        default=1000,
        nullable=False,
        comment="Maximum storage in MB (default: 1GB)"
    )

    # Settings (JSON for flexibility)
    settings = Column(
        JSON,
        default={},
        nullable=False,
        comment="Tenant-specific settings and configurations"
    )
    """
    Example settings structure:
    {
        "onboarding_auto_assign": true,
        "require_email_verification": true,
        "allow_self_registration": false,
        "custom_domain": "onboarding.company.com",
        "session_timeout_minutes": 30
    }
    """

    # Relationships
    # NOTE: These will be uncommented as modules are implemented
    # users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    # onboarding_flows = relationship("OnboardingFlow", back_populates="tenant", cascade="all, delete-orphan")
    # content_blocks = relationship("ContentBlock", back_populates="tenant", cascade="all, delete-orphan")

    branding = relationship(
        "TenantBranding",
        back_populates="tenant",
        uselist=False,
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Tenant {self.name} ({self.slug})>"

    @property
    def full_domain(self) -> str | None:
        """
        Returns the full domain for the tenant.

        Returns:
            Full domain string or None if no subdomain is set

        Example:
            >>> tenant.subdomain = "acme"
            >>> tenant.full_domain
            "acme.habilitat.com"
        """
        if self.subdomain:
            return f"{self.subdomain}.habilitat.com"
        return None

    @property
    def user_count(self) -> int:
        """
        Returns the number of users in the tenant.

        Returns:
            Number of users

        Note:
            Returns 0 if relationship is not loaded. Use with caution in queries
            to avoid N+1 problems. Consider using a dedicated query method instead.
        """
        if hasattr(self, 'users') and self.users is not None:
            return len(self.users)
        return 0

    @property
    def is_at_user_limit(self) -> bool:
        """
        Check if tenant has reached maximum user limit.

        Returns:
            True if at or over limit, False otherwise
        """
        return self.user_count >= self.max_users


class TenantBranding(BaseModel, TimestampMixin):
    """
    Branding and visual customization for a tenant.
    Stores logos, colors, images, and typography settings.
    """

    __tablename__ = "tenant_branding"

    tenant_id = Column(
        Integer,
        ForeignKey("tenants.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        comment="Foreign key to tenant"
    )

    # Logo images
    logo_url = Column(
        String(500),
        nullable=True,
        comment="Main logo URL"
    )
    logo_dark_url = Column(
        String(500),
        nullable=True,
        comment="Logo for dark theme (optional)"
    )
    favicon_url = Column(
        String(500),
        nullable=True,
        comment="Favicon URL"
    )

    # Colors (hex codes)
    primary_color = Column(
        String(7),
        default="#3B82F6",
        nullable=False,
        comment="Primary brand color (hex)"
    )
    secondary_color = Column(
        String(7),
        default="#10B981",
        nullable=False,
        comment="Secondary brand color (hex)"
    )
    accent_color = Column(
        String(7),
        default="#F59E0B",
        nullable=True,
        comment="Accent color (hex)"
    )
    background_color = Column(
        String(7),
        default="#FFFFFF",
        nullable=False,
        comment="Background color (hex)"
    )
    text_color = Column(
        String(7),
        default="#1F2937",
        nullable=False,
        comment="Text color (hex)"
    )

    # Background images
    hero_image_url = Column(
        String(500),
        nullable=True,
        comment="Hero section background image"
    )
    background_image_url = Column(
        String(500),
        nullable=True,
        comment="General background image"
    )

    # Typography
    font_family = Column(
        String(100),
        nullable=True,
        comment="Custom font family (e.g., 'Inter', 'Roboto')"
    )

    # Custom CSS (for advanced customization, post-MVP)
    custom_css = Column(
        String(5000),
        nullable=True,
        comment="Custom CSS for advanced styling"
    )

    # Relationship
    tenant = relationship("Tenant", back_populates="branding")

    def __repr__(self):
        return f"<TenantBranding tenant_id={self.tenant_id}>"

    def to_theme_dict(self) -> dict:
        """
        Convert branding to theme dictionary for frontend.

        Returns:
            Dictionary with structured theme data

        Example:
            >>> branding.to_theme_dict()
            {
                "logo": "https://...",
                "colors": {"primary": "#3B82F6", ...},
                ...
            }
        """
        return {
            "logo": self.logo_url,
            "logo_dark": self.logo_dark_url,
            "favicon": self.favicon_url,
            "colors": {
                "primary": self.primary_color,
                "secondary": self.secondary_color,
                "accent": self.accent_color,
                "background": self.background_color,
                "text": self.text_color
            },
            "images": {
                "hero": self.hero_image_url,
                "background": self.background_image_url
            },
            "typography": {
                "font_family": self.font_family
            }
        }
