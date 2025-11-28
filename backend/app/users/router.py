"""
FastAPI router for Users module.
Provides endpoints for user management and invitations.
"""

from fastapi import APIRouter, Depends, status, UploadFile, File, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.schemas import SuccessResponse, PaginatedResponse
from app.core.enums import UserRole
from app.core.storage import storage_service
from app.core.exceptions import ValidationException
from app.auth.dependencies import get_current_user, get_current_active_user, require_any_role
from app.tenants.dependencies import get_current_tenant
from app.tenants.models import Tenant
from app.users import schemas
from app.users.models import User
from app.users.service import UserService
from app.users.dependencies import get_tenant_admin_user


router = APIRouter(prefix="/users", tags=["Users"])


# =============================================================================
# Current User Endpoints (/me)
# =============================================================================

@router.get("/me", response_model=schemas.UserResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user's profile.

    Returns the authenticated user's profile information.
    """
    return current_user


@router.patch("/me", response_model=schemas.UserResponse)
async def update_my_profile(
    data: schemas.UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update current user's profile.

    Allows users to update their own profile information.
    """
    user = UserService.update_user(db, current_user.id, data)
    return user


@router.post("/me/change-password", response_model=SuccessResponse)
async def change_my_password(
    data: schemas.ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Change current user's password.

    Requires current password verification.
    """
    UserService.change_password(
        db,
        current_user.id,
        data.current_password,
        data.new_password
    )
    return SuccessResponse(message="Contraseña actualizada exitosamente")


@router.post("/me/avatar", response_model=schemas.AvatarUploadResponse)
async def upload_my_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Upload avatar for current user.

    - Max file size: 2MB
    - Accepted formats: PNG, JPEG
    """
    # Validate file size
    file_data = await file.read()
    if len(file_data) > 2 * 1024 * 1024:  # 2MB
        raise ValidationException("El archivo es muy grande. Máximo 2MB")

    # Validate file type
    if file.content_type not in ["image/png", "image/jpeg"]:
        raise ValidationException("Formato no válido. Solo se aceptan PNG y JPEG")

    # Upload file
    filename = f"avatar_{current_user.id}_{file.filename}"
    url = await storage_service.upload_file(
        file_data,
        filename,
        folder=f"users/{current_user.id}/avatar",
        content_type=file.content_type
    )

    # Update user avatar
    UserService.update_avatar(db, current_user.id, url)

    return schemas.AvatarUploadResponse(url=url)


# =============================================================================
# Admin User Management Endpoints
# =============================================================================

@router.get("", response_model=PaginatedResponse[schemas.UserListResponse])
async def list_users(
    filters: schemas.UserFilterParams = Depends(),
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(require_any_role(UserRole.TENANT_ADMIN, UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    List users in the current tenant.

    - Requires TENANT_ADMIN or SUPER_ADMIN role
    - Supports filtering by search, role, status, and department
    - Returns paginated results
    """
    users, total = UserService.list_users(db, tenant.id, filters)

    return PaginatedResponse.create(
        data=users,
        total=total,
        page=filters.page,
        page_size=filters.page_size
    )


@router.get("/{user_id}", response_model=schemas.UserResponse)
async def get_user(
    user_id: int,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(require_any_role(UserRole.TENANT_ADMIN, UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Get user by ID.

    - Requires TENANT_ADMIN or SUPER_ADMIN role
    - User must belong to the current tenant (unless super admin)
    """
    user = UserService.get_user_by_id(db, user_id)

    # Validate tenant access
    if current_user.role != UserRole.SUPER_ADMIN.value:
        UserService.verify_user_in_tenant(user, tenant.id, allow_super_admin=False)

    return user


@router.patch("/{user_id}", response_model=schemas.UserResponse)
async def update_user(
    user_id: int,
    data: schemas.UserUpdateByAdmin,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(require_any_role(UserRole.TENANT_ADMIN, UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Update user by ID.

    - Requires TENANT_ADMIN or SUPER_ADMIN role
    - Admins can update email, role, and status
    - User must belong to current tenant (unless super admin)
    """
    user = UserService.get_user_by_id(db, user_id)

    # Validate tenant access
    if current_user.role != UserRole.SUPER_ADMIN.value:
        UserService.verify_user_in_tenant(user, tenant.id, allow_super_admin=False)

    updated_user = UserService.update_user(db, user_id, data)
    return updated_user


@router.delete("/{user_id}", response_model=SuccessResponse)
async def delete_user(
    user_id: int,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(require_any_role(UserRole.TENANT_ADMIN, UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Delete user (soft delete).

    - Requires TENANT_ADMIN or SUPER_ADMIN role
    - Cannot delete yourself
    - User must belong to current tenant (unless super admin)
    """
    user = UserService.get_user_by_id(db, user_id)

    # Validate tenant access
    if current_user.role != UserRole.SUPER_ADMIN.value:
        UserService.verify_user_in_tenant(user, tenant.id, allow_super_admin=False)

    UserService.delete_user(db, user_id, current_user.id)
    return SuccessResponse(message="Usuario eliminado exitosamente")


# =============================================================================
# Invitation Endpoints
# =============================================================================

@router.post("/invitations", response_model=schemas.UserInvitationResponse, status_code=status.HTTP_201_CREATED)
async def invite_user(
    data: schemas.InviteUserRequest,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(require_any_role(UserRole.TENANT_ADMIN, UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Invite a user to the tenant.

    - Requires TENANT_ADMIN or SUPER_ADMIN role
    - Sends invitation email (via notifications module)
    - Invitation expires in 7 days
    """
    invitation = UserService.create_invitation(
        db,
        tenant.id,
        current_user.id,
        data
    )

    # TODO: Send invitation email via notifications module
    # await notification_service.send_invitation_email(invitation)

    return invitation


@router.get("/invitations", response_model=list[schemas.UserInvitationResponse])
async def list_invitations(
    include_accepted: bool = Query(False, description="Include accepted invitations"),
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(require_any_role(UserRole.TENANT_ADMIN, UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    List invitations for the current tenant.

    - Requires TENANT_ADMIN or SUPER_ADMIN role
    - By default only shows pending invitations
    """
    invitations = UserService.list_invitations(db, tenant.id, include_accepted)
    return invitations


@router.post("/invitations/accept", response_model=schemas.UserResponse)
async def accept_invitation(
    data: schemas.AcceptInvitationRequest,
    db: Session = Depends(get_db)
):
    """
    Accept an invitation and create user account.

    - Public endpoint (no authentication required)
    - Token must be valid and not expired
    """
    user = UserService.accept_invitation(db, data)
    return user


@router.post("/invitations/{invitation_id}/resend", response_model=schemas.UserInvitationResponse)
async def resend_invitation(
    invitation_id: int,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(require_any_role(UserRole.TENANT_ADMIN, UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Resend an invitation (generates new token and extends expiry).

    - Requires TENANT_ADMIN or SUPER_ADMIN role
    - Cannot resend accepted invitations
    """
    invitation = UserService.resend_invitation(db, invitation_id, tenant.id)

    # TODO: Send invitation email via notifications module
    # await notification_service.send_invitation_email(invitation)

    return invitation


@router.delete("/invitations/{invitation_id}", response_model=SuccessResponse)
async def cancel_invitation(
    invitation_id: int,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(require_any_role(UserRole.TENANT_ADMIN, UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Cancel an invitation.

    - Requires TENANT_ADMIN or SUPER_ADMIN role
    - Cannot cancel accepted invitations
    """
    UserService.cancel_invitation(db, invitation_id, tenant.id)
    return SuccessResponse(message="Invitación cancelada exitosamente")
