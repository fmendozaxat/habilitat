"""
Tests for tenant service module.
"""

import pytest
from sqlalchemy.orm import Session
from app.tenants.service import TenantService
from app.tenants.schemas import TenantCreate, TenantUpdate, TenantBrandingUpdate
from app.tenants.models import Tenant, TenantBranding
from app.core.exceptions import NotFoundException, AlreadyExistsException


class TestTenantService:
    """Tests for TenantService class."""

    def test_create_tenant(self, db: Session):
        """Test creating a new tenant."""
        data = TenantCreate(
            name="Test Company",
            slug="test-company",
            contact_email="test@example.com"
        )

        tenant = TenantService.create_tenant(db, data)

        assert tenant.id is not None
        assert tenant.name == "Test Company"
        assert tenant.slug == "test-company"
        assert tenant.contact_email == "test@example.com"
        assert tenant.is_active is True
        assert tenant.plan == "free"
        assert tenant.max_users == 10
        assert tenant.branding is not None  # Should create default branding

    def test_create_tenant_with_subdomain(self, db: Session):
        """Test creating tenant with subdomain."""
        data = TenantCreate(
            name="ACME Corporation",
            subdomain="acme"
        )

        tenant = TenantService.create_tenant(db, data)

        assert tenant.subdomain == "acme"
        assert tenant.slug == "acme-corporation"

    def test_create_tenant_duplicate_slug(self, db: Session):
        """Test creating tenant with duplicate slug raises error."""
        data1 = TenantCreate(name="Company One", slug="company")
        TenantService.create_tenant(db, data1)

        data2 = TenantCreate(name="Company Two", slug="company")

        with pytest.raises(AlreadyExistsException):
            TenantService.create_tenant(db, data2)

    def test_create_tenant_duplicate_subdomain(self, db: Session):
        """Test creating tenant with duplicate subdomain raises error."""
        data1 = TenantCreate(name="Company One", subdomain="acme")
        TenantService.create_tenant(db, data1)

        data2 = TenantCreate(name="Company Two", subdomain="acme")

        with pytest.raises(AlreadyExistsException):
            TenantService.create_tenant(db, data2)

    def test_get_tenant_by_id(self, db: Session):
        """Test getting tenant by ID."""
        data = TenantCreate(name="Test Company", slug="test")
        created = TenantService.create_tenant(db, data)

        retrieved = TenantService.get_tenant_by_id(db, created.id)

        assert retrieved.id == created.id
        assert retrieved.name == "Test Company"

    def test_get_tenant_by_id_not_found(self, db: Session):
        """Test getting non-existent tenant raises error."""
        with pytest.raises(NotFoundException):
            TenantService.get_tenant_by_id(db, 99999)

    def test_get_tenant_by_slug(self, db: Session):
        """Test getting tenant by slug."""
        data = TenantCreate(name="Test Company", slug="test-company")
        TenantService.create_tenant(db, data)

        tenant = TenantService.get_tenant_by_slug(db, "test-company")

        assert tenant is not None
        assert tenant.slug == "test-company"

    def test_get_tenant_by_subdomain(self, db: Session):
        """Test getting tenant by subdomain."""
        data = TenantCreate(name="Test Company", subdomain="testco")
        TenantService.create_tenant(db, data)

        tenant = TenantService.get_tenant_by_subdomain(db, "testco")

        assert tenant is not None
        assert tenant.subdomain == "testco"

    def test_update_tenant(self, db: Session):
        """Test updating tenant information."""
        data = TenantCreate(name="Original Name", slug="original")
        tenant = TenantService.create_tenant(db, data)

        update_data = TenantUpdate(
            name="Updated Name",
            contact_email="updated@example.com"
        )

        updated = TenantService.update_tenant(db, tenant.id, update_data)

        assert updated.name == "Updated Name"
        assert updated.contact_email == "updated@example.com"
        assert updated.slug == "original"  # Slug should not change

    def test_delete_tenant(self, db: Session):
        """Test soft deleting tenant."""
        data = TenantCreate(name="To Delete", slug="to-delete")
        tenant = TenantService.create_tenant(db, data)

        result = TenantService.delete_tenant(db, tenant.id)

        assert result is True

        # Tenant should be marked as deleted
        deleted_tenant = db.query(Tenant).filter(Tenant.id == tenant.id).first()
        assert deleted_tenant.deleted_at is not None
        assert deleted_tenant.is_active is False

        # Should not be able to get it with regular get method
        with pytest.raises(NotFoundException):
            TenantService.get_tenant_by_id(db, tenant.id)

    def test_list_tenants(self, db: Session):
        """Test listing tenants."""
        # Create multiple tenants
        for i in range(5):
            data = TenantCreate(name=f"Company {i}", slug=f"company-{i}")
            TenantService.create_tenant(db, data)

        tenants = TenantService.list_tenants(db, skip=0, limit=10)

        assert len(tenants) == 5

    def test_list_tenants_pagination(self, db: Session):
        """Test tenant list pagination."""
        # Create multiple tenants
        for i in range(5):
            data = TenantCreate(name=f"Company {i}", slug=f"company-{i}")
            TenantService.create_tenant(db, data)

        page1 = TenantService.list_tenants(db, skip=0, limit=2)
        page2 = TenantService.list_tenants(db, skip=2, limit=2)

        assert len(page1) == 2
        assert len(page2) == 2
        assert page1[0].id != page2[0].id

    def test_search_tenants(self, db: Session):
        """Test searching tenants."""
        data1 = TenantCreate(name="ACME Corporation", slug="acme")
        data2 = TenantCreate(name="Tech Solutions", slug="tech-sol")
        data3 = TenantCreate(name="ACME Tech", slug="acme-tech")

        TenantService.create_tenant(db, data1)
        TenantService.create_tenant(db, data2)
        TenantService.create_tenant(db, data3)

        results = TenantService.search_tenants(db, "ACME")

        assert len(results) == 2
        assert all("acme" in t.name.lower() for t in results)


