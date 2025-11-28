"""
FastAPI dependencies for Users module.
Provides dependency functions for user and permission validation.
"""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.enums import UserRole
from app.core.exceptions import ForbiddenException
from app.auth.dependencies import get_current_user, get_current_active_user
from app.tenants.dependencies import get_current_tenant
from app.tenants.models import Tenant
from app.users.models import User
from app.users.service import UserService


async def get_user_from_path(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    tenant: Tenant = Depends(get_current_tenant)
) -> User:
    """
    Get user from path parameter and verify tenant access.

    Args:
        user_id: User ID from path
        db: Database session
        current_user: Current authenticated user
        tenant: Current tenant

    Returns:
        User instance

    Raises:
        UserNotFoundException: If user not found
        UserNotInTenantException: If user doesn't belong to tenant
    """
    user = UserService.get_user_by_id(db, user_id)

    # Super admins can access any user
    if current_user.role != UserRole.SUPER_ADMIN.value:
        # Verify user belongs to the current tenant
        UserService.verify_user_in_tenant(user, tenant.id, allow_super_admin=False)

    return user


def require_admin_for_user(target_user: User, current_user: User) -> None:
    """
    Verify current user has admin rights over target user.

    Args:
        target_user: User being accessed/modified
        current_user: Current authenticated user

    Raises:
        ForbiddenException: If current user doesn't have admin rights
    """
    # Super admins can manage anyone
    if current_user.role == UserRole.SUPER_ADMIN.value:
        return

    # Tenant admins can only manage users in their tenant
    if current_user.role == UserRole.TENANT_ADMIN.value:
        if target_user.tenant_id != current_user.tenant_id:
            raise ForbiddenException("No tienes permisos para gestionar este usuario")
        return

    # Regular users can only manage themselves
    if target_user.id != current_user.id:
        raise ForbiddenException("No tienes permisos para gestionar este usuario")


def require_same_tenant(
    target_user: User,
    current_user: User,
    allow_super_admin: bool = True
) -> None:
    """
    Verify users are in the same tenant.

    Args:
        target_user: Target user
        current_user: Current authenticated user
        allow_super_admin: Allow super admins to bypass check

    Raises:
        ForbiddenException: If users are in different tenants
    """
    if allow_super_admin and current_user.role == UserRole.SUPER_ADMIN.value:
        return

    if target_user.tenant_id != current_user.tenant_id:
        raise ForbiddenException("Este usuario no pertenece a tu organización")


async def get_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Dependency that requires user to be an admin (tenant or super).

    Args:
        current_user: Current authenticated user

    Returns:
        User instance if admin

    Raises:
        ForbiddenException: If user is not an admin
    """
    if current_user.role not in [UserRole.SUPER_ADMIN.value, UserRole.TENANT_ADMIN.value]:
        raise ForbiddenException("Se requiere rol de administrador")

    return current_user


async def get_tenant_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Dependency that requires user to be at least a tenant admin.

    Args:
        current_user: Current authenticated user

    Returns:
        User instance if tenant admin or higher

    Raises:
        ForbiddenException: If user is not at least tenant admin
    """
    if current_user.role not in [UserRole.SUPER_ADMIN.value, UserRole.TENANT_ADMIN.value]:
        raise ForbiddenException("Se requiere rol de administrador de tenant")

    return current_user


async def get_super_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Dependency that requires user to be a super admin.

    Args:
        current_user: Current authenticated user

    Returns:
        User instance if super admin

    Raises:
        ForbiddenException: If user is not super admin
    """
    if current_user.role != UserRole.SUPER_ADMIN.value:
        raise ForbiddenException("Se requiere rol de super administrador")

    return current_user
