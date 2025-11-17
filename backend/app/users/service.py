"""
User service.
Business logic for user management, including CRUD, invitations, and profile management.
"""

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from app.core.security import hash_password, verify_password
from app.core.exceptions import (
    NotFoundException,
    AlreadyExistsException,
    ValidationException,
    ForbiddenException
)
from app.core.utils import generate_random_string
from app.users.models import User, UserInvitation
from app.users import schemas


class UserService:
    """Service for user management."""

    # =========================================================================
    # Basic CRUD Operations
    # =========================================================================

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> User:
        """Get user by ID."""
        user = db.query(User).filter(
            User.id == user_id,
            User.deleted_at.is_(None)
        ).first()

        if not user:
            raise NotFoundException("Usuario")

        return user

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> User | None:
        """Get user by email."""
        return db.query(User).filter(
            User.email == email,
            User.deleted_at.is_(None)
        ).first()

    @staticmethod
    def create_user(db: Session, data: schemas.UserCreate) -> User:
        """
        Create a new user.

        Args:
            db: Database session
            data: User creation data

        Returns:
            Created user

        Raises:
            AlreadyExistsException: If email already exists
            ValidationException: If tenant user limit reached
        """
        # Validate email is unique
        existing = UserService.get_user_by_email(db, data.email)
        if existing:
            raise AlreadyExistsException(f"Usuario con email '{data.email}'")

        # Validate tenant user limit
        from app.tenants.service import TenantService
        if not TenantService.check_user_limit(db, data.tenant_id):
            raise ValidationException("Límite de usuarios alcanzado para este tenant")

        # Hash password
        hashed_password = hash_password(data.password)

        # Create user
        user_data = data.model_dump(exclude={'password'})
        user = User(
            **user_data,
            hashed_password=hashed_password
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        return user

    @staticmethod
    def update_user(
        db: Session,
        user_id: int,
        data: schemas.UserUpdate | schemas.UserUpdateByAdmin
    ) -> User:
        """
        Update user.

        Args:
            db: Database session
            user_id: User ID to update
            data: Update data

        Returns:
            Updated user

        Raises:
            NotFoundException: If user not found
            AlreadyExistsException: If email already exists
        """
        user = UserService.get_user_by_id(db, user_id)

        # If updating email, validate it's unique
        if isinstance(data, schemas.UserUpdateByAdmin) and data.email:
            existing = UserService.get_user_by_email(db, data.email)
            if existing and existing.id != user_id:
                raise AlreadyExistsException(f"Usuario con email '{data.email}'")

        # Update fields
        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(user, field, value)

        db.commit()
        db.refresh(user)

        return user

    @staticmethod
    def delete_user(db: Session, user_id: int) -> bool:
        """
        Soft delete user.

        Args:
            db: Database session
            user_id: User ID to delete

        Returns:
            True if successful

        Raises:
            NotFoundException: If user not found
        """
        user = UserService.get_user_by_id(db, user_id)
        user.deleted_at = datetime.utcnow()
        user.is_active = False
        db.commit()

        return True

    # =========================================================================
    # Password Management
    # =========================================================================

    @staticmethod
    def change_password(
        db: Session,
        user_id: int,
        current_password: str,
        new_password: str
    ) -> bool:
        """
        Change user password.

        Args:
            db: Database session
            user_id: User ID
            current_password: Current password
            new_password: New password

        Returns:
            True if successful

        Raises:
            ValidationException: If current password is incorrect
            NotFoundException: If user not found
        """
        user = UserService.get_user_by_id(db, user_id)

        # Verify current password
        if not verify_password(current_password, user.hashed_password):
            raise ValidationException("Contraseña actual incorrecta")

        # Update password
        user.hashed_password = hash_password(new_password)
        db.commit()

        return True

    # =========================================================================
    # List and Search
    # =========================================================================

    @staticmethod
    def list_users(
        db: Session,
        tenant_id: int,
        filters: schemas.UserFilterParams
    ) -> tuple[list[User], int]:
        """
        List users of a tenant with filters and pagination.

        Args:
            db: Database session
            tenant_id: Tenant ID
            filters: Filter and pagination parameters

        Returns:
            Tuple of (users list, total count)
        """
        query = db.query(User).filter(
            User.tenant_id == tenant_id,
            User.deleted_at.is_(None)
        )

        # Apply filters
        if filters.search:
            search_term = f"%{filters.search}%"
            query = query.filter(
                or_(
                    User.email.ilike(search_term),
                    User.first_name.ilike(search_term),
                    User.last_name.ilike(search_term)
                )
            )

        if filters.role:
            query = query.filter(User.role == filters.role.value)

        if filters.is_active is not None:
            query = query.filter(User.is_active == filters.is_active)

        if filters.department:
            query = query.filter(User.department == filters.department)

        # Get total count
        total = query.count()

        # Apply pagination
        users = query.offset(filters.offset).limit(filters.page_size).all()

        return users, total

    # =========================================================================
    # User Invitations
    # =========================================================================

    @staticmethod
    def create_invitation(
        db: Session,
        tenant_id: int,
        inviter_id: int,
        data: schemas.InviteUserRequest
    ) -> UserInvitation:
        """
        Create user invitation.

        Args:
            db: Database session
            tenant_id: Tenant ID
            inviter_id: User ID of the inviter
            data: Invitation data

        Returns:
            Created invitation

        Raises:
            AlreadyExistsException: If email already exists or has pending invitation
            ValidationException: If tenant user limit reached
        """
        # Validate email doesn't exist
        existing_user = UserService.get_user_by_email(db, data.email)
        if existing_user:
            raise AlreadyExistsException(f"Usuario con email '{data.email}' ya existe")

        # Check for pending invitation
        existing_invitation = db.query(UserInvitation).filter(
            and_(
                UserInvitation.email == data.email,
                UserInvitation.tenant_id == tenant_id,
                UserInvitation.is_accepted == False
            )
        ).first()

        if existing_invitation and existing_invitation.is_valid:
            raise AlreadyExistsException("Ya existe una invitación pendiente para este email")

        # Validate tenant user limit
        from app.tenants.service import TenantService
        if not TenantService.check_user_limit(db, tenant_id):
            raise ValidationException("Límite de usuarios alcanzado")

        # Create invitation
        token = generate_random_string(32)
        expires_at = datetime.utcnow() + timedelta(days=7)  # 7 days

        invitation = UserInvitation(
            email=data.email,
            token=token,
            role=data.role.value,
            tenant_id=tenant_id,
            invited_by=inviter_id,
            expires_at=expires_at
        )

        db.add(invitation)
        db.commit()
        db.refresh(invitation)

        return invitation

    @staticmethod
    def accept_invitation(
        db: Session,
        token: str,
        data: schemas.AcceptInvitationRequest
    ) -> User:
        """
        Accept invitation and create user.

        Args:
            db: Database session
            token: Invitation token
            data: User data for creating account

        Returns:
            Created user

        Raises:
            ValidationException: If token is invalid or expired
        """
        # Find invitation
        invitation = db.query(UserInvitation).filter(
            UserInvitation.token == token
        ).first()

        if not invitation or not invitation.is_valid:
            raise ValidationException("Invitación inválida o expirada")

        # Create user
        user_data = schemas.UserCreate(
            email=invitation.email,
            password=data.password,
            first_name=data.first_name,
            last_name=data.last_name,
            role=UserRole(invitation.role) if isinstance(invitation.role, str) else invitation.role,
            tenant_id=invitation.tenant_id
        )

        user = UserService.create_user(db, user_data)

        # Mark invitation as accepted
        invitation.is_accepted = True
        invitation.accepted_at = datetime.utcnow()
        db.commit()

        return user

    @staticmethod
    def cancel_invitation(db: Session, invitation_id: int, tenant_id: int) -> bool:
        """
        Cancel invitation.

        Args:
            db: Database session
            invitation_id: Invitation ID
            tenant_id: Tenant ID (for validation)

        Returns:
            True if successful

        Raises:
            NotFoundException: If invitation not found
            ValidationException: If invitation already accepted
        """
        invitation = db.query(UserInvitation).filter(
            UserInvitation.id == invitation_id,
            UserInvitation.tenant_id == tenant_id
        ).first()

        if not invitation:
            raise NotFoundException("Invitación")

        if invitation.is_accepted:
            raise ValidationException("No se puede cancelar una invitación ya aceptada")

        db.delete(invitation)
        db.commit()

        return True

    @staticmethod
    def list_invitations(
        db: Session,
        tenant_id: int,
        include_accepted: bool = False
    ) -> list[UserInvitation]:
        """
        List invitations of a tenant.

        Args:
            db: Database session
            tenant_id: Tenant ID
            include_accepted: Whether to include accepted invitations

        Returns:
            List of invitations
        """
        query = db.query(UserInvitation).filter(
            UserInvitation.tenant_id == tenant_id
        )

        if not include_accepted:
            query = query.filter(UserInvitation.is_accepted == False)

        return query.order_by(UserInvitation.created_at.desc()).all()


# Import UserRole here to avoid circular import
from app.core.enums import UserRole
