"""
FastAPI router for tenant endpoints.
Defines all HTTP endpoints for tenant and branding operations.
"""

from typing import List
from fastapi import APIRouter, Depends, status, UploadFile, File, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.schemas import SuccessResponse
from app.core.storage import storage_service
from app.core.exceptions import ValidationException
from app.core.constants import MAX_LOGO_SIZE, ALLOWED_IMAGE_TYPES
from app.tenants import schemas
from app.tenants.models import Tenant
from app.tenants.dependencies import get_current_tenant, get_optional_tenant
from app.tenants import service


router = APIRouter(prefix="/tenants", tags=["Tenants"])


# ============================================================================
# Tenant CRUD Endpoints
# ============================================================================

@router.post(
    "",
    response_model=schemas.TenantResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new tenant"
)
async def create_tenant(
    data: schemas.TenantCreate,
    db: Session = Depends(get_db),
    # TODO: Add authentication when auth module is ready
    # current_user: User = Depends(require_role(UserRole.SUPER_ADMIN))
):
    """
    Create a new tenant (organization).

    - **name**: Organization name (required)
    - **slug**: URL-friendly identifier (auto-generated if not provided)
    - **subdomain**: Subdomain for tenant access (optional)
    - **contact_email**: Contact email
    - **contact_phone**: Contact phone

    Note: Currently public for development. Will require SUPER_ADMIN role.
    """
    tenant = service.TenantService.create_tenant(db, data)
    return tenant


@router.get(
    "/me",
    response_model=schemas.TenantResponse,
    summary="Get current tenant"
)
async def get_my_tenant(
    tenant: Tenant = Depends(get_current_tenant),
    # TODO: Add authentication when auth module is ready
    # current_user: User = Depends(get_current_user)
):
    """
    Get information about the current tenant.

    Tenant is resolved from:
    1. Subdomain (e.g., acme.habilitat.com)
    2. X-Tenant-ID header
    3. Query parameter ?tenant=xxx (development only)
    """
    return tenant


@router.get(
    "",
    response_model=List[schemas.TenantListResponse],
    summary="List all tenants"
)
async def list_tenants(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    active_only: bool = True,
    db: Session = Depends(get_db),
    # TODO: Add authentication when auth module is ready
    # current_user: User = Depends(require_role(UserRole.SUPER_ADMIN))
):
    """
    List all tenants with pagination.

    - **skip**: Number of records to skip
    - **limit**: Maximum number of records to return
    - **active_only**: Filter by active tenants only

    Note: Will require SUPER_ADMIN role when auth is implemented.
    """
    tenants = service.TenantService.list_tenants(db, skip, limit, active_only)
    return tenants


@router.get(
    "/search",
    response_model=List[schemas.TenantListResponse],
    summary="Search tenants"
)
async def search_tenants(
    q: str = Query(..., min_length=2),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    # TODO: Add authentication when auth module is ready
    # current_user: User = Depends(require_role(UserRole.SUPER_ADMIN))
):
    """
    Search tenants by name, slug, or subdomain.

    - **q**: Search query (minimum 2 characters)
    - **skip**: Number of records to skip
    - **limit**: Maximum number of records to return

    Note: Will require SUPER_ADMIN role when auth is implemented.
    """
    tenants = service.TenantService.search_tenants(db, q, skip, limit)
    return tenants


@router.get(
    "/{tenant_id}",
    response_model=schemas.TenantResponse,
    summary="Get tenant by ID"
)
async def get_tenant(
    tenant_id: int,
    db: Session = Depends(get_db),
    # TODO: Add authentication when auth module is ready
    # current_user: User = Depends(require_role(UserRole.SUPER_ADMIN))
):
    """
    Get tenant by ID.

    Note: Will require SUPER_ADMIN role when auth is implemented.
    """
    tenant = service.TenantService.get_tenant_by_id(db, tenant_id)
    return tenant


@router.patch(
    "/{tenant_id}",
    response_model=schemas.TenantResponse,
    summary="Update tenant"
)
async def update_tenant(
    tenant_id: int,
    data: schemas.TenantUpdate,
    db: Session = Depends(get_db),
    # TODO: Add authentication and permission checks when auth module is ready
    # current_user: User = Depends(get_current_user)
):
    """
    Update tenant information.

    - SUPER_ADMIN can update any tenant
    - TENANT_ADMIN can only update their own tenant

    Note: Currently public for development.
    """
    tenant = service.TenantService.update_tenant(db, tenant_id, data)
    return tenant


@router.patch(
    "/{tenant_id}/plan",
    response_model=schemas.TenantResponse,
    summary="Update tenant plan"
)
async def update_tenant_plan(
    tenant_id: int,
    data: schemas.TenantPlanUpdate,
    db: Session = Depends(get_db),
    # TODO: Add authentication when auth module is ready
    # current_user: User = Depends(require_role(UserRole.SUPER_ADMIN))
):
    """
    Update tenant plan and limits.

    Note: Will require SUPER_ADMIN role when auth is implemented.
    """
    tenant = service.TenantService.update_tenant_plan(db, tenant_id, data)
    return tenant


@router.delete(
    "/{tenant_id}",
    response_model=SuccessResponse,
    summary="Delete tenant"
)
async def delete_tenant(
    tenant_id: int,
    db: Session = Depends(get_db),
    # TODO: Add authentication when auth module is ready
    # current_user: User = Depends(require_role(UserRole.SUPER_ADMIN))
):
    """
    Delete tenant (soft delete).

    This will mark the tenant as deleted but not remove it from database.

    Note: Will require SUPER_ADMIN role when auth is implemented.
    """
    service.TenantService.delete_tenant(db, tenant_id)
    return SuccessResponse(message="Tenant eliminado exitosamente")


