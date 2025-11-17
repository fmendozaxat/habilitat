"""
User models.
Basic User model for authentication. Will be extended in Users module.
"""

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.core.models import BaseTenantModel, SoftDeleteMixin


class User(BaseTenantModel, SoftDeleteMixin):
    """User model for authentication and user management."""

    __tablename__ = "users"

    # Basic info
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_email_verified = Column(Boolean, default=False, nullable=False)

    # Role
    role = Column(String(50), nullable=False, default="employee")

    # Relationships (will be uncommented as modules are implemented)
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    password_reset_tokens = relationship("PasswordResetToken", back_populates="user", cascade="all, delete-orphan")
    email_verification_tokens = relationship("EmailVerificationToken", back_populates="user", cascade="all, delete-orphan")

    # tenant = relationship("Tenant", back_populates="users")
    # onboarding_assignments = relationship("OnboardingAssignment", back_populates="user")

    def __repr__(self):
        return f"<User {self.email}>"

    @property
    def full_name(self) -> str:
        """Returns user's full name."""
        return f"{self.first_name} {self.last_name}"
