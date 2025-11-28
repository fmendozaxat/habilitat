"""
Notification models for email logging.
"""

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, JSON, DateTime
from sqlalchemy.orm import relationship
from app.core.models import BaseTenantModel


class EmailLog(BaseTenantModel):
    """
    Log of sent emails for tracking and debugging.

    Attributes:
        to_email: Recipient email
        to_name: Recipient name
        subject: Email subject
        email_type: Type of email (welcome, invitation, etc.)
        template_name: Template used
        template_data: Variables passed to template
        is_sent: Whether email was sent successfully
        sent_at: When email was sent
        error_message: Error message if failed
        external_id: External provider ID
        user_id: Related user (optional)
    """

    __tablename__ = "email_logs"

    # Override tenant_id with explicit FK
    tenant_id = Column(
        Integer,
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=True,  # Can be null for system emails
        index=True
    )

    # Recipient
    to_email = Column(String(255), nullable=False, index=True)
    to_name = Column(String(200), nullable=True)

    # Subject & type
    subject = Column(String(500), nullable=False)
    email_type = Column(String(50), nullable=False, index=True)

    # Content
    template_name = Column(String(100), nullable=True)
    template_data = Column(JSON, nullable=True)

    # Status
    is_sent = Column(Boolean, default=False, nullable=False)
    sent_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

    # External ID
    external_id = Column(String(200), nullable=True)

    # Related user
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Relationships
    user = relationship("User")

    def __repr__(self):
        return f"<EmailLog {self.to_email} ({self.email_type})>"
