"""
Tests for auth router endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.users.models import User
from app.tenants.models import Tenant


class TestAuthLogin:
    """Tests for login endpoint."""

    def test_login_success(self, client: TestClient, db: Session):
        """Test successful login."""
        # Create tenant
        tenant = Tenant(
            name="Test Tenant",
            slug="test-tenant",
            plan="professional"
        )
        db.add(tenant)
        db.commit()

        # Create user
        user = User(
            email="test@example.com",
            hashed_password=get_password_hash("TestPassword123!"),
            first_name="Test",
            last_name="User",
            tenant_id=tenant.id,
            role="employee",
            is_active=True
        )
        db.add(user)
        db.commit()

        # Login
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "TestPassword123!"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "Bearer"
        assert data["user"]["email"] == "test@example.com"

    def test_login_invalid_password(self, client: TestClient, db: Session):
        """Test login with invalid password."""
        # Create tenant
        tenant = Tenant(
            name="Test Tenant",
            slug="test-tenant",
            plan="professional"
        )
        db.add(tenant)
        db.commit()

        # Create user
        user = User(
            email="test@example.com",
            hashed_password=get_password_hash("TestPassword123!"),
            first_name="Test",
            last_name="User",
            tenant_id=tenant.id,
            role="employee",
            is_active=True
        )
        db.add(user)
        db.commit()

        # Login with wrong password
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "WrongPassword123!"}
        )

        assert response.status_code == 401

    def test_login_nonexistent_user(self, client: TestClient, db: Session):
        """Test login with nonexistent user."""
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "nonexistent@example.com", "password": "TestPassword123!"}
        )

        assert response.status_code == 401

    def test_login_inactive_user(self, client: TestClient, db: Session):
        """Test login with inactive user."""
        # Create tenant
        tenant = Tenant(
            name="Test Tenant",
            slug="test-tenant",
            plan="professional"
        )
        db.add(tenant)
        db.commit()

        # Create inactive user
        user = User(
            email="test@example.com",
            hashed_password=get_password_hash("TestPassword123!"),
            first_name="Test",
            last_name="User",
            tenant_id=tenant.id,
            role="employee",
            is_active=False
        )
        db.add(user)
        db.commit()

        # Login
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "TestPassword123!"}
        )

        assert response.status_code == 401


class TestAuthMe:
    """Tests for /me endpoint."""

    def test_get_me_authenticated(self, client: TestClient, db: Session):
        """Test getting current user info."""
        # Create tenant
        tenant = Tenant(
            name="Test Tenant",
            slug="test-tenant",
            plan="professional"
        )
        db.add(tenant)
        db.commit()

        # Create user
        user = User(
            email="test@example.com",
            hashed_password=get_password_hash("TestPassword123!"),
            first_name="Test",
            last_name="User",
            tenant_id=tenant.id,
            role="employee",
            is_active=True
        )
        db.add(user)
        db.commit()

        # Login first
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "TestPassword123!"}
        )
        token = login_response.json()["access_token"]

        # Get /me
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["first_name"] == "Test"

    def test_get_me_unauthenticated(self, client: TestClient):
        """Test getting current user without authentication."""
        response = client.get("/api/v1/auth/me")

        assert response.status_code == 401


class TestAuthRefresh:
    """Tests for token refresh endpoint."""

    def test_refresh_token_success(self, client: TestClient, db: Session):
        """Test successful token refresh."""
        # Create tenant
        tenant = Tenant(
            name="Test Tenant",
            slug="test-tenant",
            plan="professional"
        )
        db.add(tenant)
        db.commit()

        # Create user
        user = User(
            email="test@example.com",
            hashed_password=get_password_hash("TestPassword123!"),
            first_name="Test",
            last_name="User",
            tenant_id=tenant.id,
            role="employee",
            is_active=True
        )
        db.add(user)
        db.commit()

        # Login first
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "TestPassword123!"}
        )
        refresh_token = login_response.json()["refresh_token"]

        # Refresh
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    def test_refresh_token_invalid(self, client: TestClient):
        """Test refresh with invalid token."""
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid-token"}
        )

        assert response.status_code == 401
