"""
Tests for core security utilities.
"""

import pytest
from datetime import timedelta
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_token_type,
    create_email_verification_token,
    create_password_reset_token,
    verify_token_purpose
)
from app.core.exceptions import TokenExpiredException, InvalidTokenException


class TestPasswordHashing:
    """Tests for password hashing functions."""

    def test_hash_password(self):
        """Test password hashing."""
        password = "SecurePassword123!"
        hashed = hash_password(password)

        assert hashed != password
        assert len(hashed) > 0

    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "SecurePassword123!"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "SecurePassword123!"
        wrong_password = "WrongPassword456!"
        hashed = hash_password(password)

        assert verify_password(wrong_password, hashed) is False

    def test_same_password_different_hashes(self):
        """Test that same password produces different hashes (salt)."""
        password = "SecurePassword123!"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != hash2
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestJWTTokens:
    """Tests for JWT token functions."""

    def test_create_access_token(self):
        """Test access token creation."""
        data = {"sub": "user@example.com", "user_id": 1}
        token = create_access_token(data)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_refresh_token(self):
        """Test refresh token creation."""
        data = {"sub": "user@example.com", "user_id": 1}
        token = create_refresh_token(data)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_valid_token(self):
        """Test decoding a valid token."""
        data = {"sub": "user@example.com", "user_id": 1}
        token = create_access_token(data)

        decoded = decode_token(token)

        assert decoded["sub"] == "user@example.com"
        assert decoded["user_id"] == 1
        assert "exp" in decoded
        assert "iat" in decoded
        assert decoded["type"] == "access"

    def test_decode_invalid_token(self):
        """Test decoding an invalid token."""
        with pytest.raises(InvalidTokenException):
            decode_token("invalid.token.here")

    def test_token_with_custom_expiration(self):
        """Test token creation with custom expiration."""
        data = {"sub": "user@example.com"}
        expires_delta = timedelta(hours=1)

        token = create_access_token(data, expires_delta=expires_delta)
        decoded = decode_token(token)

        assert "exp" in decoded

    def test_verify_token_type_access(self):
        """Test verifying access token type."""
        data = {"sub": "user@example.com"}
        token = create_access_token(data)
        decoded = decode_token(token)

        assert verify_token_type(decoded, "access") is True
        assert verify_token_type(decoded, "refresh") is False

    def test_verify_token_type_refresh(self):
        """Test verifying refresh token type."""
        data = {"sub": "user@example.com"}
        token = create_refresh_token(data)
        decoded = decode_token(token)

        assert verify_token_type(decoded, "refresh") is True
        assert verify_token_type(decoded, "access") is False


class TestSpecialTokens:
    """Tests for special purpose tokens."""

    def test_create_email_verification_token(self):
        """Test email verification token creation."""
        email = "user@example.com"
        user_id = 1

        token = create_email_verification_token(email, user_id)
        decoded = decode_token(token)

        assert decoded["sub"] == email
        assert decoded["user_id"] == user_id
        assert decoded["purpose"] == "email_verification"

    def test_create_password_reset_token(self):
        """Test password reset token creation."""
        email = "user@example.com"
        user_id = 1

        token = create_password_reset_token(email, user_id)
        decoded = decode_token(token)

        assert decoded["sub"] == email
        assert decoded["user_id"] == user_id
        assert decoded["purpose"] == "password_reset"

    def test_verify_token_purpose(self):
        """Test verifying token purpose."""
        email = "user@example.com"
        user_id = 1

        token = create_email_verification_token(email, user_id)
        decoded = decode_token(token)

        assert verify_token_purpose(decoded, "email_verification") is True
        assert verify_token_purpose(decoded, "password_reset") is False
