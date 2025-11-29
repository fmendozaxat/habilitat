"""
Tests for onboarding router endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.users.models import User
from app.tenants.models import Tenant
from app.onboarding.models import OnboardingFlow, OnboardingModule


def create_test_tenant(db: Session) -> Tenant:
    """Helper to create a test tenant."""
    tenant = Tenant(name="Test Tenant", slug="test-tenant", plan="professional")
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant


def create_test_admin(db: Session, tenant_id: int) -> User:
    """Helper to create a test admin."""
    admin = User(
        email="admin@example.com",
        hashed_password=get_password_hash("TestPassword123!"),
        first_name="Admin",
        last_name="User",
        tenant_id=tenant_id,
        role="tenant_admin",
        is_active=True
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


def create_test_employee(db: Session, tenant_id: int, email: str = "employee@example.com") -> User:
    """Helper to create a test employee."""
    employee = User(
        email=email,
        hashed_password=get_password_hash("TestPassword123!"),
        first_name="Employee",
        last_name="User",
        tenant_id=tenant_id,
        role="employee",
        is_active=True
    )
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee


def get_auth_token(client: TestClient, email: str) -> str:
    """Helper to get authentication token."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "TestPassword123!"}
    )
    return response.json()["access_token"]


class TestFlowCRUD:
    """Tests for flow CRUD operations."""

    def test_create_flow(self, client: TestClient, db: Session):
        """Test creating a new flow."""
        tenant = create_test_tenant(db)
        admin = create_test_admin(db, tenant.id)
        token = get_auth_token(client, admin.email)

        response = client.post(
            "/api/v1/onboarding/flows",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Tenant-ID": str(tenant.id)
            },
            json={
                "title": "New Employee Onboarding",
                "description": "Welcome process for new employees",
                "is_active": True
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "New Employee Onboarding"
        assert data["is_active"] is True

    def test_list_flows(self, client: TestClient, db: Session):
        """Test listing flows."""
        tenant = create_test_tenant(db)
        admin = create_test_admin(db, tenant.id)

        # Create some flows
        flow1 = OnboardingFlow(
            tenant_id=tenant.id,
            title="Flow 1",
            is_active=True
        )
        flow2 = OnboardingFlow(
            tenant_id=tenant.id,
            title="Flow 2",
            is_active=True
        )
        db.add_all([flow1, flow2])
        db.commit()

        token = get_auth_token(client, admin.email)

        response = client.get(
            "/api/v1/onboarding/flows",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Tenant-ID": str(tenant.id)
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2

    def test_get_flow(self, client: TestClient, db: Session):
        """Test getting a specific flow."""
        tenant = create_test_tenant(db)
        admin = create_test_admin(db, tenant.id)

        flow = OnboardingFlow(
            tenant_id=tenant.id,
            title="Test Flow",
            description="Test description",
            is_active=True
        )
        db.add(flow)
        db.commit()

        token = get_auth_token(client, admin.email)

        response = client.get(
            f"/api/v1/onboarding/flows/{flow.id}",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Tenant-ID": str(tenant.id)
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == flow.id
        assert data["title"] == "Test Flow"

    def test_cannot_access_flow_from_other_tenant(self, client: TestClient, db: Session):
        """Test that flows from other tenants are not accessible."""
        tenant1 = Tenant(name="Tenant 1", slug="tenant-1", plan="professional")
        tenant2 = Tenant(name="Tenant 2", slug="tenant-2", plan="professional")
        db.add_all([tenant1, tenant2])
        db.commit()

        admin1 = create_test_admin(db, tenant1.id)

        # Create flow in tenant2
        flow = OnboardingFlow(
            tenant_id=tenant2.id,
            title="Flow in Tenant 2",
            is_active=True
        )
        db.add(flow)
        db.commit()

        token = get_auth_token(client, admin1.email)

        # Try to access flow from tenant1
        response = client.get(
            f"/api/v1/onboarding/flows/{flow.id}",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Tenant-ID": str(tenant1.id)
            }
        )

        assert response.status_code == 404

    def test_update_flow(self, client: TestClient, db: Session):
        """Test updating a flow."""
        tenant = create_test_tenant(db)
        admin = create_test_admin(db, tenant.id)

        flow = OnboardingFlow(
            tenant_id=tenant.id,
            title="Original Title",
            is_active=True
        )
        db.add(flow)
        db.commit()

        token = get_auth_token(client, admin.email)

        response = client.patch(
            f"/api/v1/onboarding/flows/{flow.id}",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Tenant-ID": str(tenant.id)
            },
            json={"title": "Updated Title"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"

    def test_delete_flow(self, client: TestClient, db: Session):
        """Test soft deleting a flow."""
        tenant = create_test_tenant(db)
        admin = create_test_admin(db, tenant.id)

        flow = OnboardingFlow(
            tenant_id=tenant.id,
            title="Flow to Delete",
            is_active=True
        )
        db.add(flow)
        db.commit()

        token = get_auth_token(client, admin.email)

        response = client.delete(
            f"/api/v1/onboarding/flows/{flow.id}",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Tenant-ID": str(tenant.id)
            }
        )

        assert response.status_code == 200

        # Verify soft delete
        db.refresh(flow)
        assert flow.deleted_at is not None
        assert flow.is_active is False


class TestModuleCRUD:
    """Tests for module CRUD operations."""

    def test_create_module(self, client: TestClient, db: Session):
        """Test creating a module in a flow."""
        tenant = create_test_tenant(db)
        admin = create_test_admin(db, tenant.id)

        flow = OnboardingFlow(
            tenant_id=tenant.id,
            title="Test Flow",
            is_active=True
        )
        db.add(flow)
        db.commit()

        token = get_auth_token(client, admin.email)

        response = client.post(
            f"/api/v1/onboarding/flows/{flow.id}/modules",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Tenant-ID": str(tenant.id)
            },
            json={
                "title": "Welcome Module",
                "description": "Introduction to the company",
                "content_type": "text",
                "content_text": "Welcome to our company!",
                "order": 1,
                "is_required": True
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Welcome Module"
        assert data["content_type"] == "text"


class TestAssignments:
    """Tests for assignment operations."""

    def test_assign_flow_to_user(self, client: TestClient, db: Session):
        """Test assigning a flow to a user."""
        tenant = create_test_tenant(db)
        admin = create_test_admin(db, tenant.id)
        employee = create_test_employee(db, tenant.id)

        flow = OnboardingFlow(
            tenant_id=tenant.id,
            title="Onboarding Flow",
            is_active=True
        )
        db.add(flow)
        db.commit()

        token = get_auth_token(client, admin.email)

        response = client.post(
            "/api/v1/onboarding/assignments",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Tenant-ID": str(tenant.id)
            },
            json={
                "flow_id": flow.id,
                "user_id": employee.id
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["flow_id"] == flow.id
        assert data["user_id"] == employee.id
        assert data["status"] == "not_started"

    def test_employee_can_view_own_assignments(self, client: TestClient, db: Session):
        """Test that employee can view their own assignments."""
        tenant = create_test_tenant(db)
        admin = create_test_admin(db, tenant.id)
        employee = create_test_employee(db, tenant.id)

        flow = OnboardingFlow(
            tenant_id=tenant.id,
            title="Test Flow",
            is_active=True
        )
        db.add(flow)
        db.commit()

        # Admin assigns flow
        admin_token = get_auth_token(client, admin.email)
        client.post(
            "/api/v1/onboarding/assignments",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "X-Tenant-ID": str(tenant.id)
            },
            json={"flow_id": flow.id, "user_id": employee.id}
        )

        # Employee views their assignments
        employee_token = get_auth_token(client, employee.email)
        response = client.get(
            "/api/v1/onboarding/my-assignments",
            headers={
                "Authorization": f"Bearer {employee_token}",
                "X-Tenant-ID": str(tenant.id)
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
