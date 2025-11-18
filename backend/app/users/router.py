"""User API router."""

from fastapi import APIRouter, Depends, status, UploadFile, File, Query, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.schemas import SuccessResponse, PaginatedResponse
from app.core.enums import UserRole
from app.core.storage import storage_service
from app.core.exceptions import ForbiddenException, ValidationException
from app.users import schemas
from app.users.service import UserService
from app.users.models import User
from app.auth.dependencies import get_current_user, get_current_active_user, require_role, require_any_role
from app.tenants.models import Tenant
from app.tenants.dependencies import get_current_tenant
from app.notifications.service import NotificationService

router = APIRouter(prefix="/users", tags=["Users"])


# ============================================================================
# User Profile Endpoints (self-service)
# ============================================================================

@router.get("/me", response_model=schemas.UserResponse)
async def get_my_profile(current_user: User = Depends(get_current_active_user)):
    """
    Get current user profile.

    Returns the authenticated user's profile information.
    """
    return schemas.UserResponse(
        id=current_user.id,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        full_name=current_user.full_name,
        avatar_url=current_user.avatar_url,
        phone=current_user.phone,
        job_title=current_user.job_title,
        department=current_user.department,
        role=current_user.role,
        is_active=current_user.is_active,
        is_email_verified=current_user.is_email_verified,
        tenant_id=current_user.tenant_id,
        created_at=current_user.created_at.isoformat(),
        updated_at=current_user.updated_at.isoformat()
    )


