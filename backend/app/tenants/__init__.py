"""
Tenants module initialization.
Exports commonly used components for easy imports.
"""

from app.tenants.models import Tenant, TenantBranding
from app.tenants.service import TenantService
from app.tenants.dependencies import get_current_tenant, get_optional_tenant
from app.tenants.router import router

__all__ = [
    # Models
    "Tenant",
    "TenantBranding",
    # Service
    "TenantService",
    # Dependencies
    "get_current_tenant",
    "get_optional_tenant",
    # Router
    "router",
]
