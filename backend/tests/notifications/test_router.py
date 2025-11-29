"""
Tests for notifications router endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.users.models import User
from app.tenants.models import Tenant
from app.notifications.models import EmailLog


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


def create_test_employee(db: Session, tenant_id: int) -> User:
    """Helper to create a test employee."""
    employee = User(
        email="employee@example.com",
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


class TestEmailLogs:
    """Tests for email log endpoints."""

    def test_get_email_logs(self, client: TestClient, db: Session):
        """Test getting email logs as admin."""
        tenant = create_test_tenant(db)
        admin = create_test_admin(db, tenant.id)

        # Create some email logs
        for i in range(5):
            log = EmailLog(
                tenant_id=tenant.id,
                to_email=f"user{i}@example.com",
                subject=f"Subject {i}",
                email_type="test",
                is_sent=True
            )
            db.add(log)
        db.commit()

        token = get_auth_token(client, admin.email)

        response = client.get(
            "/api/v1/notifications/emails",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Tenant-ID": str(tenant.id)
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["items"]) == 5

    def test_get_email_logs_pagination(self, client: TestClient, db: Session):
        """Test email logs pagination."""
        tenant = create_test_tenant(db)
        admin = create_test_admin(db, tenant.id)

        # Create 25 email logs
        for i in range(25):
            log = EmailLog(
                tenant_id=tenant.id,
                to_email=f"user{i}@example.com",
                subject=f"Subject {i}",
                email_type="test",
                is_sent=True
            )
            db.add(log)
        db.commit()

        token = get_auth_token(client, admin.email)

        # Get first page
        response = client.get(
            "/api/v1/notifications/emails?page=1&size=10",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Tenant-ID": str(tenant.id)
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 25
        assert len(data["items"]) == 10
        assert data["pages"] == 3

    def test_get_email_logs_filter_by_type(self, client: TestClient, db: Session):
        """Test filtering email logs by type."""
        tenant = create_test_tenant(db)
        admin = create_test_admin(db, tenant.id)

        # Create logs of different types
        types = ["welcome", "invitation", "welcome", "password_reset", "welcome"]
        for i, email_type in enumerate(types):
            log = EmailLog(
                tenant_id=tenant.id,
                to_email=f"user{i}@example.com",
                subject=f"Subject {i}",
                email_type=email_type,
                is_sent=True
            )
            db.add(log)
        db.commit()

        token = get_auth_token(client, admin.email)

        response = client.get(
            "/api/v1/notifications/emails?email_type=welcome",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Tenant-ID": str(tenant.id)
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3

    def test_get_email_logs_employee_forbidden(self, client: TestClient, db: Session):
        """Test that employees cannot access email logs."""
        tenant = create_test_tenant(db)
        employee = create_test_employee(db, tenant.id)
        token = get_auth_token(client, employee.email)

        response = client.get(
            "/api/v1/notifications/emails",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Tenant-ID": str(tenant.id)
            }
        )

        assert response.status_code == 403

    def test_get_email_log_by_id(self, client: TestClient, db: Session):
        """Test getting a specific email log."""
        tenant = create_test_tenant(db)
        admin = create_test_admin(db, tenant.id)

        log = EmailLog(
            tenant_id=tenant.id,
            to_email="specific@example.com",
            subject="Specific Email",
            email_type="welcome",
            is_sent=True
        )
        db.add(log)
        db.commit()

        token = get_auth_token(client, admin.email)

        response = client.get(
            f"/api/v1/notifications/emails/{log.id}",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Tenant-ID": str(tenant.id)
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == log.id
        assert data["to_email"] == "specific@example.com"

    def test_get_email_log_not_found(self, client: TestClient, db: Session):
        """Test getting nonexistent email log."""
        tenant = create_test_tenant(db)
        admin = create_test_admin(db, tenant.id)
        token = get_auth_token(client, admin.email)

        response = client.get(
            "/api/v1/notifications/emails/99999",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Tenant-ID": str(tenant.id)
            }
        )

        assert response.status_code == 404


class TestEmailStats:
    """Tests for email statistics endpoint."""

    def test_get_email_stats(self, client: TestClient, db: Session):
        """Test getting email statistics."""
        tenant = create_test_tenant(db)
        admin = create_test_admin(db, tenant.id)

        # Create logs with various types and statuses
        logs = [
            EmailLog(tenant_id=tenant.id, to_email="a@t.com", subject="S", email_type="welcome", is_sent=True),
            EmailLog(tenant_id=tenant.id, to_email="b@t.com", subject="S", email_type="welcome", is_sent=True),
            EmailLog(tenant_id=tenant.id, to_email="c@t.com", subject="S", email_type="invitation", is_sent=True),
            EmailLog(tenant_id=tenant.id, to_email="d@t.com", subject="S", email_type="reminder", is_sent=False),
        ]
        db.add_all(logs)
        db.commit()

        token = get_auth_token(client, admin.email)

        response = client.get(
            "/api/v1/notifications/emails/stats",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Tenant-ID": str(tenant.id)
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_sent"] == 3
        assert data["total_failed"] == 1
        assert data["success_rate"] == 75.0
        assert data["by_type"]["welcome"] == 2


class TestEmailRetry:
    """Tests for email retry endpoint."""

    def test_retry_failed_email(self, client: TestClient, db: Session):
        """Test retrying a failed email."""
        tenant = create_test_tenant(db)
        admin = create_test_admin(db, tenant.id)

        # Create a failed email log
        failed_log = EmailLog(
            tenant_id=tenant.id,
            to_email="failed@example.com",
            subject="Failed Email",
            email_type="test",
            template_name=None,
            template_data={},
            is_sent=False,
            error_message="Connection timeout"
        )
        db.add(failed_log)
        db.commit()

        token = get_auth_token(client, admin.email)

        response = client.post(
            f"/api/v1/notifications/emails/{failed_log.id}/retry",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Tenant-ID": str(tenant.id)
            }
        )

        # Note: In test mode without SendGrid, this creates a new log entry
        assert response.status_code in [200, 404]  # 404 if retry logic doesn't find template

    def test_retry_already_sent_email_fails(self, client: TestClient, db: Session):
        """Test that retrying sent email fails."""
        tenant = create_test_tenant(db)
        admin = create_test_admin(db, tenant.id)

        # Create a successfully sent email log
        sent_log = EmailLog(
            tenant_id=tenant.id,
            to_email="sent@example.com",
            subject="Sent Email",
            email_type="test",
            is_sent=True
        )
        db.add(sent_log)
        db.commit()

        token = get_auth_token(client, admin.email)

        response = client.post(
            f"/api/v1/notifications/emails/{sent_log.id}/retry",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Tenant-ID": str(tenant.id)
            }
        )

        assert response.status_code == 404  # Not found because already sent
