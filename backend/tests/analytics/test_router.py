"""
Tests for analytics router endpoints.
"""

import pytest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.core.enums import OnboardingStatus
from app.users.models import User
from app.tenants.models import Tenant
from app.onboarding.models import OnboardingFlow, OnboardingAssignment, OnboardingModule


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


class TestDashboard:
    """Tests for dashboard analytics."""

    def test_get_dashboard_overview(self, client: TestClient, db: Session):
        """Test getting dashboard overview."""
        tenant = create_test_tenant(db)
        admin = create_test_admin(db, tenant.id)

        # Create some data
        for i in range(3):
            create_test_employee(db, tenant.id, f"emp{i}@example.com")

        flow = OnboardingFlow(
            tenant_id=tenant.id,
            title="Test Flow",
            is_active=True
        )
        db.add(flow)
        db.commit()

        token = get_auth_token(client, admin.email)

        response = client.get(
            "/api/v1/analytics/dashboard",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Tenant-ID": str(tenant.id)
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "total_users" in data
        assert "total_flows" in data
        assert "total_assignments" in data
        assert data["total_users"] >= 4  # admin + 3 employees
        assert data["total_flows"] >= 1

    def test_dashboard_employee_forbidden(self, client: TestClient, db: Session):
        """Test that employees cannot access dashboard."""
        tenant = create_test_tenant(db)
        employee = create_test_employee(db, tenant.id)
        token = get_auth_token(client, employee.email)

        response = client.get(
            "/api/v1/analytics/dashboard",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Tenant-ID": str(tenant.id)
            }
        )

        assert response.status_code == 403


class TestFlowAnalytics:
    """Tests for flow-specific analytics."""

    def test_get_flow_analytics(self, client: TestClient, db: Session):
        """Test getting analytics for a specific flow."""
        tenant = create_test_tenant(db)
        admin = create_test_admin(db, tenant.id)

        flow = OnboardingFlow(
            tenant_id=tenant.id,
            title="Analytics Test Flow",
            is_active=True
        )
        db.add(flow)
        db.commit()

        # Create assignments with different statuses
        for i, status in enumerate([
            OnboardingStatus.NOT_STARTED.value,
            OnboardingStatus.IN_PROGRESS.value,
            OnboardingStatus.COMPLETED.value
        ]):
            emp = create_test_employee(db, tenant.id, f"emp{i}@example.com")
            assignment = OnboardingAssignment(
                flow_id=flow.id,
                user_id=emp.id,
                tenant_id=tenant.id,
                assigned_by=admin.id,
                status=status,
                assigned_at=datetime.now(timezone.utc)
            )
            if status == OnboardingStatus.COMPLETED.value:
                assignment.completed_at = datetime.now(timezone.utc)
            db.add(assignment)
        db.commit()

        token = get_auth_token(client, admin.email)

        response = client.get(
            f"/api/v1/analytics/flows/{flow.id}",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Tenant-ID": str(tenant.id)
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["flow_id"] == flow.id
        assert data["total_assignments"] == 3
        assert data["completed_assignments"] == 1
        assert data["in_progress_assignments"] == 1
        assert data["not_started_assignments"] == 1

    def test_get_all_flows_analytics(self, client: TestClient, db: Session):
        """Test getting analytics for all flows."""
        tenant = create_test_tenant(db)
        admin = create_test_admin(db, tenant.id)

        # Create multiple flows
        for i in range(3):
            flow = OnboardingFlow(
                tenant_id=tenant.id,
                title=f"Flow {i}",
                is_active=True
            )
            db.add(flow)
        db.commit()

        token = get_auth_token(client, admin.email)

        response = client.get(
            "/api/v1/analytics/flows",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Tenant-ID": str(tenant.id)
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "flows" in data
        assert len(data["flows"]) >= 3


class TestUserProgress:
    """Tests for user progress analytics."""

    def test_get_user_progress(self, client: TestClient, db: Session):
        """Test getting progress for a specific user."""
        tenant = create_test_tenant(db)
        admin = create_test_admin(db, tenant.id)
        employee = create_test_employee(db, tenant.id)

        flow = OnboardingFlow(
            tenant_id=tenant.id,
            title="Progress Test Flow",
            is_active=True
        )
        db.add(flow)
        db.commit()

        assignment = OnboardingAssignment(
            flow_id=flow.id,
            user_id=employee.id,
            tenant_id=tenant.id,
            assigned_by=admin.id,
            status=OnboardingStatus.IN_PROGRESS.value,
            completion_percentage=50,
            assigned_at=datetime.now(timezone.utc)
        )
        db.add(assignment)
        db.commit()

        token = get_auth_token(client, admin.email)

        response = client.get(
            f"/api/v1/analytics/users/{employee.id}/progress",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Tenant-ID": str(tenant.id)
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == employee.id
        assert data["total_assignments"] >= 1

    def test_get_my_progress(self, client: TestClient, db: Session):
        """Test getting own progress as employee."""
        tenant = create_test_tenant(db)
        admin = create_test_admin(db, tenant.id)
        employee = create_test_employee(db, tenant.id)

        flow = OnboardingFlow(
            tenant_id=tenant.id,
            title="My Progress Flow",
            is_active=True
        )
        db.add(flow)
        db.commit()

        assignment = OnboardingAssignment(
            flow_id=flow.id,
            user_id=employee.id,
            tenant_id=tenant.id,
            assigned_by=admin.id,
            status=OnboardingStatus.IN_PROGRESS.value,
            assigned_at=datetime.now(timezone.utc)
        )
        db.add(assignment)
        db.commit()

        token = get_auth_token(client, employee.email)

        response = client.get(
            "/api/v1/analytics/my-progress",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Tenant-ID": str(tenant.id)
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == employee.id

    def test_employee_cannot_view_others_progress(self, client: TestClient, db: Session):
        """Test that employee cannot view other's progress."""
        tenant = create_test_tenant(db)
        employee1 = create_test_employee(db, tenant.id, "emp1@example.com")
        employee2 = create_test_employee(db, tenant.id, "emp2@example.com")

        token = get_auth_token(client, employee1.email)

        response = client.get(
            f"/api/v1/analytics/users/{employee2.id}/progress",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Tenant-ID": str(tenant.id)
            }
        )

        assert response.status_code == 403


class TestCompletionTrends:
    """Tests for completion trends analytics."""

    def test_get_completion_trends(self, client: TestClient, db: Session):
        """Test getting completion trends."""
        tenant = create_test_tenant(db)
        admin = create_test_admin(db, tenant.id)

        token = get_auth_token(client, admin.email)

        response = client.get(
            "/api/v1/analytics/trends",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Tenant-ID": str(tenant.id)
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "trends" in data
        assert "total_completions" in data
        assert "total_new_assignments" in data

    def test_get_completion_trends_with_date_range(self, client: TestClient, db: Session):
        """Test getting completion trends with custom date range."""
        tenant = create_test_tenant(db)
        admin = create_test_admin(db, tenant.id)

        token = get_auth_token(client, admin.email)

        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        end_date = datetime.now().strftime("%Y-%m-%d")

        response = client.get(
            f"/api/v1/analytics/trends?start_date={start_date}&end_date={end_date}",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Tenant-ID": str(tenant.id)
            }
        )

        assert response.status_code == 200
        data = response.json()
        # Should have 8 days of data (inclusive)
        assert len(data["trends"]) == 8
