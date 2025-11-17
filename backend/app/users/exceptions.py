"""User-specific exceptions."""

from app.core.exceptions import HabilitatException
from fastapi import status


class UserNotFoundException(HabilitatException):
    """Exception raised when user is not found."""

    def __init__(self):
        super().__init__(
            detail="Usuario no encontrado",
            status_code=status.HTTP_404_NOT_FOUND
        )


class UserLimitReachedException(HabilitatException):
    """Exception raised when tenant user limit is reached."""

    def __init__(self):
        super().__init__(
            detail="Límite de usuarios alcanzado para este tenant",
            status_code=status.HTTP_400_BAD_REQUEST
        )


class InvitationNotFoundException(HabilitatException):
    """Exception raised when invitation is not found."""

    def __init__(self):
        super().__init__(
            detail="Invitación no encontrada",
            status_code=status.HTTP_404_NOT_FOUND
        )


class InvitationExpiredException(HabilitatException):
    """Exception raised when invitation has expired."""

    def __init__(self):
        super().__init__(
            detail="Invitación expirada",
            status_code=status.HTTP_400_BAD_REQUEST
        )


class InvitationAlreadyAcceptedException(HabilitatException):
    """Exception raised when trying to accept an already accepted invitation."""

    def __init__(self):
        super().__init__(
            detail="Invitación ya aceptada",
            status_code=status.HTTP_400_BAD_REQUEST
        )
