"""
Security utilities for authentication and authorization.
Handles password hashing, JWT token creation/validation, and security helpers.
"""

from datetime import datetime, timedelta
from typing import Dict, Any
from passlib.context import CryptContext
from jose import jwt, JWTError
from app.core.config import settings
from app.core.exceptions import InvalidTokenException, TokenExpiredException


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash a plain text password.

    Args:
        password: Plain text password

    Returns:
        Hashed password string
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to compare against

    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    data: Dict[str, Any],
    expires_delta: timedelta | None = None
) -> str:
    """
    Create a JWT access token.

    Args:
        data: Dictionary containing claims to encode in the token
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string

    Example:
        >>> token = create_access_token({"sub": "user@example.com", "user_id": 1})
    """
    to_encode = data.copy()

    # Set expiration
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )

    # Add standard claims
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })

    # Encode token
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )

    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """
    Create a JWT refresh token.

    Args:
        data: Dictionary containing claims to encode in the token

    Returns:
        Encoded JWT refresh token string

    Example:
        >>> token = create_refresh_token({"sub": "user@example.com", "user_id": 1})
    """
    to_encode = data.copy()

    # Set expiration (longer than access token)
    expire = datetime.utcnow() + timedelta(
        days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
    )

    # Add standard claims
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })

    # Encode token
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )

    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate a JWT token.

    Args:
        token: JWT token string to decode

    Returns:
        Dictionary containing the token's claims

    Raises:
        InvalidTokenException: If token is malformed or invalid
        TokenExpiredException: If token has expired

    Example:
        >>> payload = decode_token(token)
        >>> user_id = payload["user_id"]
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload

    except jwt.ExpiredSignatureError:
        raise TokenExpiredException()

    except JWTError:
        raise InvalidTokenException()


def verify_token_type(payload: Dict[str, Any], expected_type: str) -> bool:
    """
    Verify that a token payload has the expected type.

    Args:
        payload: Decoded token payload
        expected_type: Expected token type ("access" or "refresh")

    Returns:
        True if token type matches, False otherwise
    """
    return payload.get("type") == expected_type


def create_email_verification_token(email: str, user_id: int) -> str:
    """
    Create a token for email verification.

    Args:
        email: User's email address
        user_id: User's ID

    Returns:
        Encoded verification token
    """
    from app.core.constants import EMAIL_VERIFICATION_TOKEN_EXPIRE

    data = {
        "sub": email,
        "user_id": user_id,
        "purpose": "email_verification"
    }

    expire = datetime.utcnow() + timedelta(seconds=EMAIL_VERIFICATION_TOKEN_EXPIRE)

    to_encode = data.copy()
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
    })

    return jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )


def create_password_reset_token(email: str, user_id: int) -> str:
    """
    Create a token for password reset.

    Args:
        email: User's email address
        user_id: User's ID

    Returns:
        Encoded password reset token
    """
    from app.core.constants import PASSWORD_RESET_TOKEN_EXPIRE

    data = {
        "sub": email,
        "user_id": user_id,
        "purpose": "password_reset"
    }

    expire = datetime.utcnow() + timedelta(seconds=PASSWORD_RESET_TOKEN_EXPIRE)

    to_encode = data.copy()
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
    })

    return jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )


def verify_token_purpose(payload: Dict[str, Any], expected_purpose: str) -> bool:
    """
    Verify that a token has the expected purpose.

    Args:
        payload: Decoded token payload
        expected_purpose: Expected purpose (e.g., "email_verification", "password_reset")

    Returns:
        True if purpose matches, False otherwise
    """
    return payload.get("purpose") == expected_purpose
