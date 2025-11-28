"""
User models for the Users module.
Includes User model and UserInvitation model.
"""

from datetime import datetime, timezone, timedelta
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.core.models import BaseModel, BaseTenantModel, SoftDeleteMixin, TimestampMixin


class User(BaseTenantModel, SoftDeleteMixin):
    """
    User model for authentication and user management.

    Attributes:
        email: User's email address (unique)
        hashed_password: Bcrypt hashed password
        first_name: User's first name
        last_name: User's last name
        avatar_url: URL to user's avatar image
        phone: User's phone number
        job_title: User's job title
        department: User's department
        is_active: Whether the user account is active
        is_email_verified: Whether email has been verified
        role: User's role (super_admin, tenant_admin, employee)
    """

    __tablename__ = "users"

    # Override tenant_id from TenantMixin with explicit FK
    tenant_id = Column(
        Integer,
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Foreign key to tenant"
    )

    # Basic info
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)

    # Profile fields
    avatar_url = Column(String(500), nullable=True)
    phone = Column(String(50), nullable=True)
    job_title = Column(String(100), nullable=True)
    department = Column(String(100), nullable=True)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_email_verified = Column(Boolean, default=False, nullable=False)

    # Role
    role = Column(String(50), nullable=False, default="employee")

    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    password_reset_tokens = relationship("PasswordResetToken", back_populates="user", cascade="all, delete-orphan")
    email_verification_tokens = relationship("EmailVerificationToken", back_populates="user", cascade="all, delete-orphan")
    sent_invitations = relationship("UserInvitation", back_populates="inviter", foreign_keys="UserInvitation.invited_by")

    def __repr__(self):
        return f"<User {self.email}>"

    @property
    def full_name(self) -> str:
        """Returns user's full name."""
        return f"{self.first_name} {self.last_name}"

    @property
    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return self.role in ["super_admin", "tenant_admin"]

    @property
    def is_super_admin(self) -> bool:
        """Check if user is super admin."""
        return self.role == "super_admin"

    @property
    def is_tenant_admin(self) -> bool:
        """Check if user is tenant admin."""
        return self.role == "tenant_admin"


class UserInvitation(BaseModel, TimestampMixin):
    """
    User invitation model for inviting users to a tenant.

    Attributes:
        email: Email to send invitation to
        token: Unique invitation token
        role: Role to assign when invitation is accepted
        tenant_id: Tenant the invitation is for
        invited_by: User who sent the invitation
        is_accepted: Whether invitation has been accepted
        accepted_at: When the invitation was accepted
        expires_at: When the invitation expires
    """

    __tablename__ = "user_invitations"

    email = Column(String(255), nullable=False, index=True)
    token = Column(String(100), unique=True, nullable=False, index=True)
    role = Column(String(50), nullable=False, default="employee")

    # Tenant reference
    tenant_id = Column(
        Integer,
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Who invited
    invited_by = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    # Status
    is_accepted = Column(Boolean, default=False, nullable=False)
    accepted_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=False)

    # Relationships
    tenant = relationship("Tenant")
    inviter = relationship("User", back_populates="sent_invitations", foreign_keys=[invited_by])

    def __repr__(self):
        return f"<UserInvitation {self.email}>"

    @property
    def is_expired(self) -> bool:
        """Check if invitation has expired."""
        return datetime.now(timezone.utc) > self.expires_at.replace(tzinfo=timezone.utc)

    @property
    def is_valid(self) -> bool:
        """Check if invitation is still valid (not accepted and not expired)."""
        return not self.is_accepted and not self.is_expired

    @classmethod
    def default_expiry(cls) -> datetime:
        """Return default expiry date (7 days from now)."""
        return datetime.now(timezone.utc) + timedelta(days=7)
