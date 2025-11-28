"""
Custom exceptions for Users module.
"""

from fastapi import status
from app.core.exceptions import HabilitatException


class UserNotFoundException(HabilitatException):
    """Raised when a user is not found."""

    def __init__(self, detail: str = "Usuario no encontrado"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_404_NOT_FOUND
        )


class UserAlreadyExistsException(HabilitatException):
    """Raised when trying to create a user with existing email."""

    def __init__(self, email: str | None = None):
        detail = f"Usuario con email '{email}' ya existe" if email else "El email ya está registrado"
        super().__init__(
            detail=detail,
            status_code=status.HTTP_409_CONFLICT
        )


class UserLimitReachedException(HabilitatException):
    """Raised when tenant user limit is reached."""

    def __init__(self):
        super().__init__(
            detail="Límite de usuarios alcanzado para este tenant",
            status_code=status.HTTP_400_BAD_REQUEST
        )


class InvalidPasswordException(HabilitatException):
    """Raised when password validation fails."""

    def __init__(self, detail: str = "Contraseña actual incorrecta"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_400_BAD_REQUEST
        )


class InvitationNotFoundException(HabilitatException):
    """Raised when invitation is not found."""

    def __init__(self):
        super().__init__(
            detail="Invitación no encontrada",
            status_code=status.HTTP_404_NOT_FOUND
        )


class InvitationExpiredException(HabilitatException):
    """Raised when invitation has expired."""

    def __init__(self):
        super().__init__(
            detail="La invitación ha expirado",
            status_code=status.HTTP_400_BAD_REQUEST
        )


class InvitationAlreadyAcceptedException(HabilitatException):
    """Raised when invitation was already accepted."""

    def __init__(self):
        super().__init__(
            detail="Esta invitación ya fue aceptada",
            status_code=status.HTTP_400_BAD_REQUEST
        )


class PendingInvitationExistsException(HabilitatException):
    """Raised when a pending invitation already exists for email."""

    def __init__(self, email: str | None = None):
        detail = f"Ya existe una invitación pendiente para '{email}'" if email else "Ya existe una invitación pendiente"
        super().__init__(
            detail=detail,
            status_code=status.HTTP_409_CONFLICT
        )


class CannotDeleteSelfException(HabilitatException):
    """Raised when user tries to delete themselves."""

    def __init__(self):
        super().__init__(
            detail="No puedes eliminarte a ti mismo",
            status_code=status.HTTP_400_BAD_REQUEST
        )


class UserNotInTenantException(HabilitatException):
    """Raised when user doesn't belong to the tenant."""

    def __init__(self):
        super().__init__(
            detail="Este usuario no pertenece a tu organización",
            status_code=status.HTTP_403_FORBIDDEN
        )
