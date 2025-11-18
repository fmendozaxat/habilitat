"""
Notifications models.
Defines database models for email logging and notification tracking.
"""

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, JSON, DateTime
from sqlalchemy.orm import relationship
from app.core.models import BaseModel, TimestampMixin, TenantMixin


class EmailLog(BaseModel, TimestampMixin, TenantMixin):
    """
    Log de emails enviados para tracking y debugging.

    Registra todos los emails enviados por la plataforma,
    incluyendo estado de envío, errores y metadata.
    """
    __tablename__ = "email_logs"

    # Recipient information
    to_email = Column(String(255), nullable=False, index=True, comment="Email del destinatario")
    to_name = Column(String(200), nullable=True, comment="Nombre del destinatario")

    # Email details
    subject = Column(String(500), nullable=False, comment="Asunto del email")
    email_type = Column(
        String(50),
        nullable=False,
        index=True,
        comment="Tipo de email (welcome, invitation, password_reset, etc.)"
    )

    # Template information
    template_name = Column(String(100), nullable=True, comment="Nombre del template utilizado")
    template_data = Column(JSON, nullable=True, comment="Variables pasadas al template")

    # Sending status
    is_sent = Column(Boolean, default=False, nullable=False, comment="Si el email fue enviado exitosamente")
    sent_at = Column(DateTime, nullable=True, comment="Timestamp del envío")
    error_message = Column(Text, nullable=True, comment="Mensaje de error si falló el envío")

    # External tracking
    external_id = Column(
        String(200),
        nullable=True,
        comment="ID externo del proveedor de email (SendGrid, etc.)"
    )

    # Relationships
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="ID del usuario relacionado (opcional)"
    )

    user = relationship("User", foreign_keys=[user_id])

    def __repr__(self):
        return f"<EmailLog {self.to_email} ({self.email_type})>"
