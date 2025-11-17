"""
Custom exceptions for the Habilitat application.
Provides standardized HTTP exceptions for different error scenarios.
"""

from fastapi import HTTPException, status


class HabilitatException(HTTPException):
    """
    Base exception for all Habilitat application errors.

    Attributes:
        detail: Error message
        status_code: HTTP status code
    """

    def __init__(
        self,
        detail: str,
        status_code: int = status.HTTP_400_BAD_REQUEST
    ):
        super().__init__(status_code=status_code, detail=detail)


# Authentication and Authorization Exceptions

class UnauthorizedException(HabilitatException):
    """Raised when user is not authenticated."""

    def __init__(self, detail: str = "No autorizado"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_401_UNAUTHORIZED
        )


class ForbiddenException(HabilitatException):
    """Raised when user doesn't have permission to access resource."""

    def __init__(self, detail: str = "Acceso denegado"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_403_FORBIDDEN
        )


class InvalidCredentialsException(UnauthorizedException):
    """Raised when login credentials are invalid."""

    def __init__(self):
        super().__init__(detail="Credenciales inválidas")


class TokenExpiredException(UnauthorizedException):
    """Raised when JWT token has expired."""

    def __init__(self):
        super().__init__(detail="Token expirado")


class InvalidTokenException(UnauthorizedException):
    """Raised when JWT token is invalid."""

    def __init__(self):
        super().__init__(detail="Token inválido")


# Resource Exceptions

class NotFoundException(HabilitatException):
    """Raised when a resource is not found."""

    def __init__(self, resource: str = "Recurso"):
        super().__init__(
            detail=f"{resource} no encontrado",
            status_code=status.HTTP_404_NOT_FOUND
        )


class AlreadyExistsException(HabilitatException):
    """Raised when trying to create a resource that already exists."""

    def __init__(self, resource: str = "Recurso"):
        super().__init__(
            detail=f"{resource} ya existe",
            status_code=status.HTTP_409_CONFLICT
        )


class DuplicateException(HabilitatException):
    """Raised when a duplicate entry is detected."""

    def __init__(self, field: str):
        super().__init__(
            detail=f"Ya existe un registro con este {field}",
            status_code=status.HTTP_409_CONFLICT
        )


# Validation Exceptions

class ValidationException(HabilitatException):
    """Raised when data validation fails."""

    def __init__(self, detail: str):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )


class InvalidInputException(ValidationException):
    """Raised when input data is invalid."""

    def __init__(self, field: str, reason: str):
        super().__init__(detail=f"Campo '{field}' inválido: {reason}")


# Tenant Exceptions

class TenantNotFoundException(NotFoundException):
    """Raised when tenant is not found."""

    def __init__(self):
        super().__init__(resource="Tenant")


class TenantResolutionException(HabilitatException):
    """Raised when tenant cannot be resolved from request."""

    def __init__(self):
        super().__init__(
            detail="No se pudo resolver el tenant",
            status_code=status.HTTP_400_BAD_REQUEST
        )


class TenantMismatchException(ForbiddenException):
    """Raised when trying to access resource from different tenant."""

    def __init__(self):
        super().__init__(detail="No tiene acceso a este recurso")


# User Exceptions

class UserNotFoundException(NotFoundException):
    """Raised when user is not found."""

    def __init__(self):
        super().__init__(resource="Usuario")


class UserAlreadyExistsException(AlreadyExistsException):
    """Raised when trying to create a user that already exists."""

    def __init__(self):
        super().__init__(resource="Usuario")


class EmailAlreadyExistsException(DuplicateException):
    """Raised when email is already registered."""

    def __init__(self):
        super().__init__(field="email")


class InactiveUserException(ForbiddenException):
    """Raised when user account is inactive."""

    def __init__(self):
        super().__init__(detail="Cuenta de usuario inactiva")


# Business Logic Exceptions

class BusinessLogicException(HabilitatException):
    """Raised for business logic violations."""

    def __init__(self, detail: str):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_400_BAD_REQUEST
        )


class InsufficientPermissionsException(ForbiddenException):
    """Raised when user doesn't have required permissions."""

    def __init__(self, action: str):
        super().__init__(detail=f"No tiene permisos para {action}")


# File/Storage Exceptions

class FileUploadException(HabilitatException):
    """Raised when file upload fails."""

    def __init__(self, reason: str = "Error al subir archivo"):
        super().__init__(
            detail=reason,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class InvalidFileTypeException(ValidationException):
    """Raised when uploaded file type is not allowed."""

    def __init__(self, allowed_types: list[str]):
        types = ", ".join(allowed_types)
        super().__init__(
            detail=f"Tipo de archivo no permitido. Tipos permitidos: {types}"
        )


class FileSizeExceededException(ValidationException):
    """Raised when file size exceeds maximum allowed."""

    def __init__(self, max_size_mb: int):
        super().__init__(
            detail=f"El archivo excede el tamaño máximo permitido de {max_size_mb}MB"
        )
