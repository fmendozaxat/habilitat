"""Auth API router."""

from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.exceptions import UnauthorizedException, ValidationException
from app.core.rate_limit import limiter, login_rate_limit, strict_rate_limit
from app.auth.schemas import (
    LoginRequest,
    RegisterRequest,
    PasswordResetRequest,
    PasswordResetConfirm,
    UserAuthResponse,
    TenantAuthResponse,
    LoginResponse,
    RefreshTokenRequest,
    RefreshTokenResponse
)
from app.auth.service import AuthService
from app.auth.dependencies import get_current_user, get_current_active_user
from app.users.service import UserService
from app.users.models import User
from app.tenants.dependencies import get_current_tenant
from app.tenants.models import Tenant
from app.tenants.service import TenantService
from app.notifications.email_service import EmailService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def register(
    request: Request,
    data: RegisterRequest,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    Register a new user.

    Creates a new user account and returns authentication tokens.
    Sends email verification.
    """
    # Create user
    user = UserService.create_user(
        db=db,
        email=data.email,
        password=data.password,
        first_name=data.first_name,
        last_name=data.last_name,
        tenant_id=tenant.id,
        role="employee"  # Default role for new registrations
    )

    # Create email verification token
    verification_token = AuthService.create_email_verification_token(db, user.id)

    # Send verification email
    EmailService.send_email_verification(
        db=db,
        to_email=user.email,
        user_name=user.full_name,
        verification_token=verification_token.token,
        tenant_id=tenant.id,
        user_id=user.id
    )

    # Create tokens
    tokens = AuthService.create_tokens(db, user)

    return LoginResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        expires_in=tokens["expires_in"],
        token_type="Bearer",
        user=UserAuthResponse(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            role=user.role,
            is_active=user.is_active,
            is_email_verified=user.is_email_verified,
            tenant_id=user.tenant_id,
            created_at=user.created_at.isoformat()
        ),
        tenant=TenantAuthResponse(
            id=tenant.id,
            name=tenant.name,
            slug=tenant.slug,
            plan=tenant.plan
        )
    )


@router.post("/login", response_model=LoginResponse)
@limiter.limit("5/minute")
async def login(
    request: Request,
    data: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Login with email and password.

    Returns access token, refresh token, and user information.
    Rate limited to 5 attempts per minute.
    """
    user = AuthService.authenticate_user(db, data.email, data.password)

    if not user:
        raise UnauthorizedException("Email o contraseña incorrectos")

    if not user.is_active:
        raise UnauthorizedException("Usuario inactivo")

    # Get user's tenant
    tenant = TenantService.get_tenant_by_id(db, user.tenant_id)

    tokens = AuthService.create_tokens(db, user)

    return LoginResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        expires_in=tokens["expires_in"],
        token_type="Bearer",
        user=UserAuthResponse(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            role=user.role,
            is_active=user.is_active,
            is_email_verified=user.is_email_verified,
            tenant_id=user.tenant_id,
            created_at=user.created_at.isoformat()
        ),
        tenant=TenantAuthResponse(
            id=tenant.id,
            name=tenant.name,
            slug=tenant.slug,
            plan=tenant.plan
        )
    )


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(
    data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token.

    Returns a new access token. Refresh token remains valid.
    """
    try:
        access_token = AuthService.refresh_access_token(db, data.refresh_token)

        return RefreshTokenResponse(
            access_token=access_token,
            token_type="Bearer",
            expires_in=1800  # 30 minutes in seconds
        )
    except Exception:
        raise UnauthorizedException("Refresh token inválido o expirado")


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    data: RefreshTokenRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Logout user by revoking refresh token.

    The access token will remain valid until it expires (short-lived).
    The refresh token will be revoked and cannot be used to get new access tokens.
    """
    AuthService.revoke_refresh_token(db, data.refresh_token)
    return None


@router.get("/me", response_model=UserAuthResponse)
async def get_me(current_user: User = Depends(get_current_active_user)):
    """
    Get current authenticated user information.

    Requires valid access token in Authorization header.
    """
    return UserAuthResponse(
        id=current_user.id,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        role=current_user.role,
        is_active=current_user.is_active,
        is_email_verified=current_user.is_email_verified,
        tenant_id=current_user.tenant_id,
        created_at=current_user.created_at.isoformat()
    )


@router.post("/password-reset/request", status_code=status.HTTP_202_ACCEPTED)
@limiter.limit("3/minute")
async def request_password_reset(
    request: Request,
    data: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """
    Request password reset.

    Sends password reset email if user exists.
    Always returns success to prevent email enumeration.
    Rate limited to 3 requests per minute.
    """
    try:
        reset_token = AuthService.create_password_reset_token(db, data.email)

        # Get user for name
        from app.users.models import User
        user = db.query(User).filter(User.email == data.email).first()
        if user and reset_token:
            EmailService.send_password_reset_email(
                db=db,
                to_email=data.email,
                user_name=user.full_name,
                reset_token=reset_token.token,
                tenant_id=user.tenant_id,
                user_id=user.id
            )

    except ValidationException:
        # Don't reveal if email exists or not
        pass

    return {
        "message": "Si el email existe, recibirás instrucciones para restablecer tu contraseña"
    }


@router.post("/password-reset/confirm", status_code=status.HTTP_200_OK)
async def confirm_password_reset(
    data: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """
    Confirm password reset with token.

    Resets the user's password using the token from the email.
    """
    AuthService.reset_password(db, data.token, data.new_password)

    return {"message": "Contraseña restablecida exitosamente"}


@router.post("/email/verify", status_code=status.HTTP_200_OK)
async def verify_email(
    token: str,
    db: Session = Depends(get_db)
):
    """
    Verify email address using verification token.

    Marks the user's email as verified.
    """
    AuthService.verify_email(db, token)

    return {"message": "Email verificado exitosamente"}


@router.post("/email/resend-verification", status_code=status.HTTP_202_ACCEPTED)
@limiter.limit("3/minute")
async def resend_verification_email(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Resend email verification.

    Creates a new verification token and sends it to the user's email.
    Rate limited to 3 requests per minute.
    """
    if current_user.is_email_verified:
        raise ValidationException("El email ya está verificado")

    verification_token = AuthService.create_email_verification_token(db, current_user.id)

    # Send verification email
    EmailService.send_email_verification(
        db=db,
        to_email=current_user.email,
        user_name=current_user.full_name,
        verification_token=verification_token.token,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id
    )

    return {"message": "Email de verificación enviado"}
