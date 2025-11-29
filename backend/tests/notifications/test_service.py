"""
Tests for notifications service.
"""

import pytest
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.users.models import User
from app.tenants.models import Tenant
from app.notifications.models import EmailLog
from app.notifications.email_service import EmailService
from app.notifications.service import NotificationService


def create_test_tenant(db: Session) -> Tenant:
    """Helper to create a test tenant."""
    tenant = Tenant(name="Test Tenant", slug="test-tenant", plan="professional")
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant


def create_test_user(db: Session, tenant_id: int) -> User:
    """Helper to create a test user."""
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("TestPassword123!"),
        first_name="Test",
        last_name="User",
        tenant_id=tenant_id,
        role="employee",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


class TestEmailService:
    """Tests for email service."""

    def test_send_email_logs_to_database(self, db: Session):
        """Test that sending email creates a log entry."""
        tenant = create_test_tenant(db)

        email_log = EmailService.send_email(
            db=db,
            to_email="recipient@example.com",
            subject="Test Subject",
            email_type="test",
            template_name=None,
            template_data={},
            to_name="Recipient",
            tenant_id=tenant.id,
            html_content="<p>Test content</p>"
        )

        assert email_log is not None
        assert email_log.to_email == "recipient@example.com"
        assert email_log.subject == "Test Subject"
        assert email_log.email_type == "test"
        assert email_log.tenant_id == tenant.id

    def test_send_welcome_email(self, db: Session):
        """Test sending welcome email."""
        tenant = create_test_tenant(db)
        user = create_test_user(db, tenant.id)

        email_log = EmailService.send_welcome_email(
            db=db,
            user_email=user.email,
            user_name=user.full_name,
            tenant_name=tenant.name,
            login_url="https://example.com/login",
            tenant_id=tenant.id,
            user_id=user.id
        )

        assert email_log is not None
        assert email_log.email_type == "welcome"
        assert email_log.to_email == user.email
        assert email_log.user_id == user.id

    def test_send_invitation_email(self, db: Session):
        """Test sending invitation email."""
        tenant = create_test_tenant(db)
        from datetime import datetime, timedelta, timezone

        email_log = EmailService.send_invitation_email(
            db=db,
            to_email="newuser@example.com",
            inviter_name="Admin User",
            tenant_name=tenant.name,
            invitation_token="test-token-123",
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            tenant_id=tenant.id
        )

        assert email_log is not None
        assert email_log.email_type == "invitation"
        assert email_log.to_email == "newuser@example.com"

    def test_send_password_reset_email(self, db: Session):
        """Test sending password reset email."""
        tenant = create_test_tenant(db)
        user = create_test_user(db, tenant.id)

        email_log = EmailService.send_password_reset_email(
            db=db,
            to_email=user.email,
            user_name=user.full_name,
            reset_token="reset-token-456",
            tenant_id=tenant.id,
            user_id=user.id
        )

        assert email_log is not None
        assert email_log.email_type == "password_reset"
        assert email_log.to_email == user.email

    def test_send_assignment_notification(self, db: Session):
        """Test sending assignment notification."""
        tenant = create_test_tenant(db)
        user = create_test_user(db, tenant.id)
        from datetime import datetime, timedelta, timezone

        email_log = EmailService.send_assignment_notification(
            db=db,
            to_email=user.email,
            user_name=user.full_name,
            flow_title="New Employee Onboarding",
            due_date=datetime.now(timezone.utc) + timedelta(days=14),
            tenant_name=tenant.name,
            assignment_url="https://example.com/assignment/1",
            tenant_id=tenant.id,
            user_id=user.id
        )

        assert email_log is not None
        assert email_log.email_type == "assignment"

    def test_send_completion_notification(self, db: Session):
        """Test sending completion notification."""
        tenant = create_test_tenant(db)
        user = create_test_user(db, tenant.id)
        from datetime import datetime, timezone

        email_log = EmailService.send_completion_notification(
            db=db,
            to_email=user.email,
            user_name=user.full_name,
            flow_title="New Employee Onboarding",
            completion_date=datetime.now(timezone.utc),
            tenant_name=tenant.name,
            tenant_id=tenant.id,
            user_id=user.id
        )

        assert email_log is not None
        assert email_log.email_type == "completion"

    def test_send_reminder_email(self, db: Session):
        """Test sending reminder email."""
        tenant = create_test_tenant(db)
        user = create_test_user(db, tenant.id)
        from datetime import datetime, timedelta, timezone

        email_log = EmailService.send_reminder_email(
            db=db,
            to_email=user.email,
            user_name=user.full_name,
            flow_title="Pending Onboarding",
            due_date=datetime.now(timezone.utc) + timedelta(days=3),
            progress_percentage=50,
            assignment_url="https://example.com/assignment/1",
            tenant_id=tenant.id,
            user_id=user.id
        )

        assert email_log is not None
        assert email_log.email_type == "reminder"


