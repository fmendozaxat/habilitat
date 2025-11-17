"""
Base models and mixins for all database models.
Provides common functionality like timestamps, soft deletes, and tenant scoping.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.ext.declarative import declared_attr
from app.core.database import Base


class TimestampMixin:
    """
    Mixin that adds timestamp fields to models.
    Automatically tracks creation and update times.
    """

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )


class TenantMixin:
    """
    Mixin that adds tenant_id for multitenant support.
    All models with this mixin are scoped to a specific tenant.
    """

    @declared_attr
    def tenant_id(cls):
        """Tenant ID foreign key."""
        return Column(
            Integer,
            nullable=False,
            index=True,
            comment="ID of the tenant this record belongs to"
        )


class SoftDeleteMixin:
    """
    Mixin that adds soft delete functionality.
    Records are marked as deleted instead of being physically removed.
    """

    deleted_at = Column(
        DateTime,
        nullable=True,
        default=None,
        index=True
    )

    @property
    def is_deleted(self) -> bool:
        """Check if the record is soft deleted."""
        return self.deleted_at is not None

    def soft_delete(self) -> None:
        """Mark record as deleted."""
        self.deleted_at = datetime.utcnow()

    def restore(self) -> None:
        """Restore a soft deleted record."""
        self.deleted_at = None


class BaseModel(Base):
    """
    Base model for all database models.
    Provides primary key and inherits from SQLAlchemy Base.
    """

    __abstract__ = True

    id = Column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True
    )


class BaseTenantModel(BaseModel, TimestampMixin, TenantMixin):
    """
    Base model for all tenant-scoped models.
    Includes ID, timestamps, and tenant_id.

    Use this for any model that should be scoped to a tenant.
    """

    __abstract__ = True


class BaseTenantSoftDeleteModel(BaseTenantModel, SoftDeleteMixin):
    """
    Base model for tenant-scoped models with soft delete.
    Includes ID, timestamps, tenant_id, and soft delete functionality.

    Use this for tenant-scoped models that should support soft deletion.
    """

    __abstract__ = True
