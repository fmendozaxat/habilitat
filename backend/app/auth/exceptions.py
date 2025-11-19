"""Auth module exceptions."""

from app.core.exceptions import HTTPException


class InvalidCredentialsException(HTTPException):
    """Raised when login credentials are invalid."""

    def __init__(self):
        super().__init__(
            status_code=401,
            detail="Invalid email or password"
        )


class InvalidTokenException(HTTPException):
    """Raised when token is invalid or malformed."""

    def __init__(self):
        super().__init__(
            status_code=401,
            detail="Invalid or malformed token"
        )


class TokenExpiredException(HTTPException):
    """Raised when token has expired."""

    def __init__(self):
        super().__init__(
            status_code=401,
            detail="Token has expired"
        )


class UserNotVerifiedException(HTTPException):
    """Raised when user email is not verified."""

    def __init__(self):
        super().__init__(
            status_code=403,
            detail="Email not verified. Please verify your email first."
        )


class UserInactiveException(HTTPException):
    """Raised when user is inactive."""

    def __init__(self):
        super().__init__(
            status_code=403,
            detail="User account is inactive"
        )


class InvalidEmailVerificationTokenException(HTTPException):
    """Raised when email verification token is invalid or expired."""

    def __init__(self):
        super().__init__(
            status_code=400,
            detail="Invalid or expired email verification token"
        )


class InvalidPasswordResetTokenException(HTTPException):
    """Raised when password reset token is invalid or expired."""

    def __init__(self):
        super().__init__(
            status_code=400,
            detail="Invalid or expired password reset token"
        )


class RefreshTokenNotValidException(HTTPException):
    """Raised when refresh token is not valid."""

    def __init__(self):
        super().__init__(
            status_code=401,
            detail="Refresh token is not valid"
        )
