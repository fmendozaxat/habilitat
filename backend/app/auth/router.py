"""Auth API router."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.exceptions import UnauthorizedException, ValidationException
from app.auth.schemas import (
    LoginRequest,
    RegisterRequest,
    PasswordResetRequest,
    PasswordResetConfirm,
    UserAuthResponse,
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

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: RegisterRequest,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    Register a new user.

    Creates a new user account and returns authentication tokens.
    Email verification token is created but email sending is not implemented yet.
    """
    # Validate password strength is already done in schema

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

    # TODO: Send verification email
    # email_service.send_verification_email(user.email, verification_token.token)

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
        )
    )


@router.post("/login", response_model=LoginResponse)
async def login(
    data: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Login with email and password.

    Returns access token, refresh token, and user information.
    """
    user = AuthService.authenticate_user(db, data.email, data.password)

    if not user:
        raise UnauthorizedException("Email o contraseña incorrectos")

    if not user.is_active:
        raise UnauthorizedException("Usuario inactivo")

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
async def request_password_reset(
    data: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """
    Request password reset.

    Sends password reset email if user exists.
    Always returns success to prevent email enumeration.
    """
    try:
        reset_token = AuthService.create_password_reset_token(db, data.email)

        # TODO: Send password reset email
        # email_service.send_password_reset_email(data.email, reset_token.token)

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
async def resend_verification_email(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Resend email verification.

    Creates a new verification token and sends it to the user's email.
    """
    if current_user.is_email_verified:
        raise ValidationException("El email ya está verificado")

    verification_token = AuthService.create_email_verification_token(db, current_user.id)

    # TODO: Send verification email
    # email_service.send_verification_email(current_user.email, verification_token.token)

    return {"message": "Email de verificación enviado"}
