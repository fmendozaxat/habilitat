"""Auth models for token management."""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.core.models import BaseModel, TimestampMixin


class RefreshToken(BaseModel, TimestampMixin):
    """Stores refresh tokens for revocation capability."""

    __tablename__ = "refresh_tokens"

    token = Column(String(500), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_revoked = Column(Boolean, default=False, nullable=False)

    user = relationship("User", back_populates="refresh_tokens")

    @property
    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.expires_at

    @property
    def is_valid(self) -> bool:
        return not self.is_revoked and not self.is_expired


class PasswordResetToken(BaseModel, TimestampMixin):
    """Tokens for password reset."""

    __tablename__ = "password_reset_tokens"

    token = Column(String(100), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False, nullable=False)

    user = relationship("User", back_populates="password_reset_tokens")

    @property
    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.expires_at

    @property
    def is_valid(self) -> bool:
        return not self.is_used and not self.is_expired


class EmailVerificationToken(BaseModel, TimestampMixin):
    """Tokens for email verification."""

    __tablename__ = "email_verification_tokens"

    token = Column(String(100), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False, nullable=False)

    user = relationship("User", back_populates="email_verification_tokens")

    @property
    def is_valid(self) -> bool:
        return not self.is_used and not self.is_expired

    @property
    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.expires_at
