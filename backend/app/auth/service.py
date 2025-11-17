"""Auth business logic service."""

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.security import verify_password, hash_password, create_access_token, create_refresh_token
from app.core.exceptions import UnauthorizedException, ValidationException
from app.core.utils import generate_random_string
from app.auth.models import RefreshToken, PasswordResetToken, EmailVerificationToken
from app.users.models import User


class AuthService:
    """Authentication service."""

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> User | None:
        """Authenticate user by email and password."""
        user = db.query(User).filter(User.email == email, User.deleted_at.is_(None)).first()

        if not user or not verify_password(password, user.hashed_password):
            return None

        return user

    @staticmethod
    def create_tokens(db: Session, user: User) -> dict:
        """Create access and refresh tokens for user."""
        access_token_data = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
            "tenant_id": user.tenant_id
        }
        access_token = create_access_token(access_token_data)
        refresh_token = create_refresh_token({"sub": str(user.id)})

        expires_at = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)

        db_refresh_token = RefreshToken(
            token=refresh_token,
            user_id=user.id,
            expires_at=expires_at
        )
        db.add(db_refresh_token)
        db.commit()

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }

    @staticmethod
    def refresh_access_token(db: Session, refresh_token: str) -> str:
        """Generate new access token using refresh token."""
        db_token = db.query(RefreshToken).filter(RefreshToken.token == refresh_token).first()

        if not db_token or not db_token.is_valid:
            raise UnauthorizedException("Refresh token inválido o expirado")

        user = db_token.user
        access_token_data = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
            "tenant_id": user.tenant_id
        }

        return create_access_token(access_token_data)

    @staticmethod
    def revoke_refresh_token(db: Session, refresh_token: str) -> bool:
        """Revoke refresh token (logout)."""
        db_token = db.query(RefreshToken).filter(RefreshToken.token == refresh_token).first()

        if db_token:
            db_token.is_revoked = True
            db.commit()
            return True

        return False

    @staticmethod
    def create_password_reset_token(db: Session, email: str) -> PasswordResetToken:
        """Create password reset token."""
        user = db.query(User).filter(User.email == email, User.deleted_at.is_(None)).first()

        if not user:
            raise ValidationException("Si el email existe, recibirás instrucciones")

        token = generate_random_string(32)
        expires_at = datetime.utcnow() + timedelta(hours=1)

        reset_token = PasswordResetToken(
            token=token,
            user_id=user.id,
            expires_at=expires_at
        )
        db.add(reset_token)
        db.commit()
        db.refresh(reset_token)

        return reset_token

    @staticmethod
    def reset_password(db: Session, token: str, new_password: str) -> bool:
        """Reset password using token."""
        db_token = db.query(PasswordResetToken).filter(PasswordResetToken.token == token).first()

        if not db_token or not db_token.is_valid:
            raise ValidationException("Token inválido o expirado")

        user = db_token.user
        user.hashed_password = hash_password(new_password)
        db_token.is_used = True
        db.commit()

        return True

    @staticmethod
    def create_email_verification_token(db: Session, user_id: int) -> EmailVerificationToken:
        """Create email verification token."""
        token = generate_random_string(32)
        expires_at = datetime.utcnow() + timedelta(days=7)

        verification_token = EmailVerificationToken(
            token=token,
            user_id=user_id,
            expires_at=expires_at
        )
        db.add(verification_token)
        db.commit()
        db.refresh(verification_token)

        return verification_token

    @staticmethod
    def verify_email(db: Session, token: str) -> bool:
        """Verify email using token."""
        db_token = db.query(EmailVerificationToken).filter(EmailVerificationToken.token == token).first()

        if not db_token or not db_token.is_valid:
            raise ValidationException("Token de verificación inválido o expirado")

        user = db_token.user
        user.is_email_verified = True
        db_token.is_used = True
        db.commit()

        return True
