"""
Auth module initialization.
Exports commonly used components for easy imports.
"""

from app.auth.models import RefreshToken, PasswordResetToken, EmailVerificationToken
from app.auth.service import AuthService
from app.auth.dependencies import (
    get_current_user,
    get_current_active_user,
    get_optional_user,
    require_role,
    require_any_role
)
from app.auth.router import router

__all__ = [
    # Models
    "RefreshToken",
    "PasswordResetToken",
    "EmailVerificationToken",
    # Service
    "AuthService",
    # Dependencies
    "get_current_user",
    "get_current_active_user",
    "get_optional_user",
    "require_role",
    "require_any_role",
    # Router
    "router",
]
