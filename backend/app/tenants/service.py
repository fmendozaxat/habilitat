"""
Business logic service for tenant operations.
Handles CRUD operations for tenants and branding.
"""

from datetime import datetime
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.core.exceptions import NotFoundException, AlreadyExistsException
from app.tenants.models import Tenant, TenantBranding
from app.tenants import schemas


class TenantService:
    """Service class for tenant management operations."""

    @staticmethod
    def get_tenant_by_id(db: Session, tenant_id: int) -> Tenant:
        """
        Get tenant by ID.

        Args:
            db: Database session
            tenant_id: Tenant ID

        Returns:
            Tenant model instance

        Raises:
            NotFoundException: If tenant not found
        """
        tenant = db.query(Tenant).filter(
            Tenant.id == tenant_id,
            Tenant.deleted_at.is_(None)
        ).first()

        if not tenant:
            raise NotFoundException("Tenant")

        return tenant

    @staticmethod
    def get_tenant_by_slug(db: Session, slug: str) -> Tenant | None:
        """
        Get tenant by slug.

        Args:
            db: Database session
            slug: Tenant slug

        Returns:
            Tenant model instance or None
        """
        return db.query(Tenant).filter(
            Tenant.slug == slug,
            Tenant.deleted_at.is_(None)
        ).first()

    @staticmethod
    def get_tenant_by_subdomain(db: Session, subdomain: str) -> Tenant | None:
        """
        Get tenant by subdomain.

        Args:
            db: Database session
            subdomain: Tenant subdomain

        Returns:
            Tenant model instance or None
        """
        return db.query(Tenant).filter(
            Tenant.subdomain == subdomain,
            Tenant.deleted_at.is_(None)
        ).first()

    @staticmethod
    def list_tenants(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True
    ) -> List[Tenant]:
        """
        List all tenants with pagination.

        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            active_only: If True, only return active tenants

        Returns:
            List of Tenant instances
        """
        query = db.query(Tenant).filter(Tenant.deleted_at.is_(None))

        if active_only:
            query = query.filter(Tenant.is_active == True)

        return query.offset(skip).limit(limit).all()

    @staticmethod
    def create_tenant(db: Session, data: schemas.TenantCreate) -> Tenant:
        """
        Create a new tenant with default branding.

        Args:
            db: Database session
            data: Tenant creation data

        Returns:
            Created Tenant instance

        Raises:
            AlreadyExistsException: If slug or subdomain already exists
        """
        # Validate that slug doesn't exist
        existing = TenantService.get_tenant_by_slug(db, data.slug)
        if existing:
            raise AlreadyExistsException(f"Tenant con slug '{data.slug}'")

        # Validate subdomain if provided
        if data.subdomain:
            existing = TenantService.get_tenant_by_subdomain(db, data.subdomain)
            if existing:
                raise AlreadyExistsException(f"Tenant con subdomain '{data.subdomain}'")

        # Create tenant
        tenant_data = data.model_dump()
        tenant = Tenant(**tenant_data)

        db.add(tenant)
        db.flush()  # Get the tenant ID

        # Create default branding
        branding = TenantBranding(tenant_id=tenant.id)
        db.add(branding)

        db.commit()
        db.refresh(tenant)

        return tenant

    @staticmethod
    def update_tenant(
        db: Session,
        tenant_id: int,
        data: schemas.TenantUpdate
    ) -> Tenant:
        """
        Update tenant information.

        Args:
            db: Database session
            tenant_id: Tenant ID to update
            data: Update data

        Returns:
            Updated Tenant instance

        Raises:
            NotFoundException: If tenant not found
        """
        tenant = TenantService.get_tenant_by_id(db, tenant_id)

        # Update only provided fields
        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(tenant, field, value)

        db.commit()
        db.refresh(tenant)

        return tenant

    @staticmethod
    def update_tenant_plan(
        db: Session,
        tenant_id: int,
        data: schemas.TenantPlanUpdate
    ) -> Tenant:
        """
        Update tenant plan and limits (admin only).

        Args:
            db: Database session
            tenant_id: Tenant ID to update
            data: Plan update data

        Returns:
            Updated Tenant instance

        Raises:
            NotFoundException: If tenant not found
        """
        tenant = TenantService.get_tenant_by_id(db, tenant_id)

        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(tenant, field, value)

        db.commit()
        db.refresh(tenant)

        return tenant

    @staticmethod
    def delete_tenant(db: Session, tenant_id: int) -> bool:
        """
        Soft delete a tenant.

        This marks the tenant as deleted but doesn't remove it from database.

        Args:
            db: Database session
            tenant_id: Tenant ID to delete

        Returns:
            True if deleted successfully

        Raises:
            NotFoundException: If tenant not found
        """
        tenant = TenantService.get_tenant_by_id(db, tenant_id)

        tenant.deleted_at = datetime.utcnow()
        tenant.is_active = False

        db.commit()

        return True

    @staticmethod
    def get_tenant_branding(db: Session, tenant_id: int) -> TenantBranding:
        """
        Get branding configuration for a tenant.

        Args:
            db: Database session
            tenant_id: Tenant ID

        Returns:
            TenantBranding instance

        Raises:
            NotFoundException: If branding not found
        """
        branding = db.query(TenantBranding).filter(
            TenantBranding.tenant_id == tenant_id
        ).first()

        if not branding:
            raise NotFoundException("Branding")

        return branding

    @staticmethod
    def update_branding(
        db: Session,
        tenant_id: int,
        data: schemas.TenantBrandingUpdate
    ) -> TenantBranding:
        """
        Update tenant branding configuration.

        Args:
            db: Database session
            tenant_id: Tenant ID
            data: Branding update data

        Returns:
            Updated TenantBranding instance

        Raises:
            NotFoundException: If branding not found
        """
        branding = TenantService.get_tenant_branding(db, tenant_id)

        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(branding, field, value)

        db.commit()
        db.refresh(branding)

        return branding

    @staticmethod
    def check_user_limit(db: Session, tenant_id: int) -> bool:
        """
        Check if tenant can add more users.

        Args:
            db: Database session
            tenant_id: Tenant ID

        Returns:
            True if can add more users, False otherwise

        Raises:
            NotFoundException: If tenant not found
        """
        from app.users.models import User

        tenant = TenantService.get_tenant_by_id(db, tenant_id)

        # Count active users in tenant
        current_user_count = db.query(User).filter(
            User.tenant_id == tenant_id,
            User.deleted_at.is_(None)
        ).count()

        return current_user_count < tenant.max_users

    @staticmethod
    def get_tenant_stats(db: Session, tenant_id: int) -> dict:
        """
        Get tenant statistics.

        Args:
            db: Database session
            tenant_id: Tenant ID

        Returns:
            Dictionary with tenant statistics

        Raises:
            NotFoundException: If tenant not found
        """
        from app.users.models import User

        tenant = TenantService.get_tenant_by_id(db, tenant_id)

        # Count active users
        users_count = db.query(User).filter(
            User.tenant_id == tenant_id,
            User.deleted_at.is_(None)
        ).count()

        # TODO: Calculate when modules are implemented
        onboarding_flows_count = 0  # len(tenant.onboarding_flows)
        storage_used_mb = 0.0  # Calculate from uploaded files

        return {
            "users_count": users_count,
            "max_users": tenant.max_users,
            "storage_used_mb": storage_used_mb,
            "max_storage_mb": tenant.max_storage_mb,
            "onboarding_flows_count": onboarding_flows_count,
            "is_active": tenant.is_active,
            "plan": tenant.plan
        }

    @staticmethod
    def search_tenants(
        db: Session,
        query: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Tenant]:
        """
        Search tenants by name, slug, or subdomain.

        Args:
            db: Database session
            query: Search query string
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of matching Tenant instances
        """
        search_term = f"%{query}%"

        return db.query(Tenant).filter(
            Tenant.deleted_at.is_(None),
            or_(
                Tenant.name.ilike(search_term),
                Tenant.slug.ilike(search_term),
                Tenant.subdomain.ilike(search_term)
            )
        ).offset(skip).limit(limit).all()
