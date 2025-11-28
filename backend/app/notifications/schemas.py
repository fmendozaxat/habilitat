"""
Pydantic schemas for Notifications module.
"""

from datetime import datetime
from typing import Any
from pydantic import BaseModel, EmailStr
from app.core.schemas import BaseSchema


# ==================== Email Request Schemas ====================

class SendEmailRequest(BaseModel):
    """Request to send an email."""

    to_email: EmailStr
    to_name: str | None = None
    subject: str
    template_name: str
    template_data: dict[str, Any] = {}


class SendWelcomeEmailRequest(BaseModel):
    """Request to send welcome email."""

    user_id: int


class SendInvitationEmailRequest(BaseModel):
    """Request to send invitation email."""

    invitation_id: int


class SendPasswordResetEmailRequest(BaseModel):
    """Request to send password reset email."""

    email: EmailStr


class SendAssignmentNotificationRequest(BaseModel):
    """Request to send assignment notification."""

    assignment_id: int


class SendCompletionNotificationRequest(BaseModel):
    """Request to send completion notification."""

    assignment_id: int


class SendReminderEmailRequest(BaseModel):
    """Request to send reminder email."""

    assignment_id: int


# ==================== Email Log Schemas ====================

class EmailLogResponse(BaseSchema):
    """Email log response."""

    id: int
    tenant_id: int | None
    to_email: str
    to_name: str | None
    subject: str
    email_type: str
    template_name: str | None
    is_sent: bool
    sent_at: datetime | None
    error_message: str | None
    external_id: str | None
    user_id: int | None
    created_at: datetime


class EmailLogListResponse(BaseSchema):
    """Paginated email log list."""

    items: list[EmailLogResponse]
    total: int
    page: int
    size: int
    pages: int


class EmailStatsResponse(BaseSchema):
    """Email statistics."""

    total_sent: int
    total_failed: int
    success_rate: float
    by_type: dict[str, int]
