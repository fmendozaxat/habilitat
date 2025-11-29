"""
Tests for users router endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.users.models import User
from app.tenants.models import Tenant


def create_test_tenant(db: Session, name: str = "Test Tenant", slug: str = "test-tenant") -> Tenant:
    """Helper to create a test tenant."""
    tenant = Tenant(name=name, slug=slug, plan="professional")
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant


def create_test_user(
    db: Session,
    tenant_id: int,
    email: str = "test@example.com",
    role: str = "employee",
    is_active: bool = True
) -> User:
    """Helper to create a test user."""
    user = User(
        email=email,
        hashed_password=get_password_hash("TestPassword123!"),
        first_name="Test",
        last_name="User",
        tenant_id=tenant_id,
        role=role,
        is_active=is_active
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_auth_token(client: TestClient, email: str, password: str = "TestPassword123!") -> str:
    """Helper to get authentication token."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password}
    )
    return response.json()["access_token"]


class TestUserMe:
    """Tests for /users/me endpoints."""

    def test_get_my_profile(self, client: TestClient, db: Session):
        """Test getting own profile."""
        tenant = create_test_tenant(db)
        user = create_test_user(db, tenant.id)
        token = get_auth_token(client, user.email)

        response = client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == user.email
        assert data["first_name"] == "Test"

    def test_update_my_profile(self, client: TestClient, db: Session):
        """Test updating own profile."""
        tenant = create_test_tenant(db)
        user = create_test_user(db, tenant.id)
        token = get_auth_token(client, user.email)

        response = client.patch(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
            json={"first_name": "Updated", "department": "Engineering"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "Updated"
        assert data["department"] == "Engineering"

    def test_change_password(self, client: TestClient, db: Session):
        """Test changing own password."""
        tenant = create_test_tenant(db)
        user = create_test_user(db, tenant.id)
        token = get_auth_token(client, user.email)

        response = client.post(
            "/api/v1/users/me/change-password",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "current_password": "TestPassword123!",
                "new_password": "NewPassword456!"
            }
        )

        assert response.status_code == 200

        # Verify can login with new password
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": user.email, "password": "NewPassword456!"}
        )
        assert login_response.status_code == 200


class TestUserAdmin:
    """Tests for admin user management."""

    def test_list_users_as_admin(self, client: TestClient, db: Session):
        """Test listing users as admin."""
        tenant = create_test_tenant(db)
        admin = create_test_user(db, tenant.id, email="admin@example.com", role="tenant_admin")
        create_test_user(db, tenant.id, email="user1@example.com")
        create_test_user(db, tenant.id, email="user2@example.com")

        token = get_auth_token(client, admin.email)

        response = client.get(
            "/api/v1/users",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Tenant-ID": str(tenant.id)
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 3  # admin + 2 users

    def test_list_users_as_employee_forbidden(self, client: TestClient, db: Session):
        """Test that employees cannot list users."""
        tenant = create_test_tenant(db)
        user = create_test_user(db, tenant.id, role="employee")
        token = get_auth_token(client, user.email)

        response = client.get(
            "/api/v1/users",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Tenant-ID": str(tenant.id)
            }
        )

        assert response.status_code == 403

    def test_get_user_by_id(self, client: TestClient, db: Session):
        """Test getting a user by ID as admin."""
        tenant = create_test_tenant(db)
        admin = create_test_user(db, tenant.id, email="admin@example.com", role="tenant_admin")
        user = create_test_user(db, tenant.id, email="user@example.com")

        token = get_auth_token(client, admin.email)

        response = client.get(
            f"/api/v1/users/{user.id}",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Tenant-ID": str(tenant.id)
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user.id
        assert data["email"] == user.email

    def test_cannot_access_user_from_other_tenant(self, client: TestClient, db: Session):
        """Test that admin cannot access users from other tenants."""
        tenant1 = create_test_tenant(db, name="Tenant 1", slug="tenant-1")
        tenant2 = create_test_tenant(db, name="Tenant 2", slug="tenant-2")

        admin1 = create_test_user(db, tenant1.id, email="admin1@example.com", role="tenant_admin")
        user2 = create_test_user(db, tenant2.id, email="user2@example.com")

        token = get_auth_token(client, admin1.email)

        response = client.get(
            f"/api/v1/users/{user2.id}",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Tenant-ID": str(tenant1.id)
            }
        )

        # Should get 403 forbidden because user belongs to different tenant
        assert response.status_code == 403

    def test_delete_user(self, client: TestClient, db: Session):
        """Test deleting a user as admin."""
        tenant = create_test_tenant(db)
        admin = create_test_user(db, tenant.id, email="admin@example.com", role="tenant_admin")
        user = create_test_user(db, tenant.id, email="user@example.com")

        token = get_auth_token(client, admin.email)

        response = client.delete(
            f"/api/v1/users/{user.id}",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Tenant-ID": str(tenant.id)
            }
        )

        assert response.status_code == 200

        # Verify user is soft deleted
        db.refresh(user)
        assert user.deleted_at is not None
