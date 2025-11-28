"""
Custom exceptions for Onboarding module.
"""

from fastapi import status
from app.core.exceptions import HabilitatException


class FlowNotFoundException(HabilitatException):
    """Raised when an onboarding flow is not found."""

    def __init__(self):
        super().__init__(
            detail="Flujo de onboarding no encontrado",
            status_code=status.HTTP_404_NOT_FOUND
        )


class ModuleNotFoundException(HabilitatException):
    """Raised when a module is not found."""

    def __init__(self):
        super().__init__(
            detail="Módulo no encontrado",
            status_code=status.HTTP_404_NOT_FOUND
        )


class AssignmentNotFoundException(HabilitatException):
    """Raised when an assignment is not found."""

    def __init__(self):
        super().__init__(
            detail="Asignación no encontrada",
            status_code=status.HTTP_404_NOT_FOUND
        )


class ProgressNotFoundException(HabilitatException):
    """Raised when module progress is not found."""

    def __init__(self):
        super().__init__(
            detail="Progreso de módulo no encontrado",
            status_code=status.HTTP_404_NOT_FOUND
        )


class FlowAlreadyAssignedException(HabilitatException):
    """Raised when a flow is already assigned to a user."""

    def __init__(self):
        super().__init__(
            detail="Este flujo ya está asignado al usuario",
            status_code=status.HTTP_409_CONFLICT
        )


class ModuleNotInFlowException(HabilitatException):
    """Raised when module doesn't belong to the specified flow."""

    def __init__(self):
        super().__init__(
            detail="El módulo no pertenece a este flujo",
            status_code=status.HTTP_400_BAD_REQUEST
        )


class NotAQuizModuleException(HabilitatException):
    """Raised when trying to submit quiz on non-quiz module."""

    def __init__(self):
        super().__init__(
            detail="Este módulo no es un quiz",
            status_code=status.HTTP_400_BAD_REQUEST
        )


class ModuleAlreadyCompletedException(HabilitatException):
    """Raised when trying to complete an already completed module."""

    def __init__(self):
        super().__init__(
            detail="Este módulo ya fue completado",
            status_code=status.HTTP_400_BAD_REQUEST
        )


class CannotModifyCompletedAssignmentException(HabilitatException):
    """Raised when trying to modify a completed assignment."""

    def __init__(self):
        super().__init__(
            detail="No se puede modificar una asignación completada",
            status_code=status.HTTP_400_BAD_REQUEST
        )


class FlowHasAssignmentsException(HabilitatException):
    """Raised when trying to delete a flow with active assignments."""

    def __init__(self):
        super().__init__(
            detail="No se puede eliminar un flujo con asignaciones activas",
            status_code=status.HTTP_400_BAD_REQUEST
        )


class InvalidQuizDataException(HabilitatException):
    """Raised when quiz data is invalid."""

    def __init__(self, detail: str = "Datos del quiz inválidos"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_400_BAD_REQUEST
        )
