"""
User models.
User model for authentication and user management.
"""

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.core.models import BaseModel, TimestampMixin, SoftDeleteMixin
from app.core.enums import UserRole


class User(BaseModel, TimestampMixin, SoftDeleteMixin):
    """User model for authentication and user management."""

    __tablename__ = "users"

    # Tenant relationship
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)

    # Basic info
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)

    # Profile
    avatar_url = Column(String(500), nullable=True)
    phone = Column(String(50), nullable=True)
    job_title = Column(String(100), nullable=True)
    department = Column(String(100), nullable=True)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_email_verified = Column(Boolean, default=False, nullable=False)

    # Role
    role = Column(String(50), nullable=False, default=UserRole.EMPLOYEE.value)

    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    password_reset_tokens = relationship("PasswordResetToken", back_populates="user", cascade="all, delete-orphan")
    email_verification_tokens = relationship("EmailVerificationToken", back_populates="user", cascade="all, delete-orphan")
    onboarding_assignments = relationship("OnboardingAssignment", foreign_keys="OnboardingAssignment.user_id", back_populates="user")

    def __repr__(self):
        return f"<User {self.email}>"

    @property
    def full_name(self) -> str:
        """Returns user's full name."""
        return f"{self.first_name} {self.last_name}"

    @property
    def is_admin(self) -> bool:
        """Check if user has admin privileges."""
        return self.role in [UserRole.SUPER_ADMIN.value, UserRole.TENANT_ADMIN.value]

    @property
    def is_super_admin(self) -> bool:
        """Check if user is super admin."""
        return self.role == UserRole.SUPER_ADMIN.value

    @property
    def is_tenant_admin(self) -> bool:
        """Check if user is tenant admin."""
        return self.role == UserRole.TENANT_ADMIN.value


class UserInvitation(BaseModel, TimestampMixin):
    """User invitation model for inviting users to a tenant."""

    __tablename__ = "user_invitations"

    # Tenant relationship
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)

    # Invitation details
    email = Column(String(255), nullable=False, index=True)
    token = Column(String(100), unique=True, nullable=False, index=True)
    role = Column(String(50), nullable=False, default=UserRole.EMPLOYEE.value)

    # Who invited
    invited_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Status
    is_accepted = Column(Boolean, default=False, nullable=False)
    accepted_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=False)

    # Relationships
    tenant = relationship("Tenant")
    inviter = relationship("User", foreign_keys=[invited_by])

    def __repr__(self):
        return f"<UserInvitation {self.email}>"

    @property
    def is_expired(self) -> bool:
        """Check if invitation is expired."""
        from datetime import datetime
        return datetime.utcnow() > self.expires_at

    @property
    def is_valid(self) -> bool:
        """Check if invitation is valid (not accepted and not expired)."""
        return not self.is_accepted and not self.is_expired
