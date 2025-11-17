"""
User service.
Basic user service for Auth module. Will be extended in Users module.
"""

from sqlalchemy.orm import Session
from app.core.security import hash_password
from app.core.exceptions import ValidationException
from app.users.models import User


class UserService:
    """User service for basic user operations."""

    @staticmethod
    def create_user(
        db: Session,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        tenant_id: int,
        role: str = "employee",
        is_active: bool = True
    ) -> User:
        """Create a new user."""
        # Check if email already exists
        existing_user = db.query(User).filter(
            User.email == email,
            User.deleted_at.is_(None)
        ).first()

        if existing_user:
            raise ValidationException("El email ya está registrado")

        # Create user
        user = User(
            email=email,
            hashed_password=hash_password(password),
            first_name=first_name,
            last_name=last_name,
            tenant_id=tenant_id,
            role=role,
            is_active=is_active,
            is_email_verified=False
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        return user

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> User | None:
        """Get user by ID."""
        return db.query(User).filter(
            User.id == user_id,
            User.deleted_at.is_(None)
        ).first()

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> User | None:
        """Get user by email."""
        return db.query(User).filter(
            User.email == email,
            User.deleted_at.is_(None)
        ).first()
