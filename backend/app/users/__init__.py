"""
Users module initialization.
Basic user exports for Auth module. Will be extended in Users module.
"""

from app.users.models import User
from app.users.service import UserService

__all__ = [
    "User",
    "UserService",
]
