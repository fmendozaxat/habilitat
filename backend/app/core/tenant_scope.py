"""
Tenant scoping utilities for multi-tenant resource access validation.
Provides decorators and helpers to ensure resources belong to current tenant.
"""

from functools import wraps
from typing import Callable, Any
from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenException, NotFoundException


def validate_tenant_resource(
    db: Session,
    model_class: Any,
    resource_id: int,
    tenant_id: int,
    resource_name: str = "Recurso"
) -> Any:
    """
    Validate that a resource belongs to the given tenant.

    Args:
        db: Database session
        model_class: SQLAlchemy model class
        resource_id: ID of the resource to check
        tenant_id: Tenant ID to validate against
        resource_name: Human-readable name for error messages

    Returns:
        The resource if valid

    Raises:
        NotFoundException: If resource doesn't exist
        ForbiddenException: If resource belongs to different tenant
    """
    resource = db.query(model_class).filter(model_class.id == resource_id).first()

    if not resource:
        raise NotFoundException(f"{resource_name} no encontrado")

    # Check if model has tenant_id attribute
    if hasattr(resource, 'tenant_id'):
        if resource.tenant_id != tenant_id:
            raise ForbiddenException(f"No tienes acceso a este {resource_name.lower()}")

    return resource


def validate_user_in_tenant(
    db: Session,
    user_id: int,
    tenant_id: int
) -> Any:
    """
    Validate that a user belongs to the given tenant.

    Args:
        db: Database session
        user_id: User ID to check
        tenant_id: Tenant ID to validate against

    Returns:
        The user if valid

    Raises:
        NotFoundException: If user doesn't exist
        ForbiddenException: If user belongs to different tenant
    """
    from app.users.models import User

    user = db.query(User).filter(
        User.id == user_id,
        User.deleted_at.is_(None)
    ).first()

    if not user:
        raise NotFoundException("Usuario no encontrado")

    if user.tenant_id != tenant_id:
        raise ForbiddenException("El usuario no pertenece a este tenant")

    return user


def require_same_tenant(current_user_tenant_id: int, resource_tenant_id: int) -> None:
    """
    Validate that current user and resource are in the same tenant.

    Raises:
        ForbiddenException: If tenants don't match
    """
    if current_user_tenant_id != resource_tenant_id:
        raise ForbiddenException("No tienes acceso a este recurso")
