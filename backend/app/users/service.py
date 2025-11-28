"""
User service for business logic operations.
Handles CRUD operations for users and invitations.
"""

from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.security import hash_password, verify_password
from app.core.utils import generate_random_string
from app.users.models import User, UserInvitation
from app.users import schemas
from app.users.exceptions import (
    UserNotFoundException,
    UserAlreadyExistsException,
    UserLimitReachedException,
    InvalidPasswordException,
    InvitationNotFoundException,
    InvitationExpiredException,
    InvitationAlreadyAcceptedException,
    PendingInvitationExistsException,
    CannotDeleteSelfException,
    UserNotInTenantException
)


class UserService:
    """Service class for user management operations."""

    # =========================================================================
    # User CRUD Operations
    # =========================================================================

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> User:
        """
        Get user by ID.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            User instance

        Raises:
            UserNotFoundException: If user not found
        """
        user = db.query(User).filter(
            User.id == user_id,
            User.deleted_at.is_(None)
        ).first()

        if not user:
            raise UserNotFoundException()

        return user

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> User | None:
        """
        Get user by email.

        Args:
            db: Database session
            email: User email

        Returns:
            User instance or None
        """
        return db.query(User).filter(
            User.email == email,
            User.deleted_at.is_(None)
        ).first()

    @staticmethod
    def create_user(
        db: Session,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        tenant_id: int,
        role: str = "employee",
        is_active: bool = True,
        check_limit: bool = True
    ) -> User:
        """
        Create a new user.

        Args:
            db: Database session
            email: User email
            password: Plain text password
            first_name: User's first name
            last_name: User's last name
            tenant_id: Tenant ID
            role: User role (default: employee)
            is_active: Whether user is active (default: True)
            check_limit: Whether to check tenant user limit

        Returns:
            Created User instance

        Raises:
            UserAlreadyExistsException: If email already exists
            UserLimitReachedException: If tenant user limit reached
        """
        # Check if email already exists
        existing_user = UserService.get_user_by_email(db, email)
        if existing_user:
            raise UserAlreadyExistsException(email)

        # Check tenant user limit
        if check_limit:
            from app.tenants.service import TenantService
            if not TenantService.check_user_limit(db, tenant_id):
                raise UserLimitReachedException()

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
    def create_user_from_schema(
        db: Session,
        data: schemas.UserCreate,
        check_limit: bool = True
    ) -> User:
        """
        Create a new user from schema.

        Args:
            db: Database session
            data: UserCreate schema
            check_limit: Whether to check tenant user limit

        Returns:
            Created User instance
        """
        return UserService.create_user(
            db=db,
            email=data.email,
            password=data.password,
            first_name=data.first_name,
            last_name=data.last_name,
            tenant_id=data.tenant_id,
            role=data.role.value if data.role else "employee",
            check_limit=check_limit
        )

    @staticmethod
    def update_user(
        db: Session,
        user_id: int,
        data: schemas.UserUpdate | schemas.UserUpdateByAdmin
    ) -> User:
        """
        Update user information.

        Args:
            db: Database session
            user_id: User ID
            data: Update data

        Returns:
            Updated User instance

        Raises:
            UserNotFoundException: If user not found
            UserAlreadyExistsException: If new email already exists
        """
        user = UserService.get_user_by_id(db, user_id)

        # If updating email, check it doesn't exist
        if isinstance(data, schemas.UserUpdateByAdmin) and data.email:
            existing = UserService.get_user_by_email(db, data.email)
            if existing and existing.id != user_id:
                raise UserAlreadyExistsException(data.email)

        # Update fields
        update_data = data.model_dump(exclude_unset=True)

        # Convert role enum to string if present
        if 'role' in update_data and update_data['role'] is not None:
            update_data['role'] = update_data['role'].value

        for field, value in update_data.items():
            setattr(user, field, value)

        db.commit()
        db.refresh(user)

        return user

    @staticmethod
    def delete_user(db: Session, user_id: int, current_user_id: int) -> bool:
        """
        Soft delete a user.

        Args:
            db: Database session
            user_id: User ID to delete
            current_user_id: ID of user performing deletion

        Returns:
            True if deleted successfully

        Raises:
            UserNotFoundException: If user not found
            CannotDeleteSelfException: If trying to delete self
        """
        if user_id == current_user_id:
            raise CannotDeleteSelfException()

        user = UserService.get_user_by_id(db, user_id)

        user.deleted_at = datetime.now(timezone.utc)
        user.is_active = False

        db.commit()

        return True

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
            True if password changed successfully

        Raises:
            UserNotFoundException: If user not found
            InvalidPasswordException: If current password is wrong
        """
        user = UserService.get_user_by_id(db, user_id)

        # Verify current password
        if not verify_password(current_password, user.hashed_password):
            raise InvalidPasswordException()

        # Update password
        user.hashed_password = hash_password(new_password)
        db.commit()

        return True

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
            filters: Filter parameters

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
        users = query.order_by(User.created_at.desc()).offset(
            filters.offset
        ).limit(filters.page_size).all()

        return users, total

    @staticmethod
    def update_avatar(db: Session, user_id: int, avatar_url: str) -> User:
        """
        Update user avatar URL.

        Args:
            db: Database session
            user_id: User ID
            avatar_url: New avatar URL

        Returns:
            Updated User instance
        """
        user = UserService.get_user_by_id(db, user_id)
        user.avatar_url = avatar_url
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def verify_user_in_tenant(
        user: User,
        tenant_id: int,
        allow_super_admin: bool = True
    ) -> bool:
        """
        Verify that a user belongs to a tenant.

        Args:
            user: User to verify
            tenant_id: Expected tenant ID
            allow_super_admin: If True, super admins can access any tenant

        Returns:
            True if user belongs to tenant

        Raises:
            UserNotInTenantException: If user doesn't belong to tenant
        """
        if allow_super_admin and user.is_super_admin:
            return True

        if user.tenant_id != tenant_id:
            raise UserNotInTenantException()

        return True

    # =========================================================================
    # Invitation Operations
    # =========================================================================

    @staticmethod
    def create_invitation(
        db: Session,
        tenant_id: int,
        inviter_id: int,
        data: schemas.InviteUserRequest
    ) -> UserInvitation:
        """
        Create a user invitation.

        Args:
            db: Database session
            tenant_id: Tenant ID
            inviter_id: ID of user creating invitation
            data: Invitation data

        Returns:
            Created UserInvitation instance

        Raises:
            UserAlreadyExistsException: If email already has an account
            PendingInvitationExistsException: If pending invitation exists
            UserLimitReachedException: If tenant user limit reached
        """
        # Check if user with email already exists
        existing_user = UserService.get_user_by_email(db, data.email)
        if existing_user:
            raise UserAlreadyExistsException(data.email)

        # Check for pending invitation
        existing_invitation = db.query(UserInvitation).filter(
            UserInvitation.email == data.email,
            UserInvitation.tenant_id == tenant_id,
            UserInvitation.is_accepted == False
        ).first()

        if existing_invitation and existing_invitation.is_valid:
            raise PendingInvitationExistsException(data.email)

        # Check tenant user limit
        from app.tenants.service import TenantService
        if not TenantService.check_user_limit(db, tenant_id):
            raise UserLimitReachedException()

        # Create invitation
        token = generate_random_string(32)

        invitation = UserInvitation(
            email=data.email,
            token=token,
            role=data.role.value if data.role else "employee",
            tenant_id=tenant_id,
            invited_by=inviter_id,
            expires_at=UserInvitation.default_expiry()
        )

        db.add(invitation)
        db.commit()
        db.refresh(invitation)

        return invitation

    @staticmethod
    def get_invitation_by_token(db: Session, token: str) -> UserInvitation:
        """
        Get invitation by token.

        Args:
            db: Database session
            token: Invitation token

        Returns:
            UserInvitation instance

        Raises:
            InvitationNotFoundException: If invitation not found
        """
        invitation = db.query(UserInvitation).filter(
            UserInvitation.token == token
        ).first()

        if not invitation:
            raise InvitationNotFoundException()

        return invitation

    @staticmethod
    def accept_invitation(
        db: Session,
        data: schemas.AcceptInvitationRequest
    ) -> User:
        """
        Accept an invitation and create user account.

        Args:
            db: Database session
            data: Accept invitation data

        Returns:
            Created User instance

        Raises:
            InvitationNotFoundException: If invitation not found
            InvitationExpiredException: If invitation expired
            InvitationAlreadyAcceptedException: If already accepted
        """
        invitation = UserService.get_invitation_by_token(db, data.token)

        if invitation.is_accepted:
            raise InvitationAlreadyAcceptedException()

        if invitation.is_expired:
            raise InvitationExpiredException()

        # Create user
        user = UserService.create_user(
            db=db,
            email=invitation.email,
            password=data.password,
            first_name=data.first_name,
            last_name=data.last_name,
            tenant_id=invitation.tenant_id,
            role=invitation.role,
            check_limit=False  # Already checked when invitation was created
        )

        # Mark invitation as accepted
        invitation.is_accepted = True
        invitation.accepted_at = datetime.now(timezone.utc)
        db.commit()

        return user

    @staticmethod
    def cancel_invitation(
        db: Session,
        invitation_id: int,
        tenant_id: int
    ) -> bool:
        """
        Cancel an invitation.

        Args:
            db: Database session
            invitation_id: Invitation ID
            tenant_id: Tenant ID (for validation)

        Returns:
            True if cancelled successfully

        Raises:
            InvitationNotFoundException: If invitation not found
            InvitationAlreadyAcceptedException: If already accepted
        """
        invitation = db.query(UserInvitation).filter(
            UserInvitation.id == invitation_id,
            UserInvitation.tenant_id == tenant_id
        ).first()

        if not invitation:
            raise InvitationNotFoundException()

        if invitation.is_accepted:
            raise InvitationAlreadyAcceptedException()

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
        List invitations for a tenant.

        Args:
            db: Database session
            tenant_id: Tenant ID
            include_accepted: Whether to include accepted invitations

        Returns:
            List of UserInvitation instances
        """
        query = db.query(UserInvitation).filter(
            UserInvitation.tenant_id == tenant_id
        )

        if not include_accepted:
            query = query.filter(UserInvitation.is_accepted == False)

        return query.order_by(UserInvitation.created_at.desc()).all()

    @staticmethod
    def resend_invitation(
        db: Session,
        invitation_id: int,
        tenant_id: int
    ) -> UserInvitation:
        """
        Resend an invitation (extends expiry).

        Args:
            db: Database session
            invitation_id: Invitation ID
            tenant_id: Tenant ID (for validation)

        Returns:
            Updated UserInvitation instance

        Raises:
            InvitationNotFoundException: If invitation not found
            InvitationAlreadyAcceptedException: If already accepted
        """
        invitation = db.query(UserInvitation).filter(
            UserInvitation.id == invitation_id,
            UserInvitation.tenant_id == tenant_id
        ).first()

        if not invitation:
            raise InvitationNotFoundException()

        if invitation.is_accepted:
            raise InvitationAlreadyAcceptedException()

        # Extend expiry
        invitation.expires_at = UserInvitation.default_expiry()
        invitation.token = generate_random_string(32)  # Generate new token

        db.commit()
        db.refresh(invitation)

        return invitation
