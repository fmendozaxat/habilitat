"""
FastAPI dependencies for tenant resolution.
Provides dependency functions to inject current tenant into endpoints.
"""

from fastapi import Depends, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.exceptions import TenantNotFoundException, TenantResolutionException
from app.tenants.models import Tenant
from app.tenants.service import TenantService


async def get_current_tenant(
    request: Request,
    db: Session = Depends(get_db)
) -> Tenant:
    """
    Dependency to resolve and get the current tenant from request.

    Resolution priority:
    1. request.state.tenant_identifier (set by TenantMiddleware)
    2. Header X-Tenant-ID
    3. Query parameter 'tenant' (development only)

    Args:
        request: FastAPI request object
        db: Database session

    Returns:
        Current Tenant instance

    Raises:
        TenantResolutionException: If tenant identifier cannot be resolved
        TenantNotFoundException: If tenant doesn't exist or is inactive

    Usage:
        @app.get("/endpoint")
        def my_endpoint(tenant: Tenant = Depends(get_current_tenant)):
            return tenant.name
    """
    # Get identifier from middleware (set by TenantMiddleware in core)
    tenant_identifier = getattr(request.state, 'tenant_identifier', None)

    if not tenant_identifier:
        # Fallback: try to get from header directly
        tenant_identifier = request.headers.get('X-Tenant-ID')

    if not tenant_identifier:
        raise TenantResolutionException()

    # Resolve tenant (can be ID, slug, or subdomain)
    tenant = None

    # Try as ID (if numeric)
    if tenant_identifier.isdigit():
        try:
            tenant_id = int(tenant_identifier)
            tenant = db.query(Tenant).filter(
                Tenant.id == tenant_id,
                Tenant.deleted_at.is_(None)
            ).first()
        except ValueError:
            pass

    # Try as subdomain
    if not tenant:
        tenant = TenantService.get_tenant_by_subdomain(db, tenant_identifier)

    # Try as slug
    if not tenant:
        tenant = TenantService.get_tenant_by_slug(db, tenant_identifier)

    if not tenant:
        raise TenantNotFoundException()

    # Check if tenant is active
    if not tenant.is_active:
        raise TenantResolutionException()

    return tenant


async def get_optional_tenant(
    request: Request,
    db: Session = Depends(get_db)
) -> Tenant | None:
    """
    Dependency for endpoints that may or may not have a tenant.

    Returns None if tenant cannot be resolved instead of raising exception.

    Args:
        request: FastAPI request object
        db: Database session

    Returns:
        Tenant instance or None

    Usage:
        @app.get("/endpoint")
        def my_endpoint(tenant: Tenant | None = Depends(get_optional_tenant)):
            if tenant:
                return f"Tenant: {tenant.name}"
            return "No tenant"
    """
    try:
        return await get_current_tenant(request, db)
    except (TenantResolutionException, TenantNotFoundException):
        return None


def get_tenant_from_id(tenant_id: int):
    """
    Factory function to create a dependency that gets a specific tenant by ID.

    Args:
        tenant_id: The tenant ID to fetch

    Returns:
        Dependency function that returns the tenant

    Usage:
        @app.get("/endpoint")
        def my_endpoint(tenant: Tenant = Depends(get_tenant_from_id(123))):
            return tenant.name
    """
    async def _get_tenant(db: Session = Depends(get_db)) -> Tenant:
        return TenantService.get_tenant_by_id(db, tenant_id)

    return _get_tenant


def get_tenant_from_slug(slug: str):
    """
    Factory function to create a dependency that gets a tenant by slug.

    Args:
        slug: The tenant slug to fetch

    Returns:
        Dependency function that returns the tenant

    Usage:
        @app.get("/endpoint")
        def my_endpoint(tenant: Tenant = Depends(get_tenant_from_slug("acme"))):
            return tenant.name
    """
    async def _get_tenant(db: Session = Depends(get_db)) -> Tenant:
        tenant = TenantService.get_tenant_by_slug(db, slug)
        if not tenant:
            raise TenantNotFoundException()
        return tenant

    return _get_tenant