# ============================================================================
# Branding Endpoints
# ============================================================================

@router.get(
    "/me/branding",
    response_model=schemas.TenantBrandingResponse,
    summary="Get current tenant branding"
)
async def get_my_tenant_branding(
    tenant: Tenant = Depends(get_current_tenant)
):
    """
    Get branding configuration for the current tenant.
    """
    return tenant.branding


@router.get(
    "/me/theme",
    response_model=schemas.TenantThemeResponse,
    summary="Get current tenant theme"
)
async def get_my_tenant_theme(
    tenant: Tenant | None = Depends(get_optional_tenant)
):
    """
    Get theme (simplified branding) for the current tenant.

    This endpoint is public and can be used by the frontend to style the application.
    Returns default theme if no tenant is resolved.
    """
    if not tenant or not tenant.branding:
        # Return default theme
        return {
            "logo": None,
            "logo_dark": None,
            "favicon": None,
            "colors": {
                "primary": "#3B82F6",
                "secondary": "#10B981",
                "accent": "#F59E0B",
                "background": "#FFFFFF",
                "text": "#1F2937"
            },
            "images": {
                "hero": None,
                "background": None
            },
            "typography": {
                "font_family": None
            }
        }

    return tenant.branding.to_theme_dict()


@router.patch(
    "/me/branding",
    response_model=schemas.TenantBrandingResponse,
    summary="Update current tenant branding"
)
async def update_my_tenant_branding(
    data: schemas.TenantBrandingUpdate,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db),
    # TODO: Add authentication when auth module is ready
    # current_user: User = Depends(require_role(UserRole.TENANT_ADMIN))
):
    """
    Update branding configuration for the current tenant.

    Note: Will require TENANT_ADMIN role when auth is implemented.
    """
    branding = service.TenantService.update_branding(db, tenant.id, data)
    return branding


@router.post(
    "/me/branding/logo",
    response_model=schemas.LogoUploadResponse,
    summary="Upload tenant logo"
)
async def upload_logo(
    file: UploadFile = File(...),
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db),
    # TODO: Add authentication when auth module is ready
    # current_user: User = Depends(require_role(UserRole.TENANT_ADMIN))
):
    """
    Upload logo for the current tenant.

    - **Max size:** 2MB
    - **Formats:** PNG, JPG, WebP

    Note: Will require TENANT_ADMIN role when auth is implemented.
    """
    # Read file data
    file_data = await file.read()

    # Validate file size
    if len(file_data) > MAX_LOGO_SIZE:
        raise ValidationException(
            f"Archivo muy grande. Máximo {MAX_LOGO_SIZE // (1024 * 1024)}MB"
        )

    # Validate content type
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise ValidationException(
            f"Formato inválido. Formatos permitidos: {', '.join(ALLOWED_IMAGE_TYPES)}"
        )

    # Upload to storage
    filename = f"logo_{tenant.id}_{file.filename}"
    url = await storage_service.upload_file(
        file_data,
        filename,
        folder=f"tenants/{tenant.id}/branding",
        content_type=file.content_type
    )

    # Update branding
    branding = service.TenantService.update_branding(
        db,
        tenant.id,
        schemas.TenantBrandingUpdate(logo_url=url)
    )

    return {"url": url}


@router.post(
    "/me/branding/images",
    response_model=schemas.ImageUploadResponse,
    summary="Upload tenant image"
)
async def upload_image(
    file: UploadFile = File(...),
    image_type: str = Query(..., description="Type: hero, background, favicon"),
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db),
    # TODO: Add authentication when auth module is ready
    # current_user: User = Depends(require_role(UserRole.TENANT_ADMIN))
):
    """
    Upload images for tenant branding.

    - **image_type**: Type of image (hero, background, favicon)
    - **Max size:** 5MB
    - **Formats:** PNG, JPG, WebP

    Note: Will require TENANT_ADMIN role when auth is implemented.
    """
    # Validate image type
    valid_types = ["hero", "background", "favicon"]
    if image_type not in valid_types:
        raise ValidationException(f"Tipo inválido. Tipos válidos: {', '.join(valid_types)}")

    # Read file data
    file_data = await file.read()

    # Validate file size (5MB for images)
    max_size = 5 * 1024 * 1024
    if len(file_data) > max_size:
        raise ValidationException("Archivo muy grande. Máximo 5MB")

    # Validate content type
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise ValidationException(
            f"Formato inválido. Formatos permitidos: {', '.join(ALLOWED_IMAGE_TYPES)}"
        )

    # Upload to storage
    filename = f"{image_type}_{tenant.id}_{file.filename}"
    url = await storage_service.upload_file(
        file_data,
        filename,
        folder=f"tenants/{tenant.id}/branding",
        content_type=file.content_type
    )

    # Update branding based on image type
    update_data = {}
    if image_type == "hero":
        update_data["hero_image_url"] = url
    elif image_type == "background":
        update_data["background_image_url"] = url
    elif image_type == "favicon":
        update_data["favicon_url"] = url

    branding = service.TenantService.update_branding(
        db,
        tenant.id,
        schemas.TenantBrandingUpdate(**update_data)
    )

    return {"url": url, "type": image_type}


# ============================================================================
# Tenant Statistics
# ============================================================================

@router.get(
    "/me/stats",
    response_model=schemas.TenantStatsResponse,
    summary="Get current tenant statistics"
)
async def get_my_tenant_stats(
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db),
    # TODO: Add authentication when auth module is ready
    # current_user: User = Depends(require_role(UserRole.TENANT_ADMIN))
):
    """
    Get statistics for the current tenant.

    Returns user count, storage usage, plan limits, etc.

    Note: Will require TENANT_ADMIN role when auth is implemented.
    """
    stats = service.TenantService.get_tenant_stats(db, tenant.id)
    return stats