@router.patch("/me", response_model=schemas.UserResponse)
async def update_my_profile(
    data: schemas.UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update current user profile.

    Users can update their own profile information including name, phone, job title, etc.
    """
    user = UserService.update_user(db, current_user.id, data)

    return schemas.UserResponse(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        full_name=user.full_name,
        avatar_url=user.avatar_url,
        phone=user.phone,
        job_title=user.job_title,
        department=user.department,
        role=user.role,
        is_active=user.is_active,
        is_email_verified=user.is_email_verified,
        tenant_id=user.tenant_id,
        created_at=user.created_at.isoformat(),
        updated_at=user.updated_at.isoformat()
    )


@router.post("/me/change-password", response_model=SuccessResponse)
async def change_my_password(
    data: schemas.ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Change current user password.

    Requires the current password for security validation.
    """
    UserService.change_password(
        db,
        current_user.id,
        data.current_password,
        data.new_password
    )

    return SuccessResponse(message="Contraseña actualizada exitosamente")


@router.post("/me/avatar", response_model=schemas.AvatarUploadResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Upload user avatar.

    - Max size: 2MB
    - Allowed formats: PNG, JPG, JPEG
    """
    # Read file data
    file_data = await file.read()

    # Validate file size (2MB max)
    if len(file_data) > 2 * 1024 * 1024:
        raise ValidationException("Archivo muy grande. Máximo 2MB")

    # Validate file type
    if file.content_type not in ["image/png", "image/jpeg", "image/jpg"]:
        raise ValidationException("Formato inválido. Solo PNG, JPG")

    # Upload to storage
    filename = f"avatar_{current_user.id}_{file.filename}"
    url = await storage_service.upload_file(
        file_data,
        filename,
        folder=f"users/{current_user.id}/avatar",
        content_type=file.content_type
    )

    # Update user avatar_url
    UserService.update_user(
        db,
        current_user.id,
        schemas.UserUpdate(avatar_url=url)
    )

    return schemas.AvatarUploadResponse(url=url)


# ============================================================================
# Admin User Management Endpoints
# ============================================================================

@router.get("", response_model=PaginatedResponse[schemas.UserListResponse])
async def list_users(
    filters: schemas.UserFilterParams = Depends(),
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(require_any_role(UserRole.TENANT_ADMIN, UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    List users of the tenant.

    Supports filtering by:
    - search: Search by name or email
    - role: Filter by role
    - is_active: Filter by active status
    - department: Filter by department

    Requires TENANT_ADMIN or SUPER_ADMIN role.
    """
    users, total = UserService.list_users(db, tenant.id, filters)

    user_responses = [
        schemas.UserListResponse(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            full_name=user.full_name,
            avatar_url=user.avatar_url,
            job_title=user.job_title,
            department=user.department,
            role=user.role,
            is_active=user.is_active
        )
        for user in users
    ]

    return PaginatedResponse(
        data=user_responses,
        total=total,
        page=filters.page,
        page_size=filters.page_size,
        total_pages=(total + filters.page_size - 1) // filters.page_size
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

    Requires TENANT_ADMIN or SUPER_ADMIN role.
    Users can only view users from their own tenant unless they are SUPER_ADMIN.
    """
    user = UserService.get_user_by_id(db, user_id)

    # Validate user belongs to tenant (unless super admin)
    if user.tenant_id != tenant.id and current_user.role != UserRole.SUPER_ADMIN.value:
        raise ForbiddenException("Este usuario no pertenece a tu organización")

    return schemas.UserResponse(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        full_name=user.full_name,
        avatar_url=user.avatar_url,
        phone=user.phone,
        job_title=user.job_title,
        department=user.department,
        role=user.role,
        is_active=user.is_active,
        is_email_verified=user.is_email_verified,
        tenant_id=user.tenant_id,
        created_at=user.created_at.isoformat(),
        updated_at=user.updated_at.isoformat()
    )


@router.patch("/{user_id}", response_model=schemas.UserResponse)
async def update_user(
    user_id: int,
    data: schemas.UserUpdateByAdmin,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(require_any_role(UserRole.TENANT_ADMIN, UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Update user by ID (admin).

    Allows admins to update any user field including email, role, and active status.
    Requires TENANT_ADMIN or SUPER_ADMIN role.
    """
    user = UserService.get_user_by_id(db, user_id)

    # Validate user belongs to tenant (unless super admin)
    if user.tenant_id != tenant.id and current_user.role != UserRole.SUPER_ADMIN.value:
        raise ForbiddenException("Este usuario no pertenece a tu organización")

    updated_user = UserService.update_user(db, user_id, data)

    return schemas.UserResponse(
        id=updated_user.id,
        email=updated_user.email,
        first_name=updated_user.first_name,
        last_name=updated_user.last_name,
        full_name=updated_user.full_name,
        avatar_url=updated_user.avatar_url,
        phone=updated_user.phone,
        job_title=updated_user.job_title,
        department=updated_user.department,
        role=updated_user.role,
        is_active=updated_user.is_active,
        is_email_verified=updated_user.is_email_verified,
        tenant_id=updated_user.tenant_id,
        created_at=updated_user.created_at.isoformat(),
        updated_at=updated_user.updated_at.isoformat()
    )


@router.delete("/{user_id}", response_model=SuccessResponse)
async def delete_user(
    user_id: int,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(require_any_role(UserRole.TENANT_ADMIN, UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Delete user (soft delete).

    Marks the user as deleted and inactive.
    Requires TENANT_ADMIN or SUPER_ADMIN role.
    Users cannot delete themselves.
    """
    user = UserService.get_user_by_id(db, user_id)

    # Validate user belongs to tenant (unless super admin)
    if user.tenant_id != tenant.id and current_user.role != UserRole.SUPER_ADMIN.value:
        raise ForbiddenException("Este usuario no pertenece a tu organización")

    # Prevent self-deletion
    if user.id == current_user.id:
        raise ValidationException("No puedes eliminarte a ti mismo")

    UserService.delete_user(db, user_id)

    return SuccessResponse(message="Usuario eliminado exitosamente")


# ============================================================================
# User Invitation Endpoints
# ============================================================================

@router.post("/invitations", response_model=schemas.UserInvitationResponse, status_code=status.HTTP_201_CREATED)
async def invite_user(
    data: schemas.InviteUserRequest,
    background_tasks: BackgroundTasks,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(require_any_role(UserRole.TENANT_ADMIN, UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Invite user to the tenant.

    Creates an invitation and sends an email to the invited user.
    Requires TENANT_ADMIN or SUPER_ADMIN role.
    """
    invitation = UserService.create_invitation(
        db,
        tenant.id,
        current_user.id,
        data
    )

    # Send invitation email in background
    background_tasks.add_task(
        NotificationService.send_invitation_email,
        db,
        invitation.email,
        invitation.token,
        current_user.full_name,
        tenant.id,
        tenant
    )

    return schemas.UserInvitationResponse(
        id=invitation.id,
        email=invitation.email,
        role=invitation.role,
        is_accepted=invitation.is_accepted,
        expires_at=invitation.expires_at.isoformat(),
        created_at=invitation.created_at.isoformat(),
        invited_by=invitation.invited_by
    )


@router.get("/invitations", response_model=list[schemas.UserInvitationResponse])
async def list_invitations(
    include_accepted: bool = Query(False, description="Include accepted invitations"),
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(require_any_role(UserRole.TENANT_ADMIN, UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    List tenant invitations.

    By default only shows pending invitations.
    Set include_accepted=true to see all invitations.
    Requires TENANT_ADMIN or SUPER_ADMIN role.
    """
    invitations = UserService.list_invitations(db, tenant.id, include_accepted)

    return [
        schemas.UserInvitationResponse(
            id=inv.id,
            email=inv.email,
            role=inv.role,
            is_accepted=inv.is_accepted,
            expires_at=inv.expires_at.isoformat(),
            created_at=inv.created_at.isoformat(),
            invited_by=inv.invited_by
        )
        for inv in invitations
    ]


@router.post("/invitations/accept", response_model=schemas.UserResponse)
async def accept_invitation(
    data: schemas.AcceptInvitationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Accept invitation and create user account.

    Public endpoint (no authentication required).
    Creates a new user account based on the invitation token.
    """
    user = UserService.accept_invitation(db, data.token, data)

    # Get tenant for welcome email
    tenant = db.query(Tenant).filter(Tenant.id == user.tenant_id).first()

    # Send welcome email in background
    if tenant:
        background_tasks.add_task(
            NotificationService.send_welcome_email,
            db,
            user.email,
            user.full_name,
            tenant.id,
            tenant,
            user.id
        )

    return schemas.UserResponse(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        full_name=user.full_name,
        avatar_url=user.avatar_url,
        phone=user.phone,
        job_title=user.job_title,
        department=user.department,
        role=user.role,
        is_active=user.is_active,
        is_email_verified=user.is_email_verified,
        tenant_id=user.tenant_id,
        created_at=user.created_at.isoformat(),
        updated_at=user.updated_at.isoformat()
    )


@router.delete("/invitations/{invitation_id}", response_model=SuccessResponse)
async def cancel_invitation(
    invitation_id: int,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(require_any_role(UserRole.TENANT_ADMIN, UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Cancel invitation.

    Deletes a pending invitation.
    Requires TENANT_ADMIN or SUPER_ADMIN role.
    Cannot cancel already accepted invitations.
    """
    UserService.cancel_invitation(db, invitation_id, tenant.id)

    return SuccessResponse(message="Invitación cancelada exitosamente")
