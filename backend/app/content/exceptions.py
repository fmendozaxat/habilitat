"""
Custom exceptions for Content module.
"""

from fastapi import status
from app.core.exceptions import HabilitatException


class ContentBlockNotFoundException(HabilitatException):
    """Raised when a content block is not found."""

    def __init__(self):
        super().__init__(
            detail="Bloque de contenido no encontrado",
            status_code=status.HTTP_404_NOT_FOUND
        )


class CategoryNotFoundException(HabilitatException):
    """Raised when a category is not found."""

    def __init__(self):
        super().__init__(
            detail="Categoría no encontrada",
            status_code=status.HTTP_404_NOT_FOUND
        )


class CategoryAlreadyExistsException(HabilitatException):
    """Raised when a category with the same slug exists."""

    def __init__(self, slug: str):
        super().__init__(
            detail=f"Ya existe una categoría con el slug '{slug}'",
            status_code=status.HTTP_409_CONFLICT
        )


class CategoryHasContentException(HabilitatException):
    """Raised when trying to delete a category with content."""

    def __init__(self):
        super().__init__(
            detail="No se puede eliminar una categoría con contenido asociado",
            status_code=status.HTTP_400_BAD_REQUEST
        )


class InvalidFileTypeException(HabilitatException):
    """Raised when file type is not allowed."""

    def __init__(self, allowed_types: list[str] | None = None):
        detail = "Tipo de archivo no permitido"
        if allowed_types:
            detail += f". Permitidos: {', '.join(allowed_types)}"
        super().__init__(
            detail=detail,
            status_code=status.HTTP_400_BAD_REQUEST
        )


class FileTooLargeException(HabilitatException):
    """Raised when file exceeds size limit."""

    def __init__(self, max_size_mb: int = 10):
        super().__init__(
            detail=f"Archivo muy grande. Máximo {max_size_mb}MB",
            status_code=status.HTTP_400_BAD_REQUEST
        )
