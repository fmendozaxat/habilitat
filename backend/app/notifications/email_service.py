"""
Email service for sending emails using templates.
"""

import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy.orm import Session

from app.core.config import settings
from app.notifications.models import EmailLog


class EmailService:
    """Service for rendering and sending emails."""

    _instance = None
    _env: Environment | None = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._setup_templates()
        return cls._instance

    @classmethod
    def _setup_templates(cls):
        """Setup Jinja2 environment for email templates."""
        templates_dir = Path(__file__).parent / "templates"
        templates_dir.mkdir(exist_ok=True)

        cls._env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True
        )

    @classmethod
    def render_template(cls, template_name: str, **context) -> str:
        """Render an email template with context."""
        if cls._env is None:
            cls._setup_templates()

        template = cls._env.get_template(template_name)
        return template.render(**context)

    @staticmethod
    def send_email(
        db: Session,
        to_email: str,
        subject: str,
        email_type: str,
        template_name: str | None = None,
        template_data: dict[str, Any] | None = None,
        to_name: str | None = None,
        tenant_id: int | None = None,
        user_id: int | None = None,
        html_content: str | None = None
    ) -> EmailLog:
        """
        Send an email and log it.

        In production, this would integrate with an email provider
        (SendGrid, AWS SES, etc.). For now, it logs the email.
        """
        # Create log entry
        email_log = EmailLog(
            tenant_id=tenant_id,
            to_email=to_email,
            to_name=to_name,
            subject=subject,
            email_type=email_type,
            template_name=template_name,
            template_data=template_data or {},
            user_id=user_id,
            is_sent=False
        )

        try:
            # Render template if provided
            if template_name and not html_content:
                service = EmailService()
                html_content = service.render_template(
                    template_name,
                    **template_data or {}
                )

            # In production, send via email provider here
            # For now, we simulate success
            if settings.DEBUG:
                # In debug mode, just log to console
                print(f"[EMAIL] To: {to_email}")
                print(f"[EMAIL] Subject: {subject}")
                print(f"[EMAIL] Type: {email_type}")
                if html_content:
                    print(f"[EMAIL] Content length: {len(html_content)} chars")

            # Mark as sent
            email_log.is_sent = True
            email_log.sent_at = datetime.now(timezone.utc)

            # In real implementation, store external ID from provider
            # email_log.external_id = response.id

        except Exception as e:
            email_log.is_sent = False
            email_log.error_message = str(e)

        db.add(email_log)
        db.commit()
        db.refresh(email_log)

        return email_log

    @staticmethod
    def send_welcome_email(
        db: Session,
        user_email: str,
        user_name: str,
        tenant_name: str,
        login_url: str,
        tenant_id: int | None = None,
        user_id: int | None = None
    ) -> EmailLog:
        """Send welcome email to new user."""
        return EmailService.send_email(
            db=db,
            to_email=user_email,
            to_name=user_name,
            subject=f"Bienvenido a {tenant_name}",
            email_type="welcome",
            template_name="welcome.html",
            template_data={
                "user_name": user_name,
                "tenant_name": tenant_name,
                "login_url": login_url
            },
            tenant_id=tenant_id,
            user_id=user_id
        )

    @staticmethod
    def send_invitation_email(
        db: Session,
        to_email: str,
        inviter_name: str,
        tenant_name: str,
        invitation_token: str,
        expires_at: datetime,
        tenant_id: int | None = None
    ) -> EmailLog:
        """Send invitation email."""
        accept_url = f"{settings.FRONTEND_URL}/accept-invitation?token={invitation_token}"

        return EmailService.send_email(
            db=db,
            to_email=to_email,
            subject=f"Invitación a unirte a {tenant_name}",
            email_type="invitation",
            template_name="invitation.html",
            template_data={
                "inviter_name": inviter_name,
                "tenant_name": tenant_name,
                "accept_url": accept_url,
                "expires_at": expires_at.strftime("%d/%m/%Y %H:%M")
            },
            tenant_id=tenant_id
        )

    @staticmethod
    def send_password_reset_email(
        db: Session,
        to_email: str,
        user_name: str,
        reset_token: str,
        tenant_id: int | None = None,
        user_id: int | None = None
    ) -> EmailLog:
        """Send password reset email."""
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"

        return EmailService.send_email(
            db=db,
            to_email=to_email,
            to_name=user_name,
            subject="Restablecer contraseña",
            email_type="password_reset",
            template_name="password_reset.html",
            template_data={
                "user_name": user_name,
                "reset_url": reset_url
            },
            tenant_id=tenant_id,
            user_id=user_id
        )

    @staticmethod
    def send_assignment_notification(
        db: Session,
        to_email: str,
        user_name: str,
        flow_title: str,
        due_date: datetime | None,
        tenant_name: str,
        assignment_url: str,
        tenant_id: int | None = None,
        user_id: int | None = None
    ) -> EmailLog:
        """Send notification about new assignment."""
        return EmailService.send_email(
            db=db,
            to_email=to_email,
            to_name=user_name,
            subject=f"Nuevo proceso asignado: {flow_title}",
            email_type="assignment",
            template_name="assignment.html",
            template_data={
                "user_name": user_name,
                "flow_title": flow_title,
                "due_date": due_date.strftime("%d/%m/%Y") if due_date else None,
                "tenant_name": tenant_name,
                "assignment_url": assignment_url
            },
            tenant_id=tenant_id,
            user_id=user_id
        )

    @staticmethod
    def send_completion_notification(
        db: Session,
        to_email: str,
        user_name: str,
        flow_title: str,
        completion_date: datetime,
        tenant_name: str,
        tenant_id: int | None = None,
        user_id: int | None = None
    ) -> EmailLog:
        """Send notification about completed onboarding."""
        return EmailService.send_email(
            db=db,
            to_email=to_email,
            to_name=user_name,
            subject=f"¡Felicitaciones! Completaste {flow_title}",
            email_type="completion",
            template_name="completion.html",
            template_data={
                "user_name": user_name,
                "flow_title": flow_title,
                "completion_date": completion_date.strftime("%d/%m/%Y"),
                "tenant_name": tenant_name
            },
            tenant_id=tenant_id,
            user_id=user_id
        )

    @staticmethod
    def send_reminder_email(
        db: Session,
        to_email: str,
        user_name: str,
        flow_title: str,
        due_date: datetime | None,
        progress_percentage: int,
        assignment_url: str,
        tenant_id: int | None = None,
        user_id: int | None = None
    ) -> EmailLog:
        """Send reminder about pending assignment."""
        return EmailService.send_email(
            db=db,
            to_email=to_email,
            to_name=user_name,
            subject=f"Recordatorio: {flow_title} pendiente",
            email_type="reminder",
            template_name="reminder.html",
            template_data={
                "user_name": user_name,
                "flow_title": flow_title,
                "due_date": due_date.strftime("%d/%m/%Y") if due_date else None,
                "progress_percentage": progress_percentage,
                "assignment_url": assignment_url
            },
            tenant_id=tenant_id,
            user_id=user_id
        )