class TestTenantBranding:
    """Tests for tenant branding operations."""

    def test_get_tenant_branding(self, db: Session):
        """Test getting tenant branding."""
        data = TenantCreate(name="Test Company", slug="test")
        tenant = TenantService.create_tenant(db, data)

        branding = TenantService.get_tenant_branding(db, tenant.id)

        assert branding is not None
        assert branding.tenant_id == tenant.id
        assert branding.primary_color == "#3B82F6"  # Default color

    def test_update_branding(self, db: Session):
        """Test updating tenant branding."""
        data = TenantCreate(name="Test Company", slug="test")
        tenant = TenantService.create_tenant(db, data)

        update_data = TenantBrandingUpdate(
            primary_color="#FF0000",
            secondary_color="#00FF00",
            logo_url="https://example.com/logo.png"
        )

        branding = TenantService.update_branding(db, tenant.id, update_data)

        assert branding.primary_color == "#FF0000"
        assert branding.secondary_color == "#00FF00"
        assert branding.logo_url == "https://example.com/logo.png"

    def test_branding_to_theme_dict(self, db: Session):
        """Test converting branding to theme dictionary."""
        data = TenantCreate(name="Test Company", slug="test")
        tenant = TenantService.create_tenant(db, data)

        branding = tenant.branding
        theme = branding.to_theme_dict()

        assert "colors" in theme
        assert "images" in theme
        assert "typography" in theme
        assert theme["colors"]["primary"] == "#3B82F6"


class TestTenantStats:
    """Tests for tenant statistics."""

    def test_get_tenant_stats(self, db: Session):
        """Test getting tenant statistics."""
        data = TenantCreate(name="Test Company", slug="test")
        tenant = TenantService.create_tenant(db, data)

        stats = TenantService.get_tenant_stats(db, tenant.id)

        assert "users_count" in stats
        assert "max_users" in stats
        assert "storage_used_mb" in stats
        assert "max_storage_mb" in stats
        assert "plan" in stats
        assert stats["plan"] == "free"
        assert stats["max_users"] == 10

    def test_check_user_limit(self, db: Session):
        """Test checking user limit."""
        data = TenantCreate(name="Test Company", slug="test")
        tenant = TenantService.create_tenant(db, data)

        # Should be able to add users (no users yet)
        can_add = TenantService.check_user_limit(db, tenant.id)

        assert can_add is True
