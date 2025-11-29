"""
Tests for auth service.
"""

import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.auth.service import AuthService
from app.auth.models import RefreshToken, PasswordResetToken, EmailVerificationToken
from app.users.models import User
from app.tenants.models import Tenant


def create_test_tenant(db: Session) -> Tenant:
    """Helper to create a test tenant."""
    tenant = Tenant(name="Test Tenant", slug="test-tenant", plan="professional")
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant


def create_test_user(db: Session, tenant_id: int, email: str = "test@example.com") -> User:
    """Helper to create a test user."""
    user = User(
        email=email,
        hashed_password=get_password_hash("TestPassword123!"),
        first_name="Test",
        last_name="User",
        tenant_id=tenant_id,
        role="employee",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


class TestAuthentication:
    """Tests for user authentication."""

    def test_authenticate_user_success(self, db: Session):
        """Test successful authentication."""
        tenant = create_test_tenant(db)
        user = create_test_user(db, tenant.id)

        result = AuthService.authenticate_user(db, "test@example.com", "TestPassword123!")

        assert result is not None
        assert result.id == user.id
        assert result.email == user.email

    def test_authenticate_user_wrong_password(self, db: Session):
        """Test authentication with wrong password."""
        tenant = create_test_tenant(db)
        create_test_user(db, tenant.id)

        result = AuthService.authenticate_user(db, "test@example.com", "WrongPassword!")

        assert result is None

    def test_authenticate_user_nonexistent(self, db: Session):
        """Test authentication with nonexistent user."""
        result = AuthService.authenticate_user(db, "nonexistent@example.com", "Password123!")

        assert result is None

    def test_authenticate_inactive_user(self, db: Session):
        """Test authentication with inactive user."""
        tenant = create_test_tenant(db)
        user = User(
            email="inactive@example.com",
            hashed_password=get_password_hash("TestPassword123!"),
            first_name="Inactive",
            last_name="User",
            tenant_id=tenant.id,
            role="employee",
            is_active=False
        )
        db.add(user)
        db.commit()

        result = AuthService.authenticate_user(db, "inactive@example.com", "TestPassword123!")

        # Should still authenticate - activity check is done in router
        assert result is not None


class TestTokens:
    """Tests for token creation and validation."""

    def test_create_tokens(self, db: Session):
        """Test creating access and refresh tokens."""
        tenant = create_test_tenant(db)
        user = create_test_user(db, tenant.id)

        tokens = AuthService.create_tokens(db, user)

        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert "expires_in" in tokens
        assert tokens["expires_in"] > 0

    def test_refresh_token_stored_in_db(self, db: Session):
        """Test that refresh token is stored in database."""
        tenant = create_test_tenant(db)
        user = create_test_user(db, tenant.id)

        tokens = AuthService.create_tokens(db, user)

        # Check refresh token exists in DB
        stored_token = db.query(RefreshToken).filter(
            RefreshToken.user_id == user.id,
            RefreshToken.is_revoked == False
        ).first()

        assert stored_token is not None

    def test_refresh_access_token(self, db: Session):
        """Test refreshing access token."""
        tenant = create_test_tenant(db)
        user = create_test_user(db, tenant.id)

        tokens = AuthService.create_tokens(db, user)
        refresh_token = tokens["refresh_token"]

        new_access_token = AuthService.refresh_access_token(db, refresh_token)

        assert new_access_token is not None
        assert new_access_token != tokens["access_token"]

    def test_revoke_refresh_token(self, db: Session):
        """Test revoking refresh token."""
        tenant = create_test_tenant(db)
        user = create_test_user(db, tenant.id)

        tokens = AuthService.create_tokens(db, user)
        refresh_token = tokens["refresh_token"]

        AuthService.revoke_refresh_token(db, refresh_token)

        # Token should be revoked
        stored_token = db.query(RefreshToken).filter(
            RefreshToken.user_id == user.id
        ).first()

        assert stored_token.is_revoked == True

    def test_refresh_with_revoked_token_fails(self, db: Session):
        """Test that refreshing with revoked token fails."""
        tenant = create_test_tenant(db)
        user = create_test_user(db, tenant.id)

        tokens = AuthService.create_tokens(db, user)
        refresh_token = tokens["refresh_token"]

        AuthService.revoke_refresh_token(db, refresh_token)

        with pytest.raises(Exception):
            AuthService.refresh_access_token(db, refresh_token)


class TestPasswordReset:
    """Tests for password reset functionality."""

    def test_create_password_reset_token(self, db: Session):
        """Test creating password reset token."""
        tenant = create_test_tenant(db)
        user = create_test_user(db, tenant.id)

        token = AuthService.create_password_reset_token(db, user.email)

        assert token is not None
        assert token.user_id == user.id
        assert token.is_used == False
        assert token.expires_at > datetime.now(timezone.utc)

    def test_reset_password(self, db: Session):
        """Test resetting password with valid token."""
        tenant = create_test_tenant(db)
        user = create_test_user(db, tenant.id)

        reset_token = AuthService.create_password_reset_token(db, user.email)
        new_password = "NewPassword456!"

        AuthService.reset_password(db, reset_token.token, new_password)

        # Verify password was changed
        db.refresh(user)
        assert verify_password(new_password, user.hashed_password)

    def test_reset_password_marks_token_used(self, db: Session):
        """Test that password reset marks token as used."""
        tenant = create_test_tenant(db)
        user = create_test_user(db, tenant.id)

        reset_token = AuthService.create_password_reset_token(db, user.email)

        AuthService.reset_password(db, reset_token.token, "NewPassword456!")

        db.refresh(reset_token)
        assert reset_token.is_used == True

    def test_reset_password_with_used_token_fails(self, db: Session):
        """Test that resetting with used token fails."""
        tenant = create_test_tenant(db)
        user = create_test_user(db, tenant.id)

        reset_token = AuthService.create_password_reset_token(db, user.email)

        # Use the token
        AuthService.reset_password(db, reset_token.token, "NewPassword456!")

        # Try to use again
        with pytest.raises(Exception):
            AuthService.reset_password(db, reset_token.token, "AnotherPassword789!")

    def test_reset_password_with_expired_token_fails(self, db: Session):
        """Test that resetting with expired token fails."""
        tenant = create_test_tenant(db)
        user = create_test_user(db, tenant.id)

        reset_token = AuthService.create_password_reset_token(db, user.email)

        # Manually expire the token
        reset_token.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
        db.commit()

        with pytest.raises(Exception):
            AuthService.reset_password(db, reset_token.token, "NewPassword456!")


class TestEmailVerification:
    """Tests for email verification functionality."""

    def test_create_email_verification_token(self, db: Session):
        """Test creating email verification token."""
        tenant = create_test_tenant(db)
        user = create_test_user(db, tenant.id)

        token = AuthService.create_email_verification_token(db, user.id)

        assert token is not None
        assert token.user_id == user.id
        assert token.is_used == False

    def test_verify_email(self, db: Session):
        """Test verifying email with valid token."""
        tenant = create_test_tenant(db)
        user = create_test_user(db, tenant.id)
        user.is_email_verified = False
        db.commit()

        verification_token = AuthService.create_email_verification_token(db, user.id)

        AuthService.verify_email(db, verification_token.token)

        db.refresh(user)
        assert user.is_email_verified == True

    def test_verify_email_marks_token_used(self, db: Session):
        """Test that email verification marks token as used."""
        tenant = create_test_tenant(db)
        user = create_test_user(db, tenant.id)

        verification_token = AuthService.create_email_verification_token(db, user.id)

        AuthService.verify_email(db, verification_token.token)

        db.refresh(verification_token)
        assert verification_token.is_used == True
