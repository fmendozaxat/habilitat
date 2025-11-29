"""
Tests for tenants router endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.users.models import User
from app.tenants.models import Tenant, TenantBranding


def create_super_admin(db: Session) -> tuple[User, Tenant]:
    """Helper to create a super admin user."""
    tenant = Tenant(name="Admin Tenant", slug="admin-tenant", plan="enterprise")
    db.add(tenant)
    db.commit()

    admin = User(
        email="superadmin@example.com",
        hashed_password=get_password_hash("TestPassword123!"),
        first_name="Super",
        last_name="Admin",
        tenant_id=tenant.id,
        role="super_admin",
        is_active=True
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    db.refresh(tenant)

    return admin, tenant


def create_tenant_admin(db: Session, tenant: Tenant) -> User:
    """Helper to create a tenant admin."""
    admin = User(
        email="tenantadmin@example.com",
        hashed_password=get_password_hash("TestPassword123!"),
        first_name="Tenant",
        last_name="Admin",
        tenant_id=tenant.id,
        role="tenant_admin",
        is_active=True
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


def get_auth_token(client: TestClient, email: str) -> str:
    """Helper to get authentication token."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "TestPassword123!"}
    )
    return response.json()["access_token"]


class TestTenantCRUD:
    """Tests for tenant CRUD operations."""

    def test_create_tenant_as_super_admin(self, client: TestClient, db: Session):
        """Test creating a tenant as super admin."""
        super_admin, _ = create_super_admin(db)
        token = get_auth_token(client, super_admin.email)

        response = client.post(
            "/api/v1/tenants",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "New Company",
                "slug": "new-company",
                "plan": "professional"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Company"
        assert data["slug"] == "new-company"
        assert data["plan"] == "professional"

    def test_create_tenant_as_tenant_admin_forbidden(self, client: TestClient, db: Session):
        """Test that tenant admin cannot create tenants."""
        tenant = Tenant(name="Test Tenant", slug="test-tenant", plan="professional")
        db.add(tenant)
        db.commit()

        admin = create_tenant_admin(db, tenant)
        token = get_auth_token(client, admin.email)

        response = client.post(
            "/api/v1/tenants",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "Another Company",
                "slug": "another-company",
                "plan": "starter"
            }
        )

        assert response.status_code == 403

    def test_list_tenants_as_super_admin(self, client: TestClient, db: Session):
        """Test listing all tenants as super admin."""
        super_admin, tenant1 = create_super_admin(db)

        # Create more tenants
        tenant2 = Tenant(name="Company 2", slug="company-2", plan="starter")
        tenant3 = Tenant(name="Company 3", slug="company-3", plan="professional")
        db.add_all([tenant2, tenant3])
        db.commit()

        token = get_auth_token(client, super_admin.email)

        response = client.get(
            "/api/v1/tenants",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 3

    def test_get_tenant_by_id(self, client: TestClient, db: Session):
        """Test getting a tenant by ID."""
        super_admin, tenant = create_super_admin(db)
        token = get_auth_token(client, super_admin.email)

        response = client.get(
            f"/api/v1/tenants/{tenant.id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == tenant.id
        assert data["name"] == tenant.name

    def test_update_tenant(self, client: TestClient, db: Session):
        """Test updating a tenant."""
        super_admin, tenant = create_super_admin(db)
        token = get_auth_token(client, super_admin.email)

        response = client.patch(
            f"/api/v1/tenants/{tenant.id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Updated Name", "plan": "enterprise"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["plan"] == "enterprise"

    def test_delete_tenant(self, client: TestClient, db: Session):
        """Test soft deleting a tenant."""
        super_admin, _ = create_super_admin(db)

        # Create tenant to delete
        tenant_to_delete = Tenant(name="Delete Me", slug="delete-me", plan="starter")
        db.add(tenant_to_delete)
        db.commit()

        token = get_auth_token(client, super_admin.email)

        response = client.delete(
            f"/api/v1/tenants/{tenant_to_delete.id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200

        # Verify soft delete
        db.refresh(tenant_to_delete)
        assert tenant_to_delete.deleted_at is not None


class TestTenantBranding:
    """Tests for tenant branding operations."""

    def test_get_current_tenant(self, client: TestClient, db: Session):
        """Test getting current tenant info."""
        tenant = Tenant(name="My Company", slug="my-company", plan="professional")
        db.add(tenant)
        db.commit()

        admin = create_tenant_admin(db, tenant)
        token = get_auth_token(client, admin.email)

        response = client.get(
            "/api/v1/tenants/current",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Tenant-ID": str(tenant.id)
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "My Company"

    def test_update_current_tenant_branding(self, client: TestClient, db: Session):
        """Test updating current tenant's branding."""
        tenant = Tenant(name="My Company", slug="my-company", plan="professional")
        db.add(tenant)
        db.commit()

        admin = create_tenant_admin(db, tenant)
        token = get_auth_token(client, admin.email)

        response = client.patch(
            "/api/v1/tenants/current",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Tenant-ID": str(tenant.id)
            },
            json={
                "name": "My Updated Company"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "My Updated Company"

    def test_get_tenant_stats(self, client: TestClient, db: Session):
        """Test getting tenant statistics."""
        tenant = Tenant(name="Stats Company", slug="stats-company", plan="professional")
        db.add(tenant)
        db.commit()

        # Add some users
        for i in range(3):
            user = User(
                email=f"user{i}@example.com",
                hashed_password=get_password_hash("TestPassword123!"),
                first_name=f"User{i}",
                last_name="Test",
                tenant_id=tenant.id,
                role="employee",
                is_active=True
            )
            db.add(user)

        admin = create_tenant_admin(db, tenant)
        db.commit()

        token = get_auth_token(client, admin.email)

        response = client.get(
            "/api/v1/tenants/current/stats",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Tenant-ID": str(tenant.id)
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_users"] >= 4  # 3 users + admin


class TestTenantSlug:
    """Tests for tenant slug operations."""

    def test_get_tenant_by_slug(self, client: TestClient, db: Session):
        """Test getting tenant by slug (public endpoint)."""
        tenant = Tenant(
            name="Public Company",
            slug="public-company",
            plan="professional",
            is_active=True
        )
        db.add(tenant)
        db.commit()

        response = client.get("/api/v1/tenants/by-slug/public-company")

        assert response.status_code == 200
        data = response.json()
        assert data["slug"] == "public-company"

    def test_get_tenant_by_slug_not_found(self, client: TestClient, db: Session):
        """Test getting nonexistent tenant by slug."""
        response = client.get("/api/v1/tenants/by-slug/nonexistent-slug")

        assert response.status_code == 404

    def test_duplicate_slug_fails(self, client: TestClient, db: Session):
        """Test that creating tenant with duplicate slug fails."""
        super_admin, _ = create_super_admin(db)

        # Create first tenant
        existing = Tenant(name="First", slug="duplicate-slug", plan="starter")
        db.add(existing)
        db.commit()

        token = get_auth_token(client, super_admin.email)

        # Try to create another with same slug
        response = client.post(
            "/api/v1/tenants",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "Second",
                "slug": "duplicate-slug",
                "plan": "starter"
            }
        )

        assert response.status_code in [400, 409, 422]  # Conflict or validation error