class TestNotificationService:
    """Tests for notification service."""

    def test_get_email_logs(self, db: Session):
        """Test getting paginated email logs."""
        tenant = create_test_tenant(db)

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

        result = NotificationService.get_email_logs(db, tenant.id, page=1, size=3)

        assert result.total == 5
        assert len(result.items) == 3
        assert result.pages == 2

    def test_get_email_logs_filter_by_type(self, db: Session):
        """Test filtering email logs by type."""
        tenant = create_test_tenant(db)

        # Create logs of different types
        types = ["welcome", "invitation", "welcome", "password_reset"]
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

        result = NotificationService.get_email_logs(
            db, tenant.id, page=1, size=10, email_type="welcome"
        )

        assert result.total == 2
        for item in result.items:
            assert item.email_type == "welcome"

    def test_get_email_logs_filter_by_sent_status(self, db: Session):
        """Test filtering email logs by sent status."""
        tenant = create_test_tenant(db)

        # Create logs with different sent status
        for i in range(4):
            log = EmailLog(
                tenant_id=tenant.id,
                to_email=f"user{i}@example.com",
                subject=f"Subject {i}",
                email_type="test",
                is_sent=(i % 2 == 0)  # alternating
            )
            db.add(log)
        db.commit()

        result = NotificationService.get_email_logs(
            db, tenant.id, page=1, size=10, is_sent=True
        )

        assert result.total == 2
        for item in result.items:
            assert item.is_sent == True

    def test_get_email_stats(self, db: Session):
        """Test getting email statistics."""
        tenant = create_test_tenant(db)

        # Create logs with various statuses and types
        logs = [
            EmailLog(tenant_id=tenant.id, to_email="a@test.com", subject="S", email_type="welcome", is_sent=True),
            EmailLog(tenant_id=tenant.id, to_email="b@test.com", subject="S", email_type="welcome", is_sent=True),
            EmailLog(tenant_id=tenant.id, to_email="c@test.com", subject="S", email_type="invitation", is_sent=True),
            EmailLog(tenant_id=tenant.id, to_email="d@test.com", subject="S", email_type="password_reset", is_sent=False),
        ]
        db.add_all(logs)
        db.commit()

        stats = NotificationService.get_email_stats(db, tenant.id)

        assert stats.total_sent == 3
        assert stats.total_failed == 1
        assert stats.success_rate == 75.0
        assert stats.by_type["welcome"] == 2
        assert stats.by_type["invitation"] == 1
        assert stats.by_type["password_reset"] == 1

    def test_get_email_log_by_id(self, db: Session):
        """Test getting a specific email log."""
        tenant = create_test_tenant(db)

        log = EmailLog(
            tenant_id=tenant.id,
            to_email="specific@test.com",
            subject="Specific Subject",
            email_type="test",
            is_sent=True
        )
        db.add(log)
        db.commit()

        result = NotificationService.get_email_log(db, log.id, tenant.id)

        assert result is not None
        assert result.id == log.id
        assert result.to_email == "specific@test.com"

    def test_get_email_log_wrong_tenant_returns_none(self, db: Session):
        """Test that getting log from wrong tenant returns None."""
        tenant1 = Tenant(name="Tenant 1", slug="tenant-1", plan="professional")
        tenant2 = Tenant(name="Tenant 2", slug="tenant-2", plan="professional")
        db.add_all([tenant1, tenant2])
        db.commit()

        log = EmailLog(
            tenant_id=tenant1.id,
            to_email="test@test.com",
            subject="Subject",
            email_type="test",
            is_sent=True
        )
        db.add(log)
        db.commit()

        # Try to get from wrong tenant
        result = NotificationService.get_email_log(db, log.id, tenant2.id)

        assert result is None
