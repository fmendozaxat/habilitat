"""
Notifications schemas.
Defines request/response models for notification endpoints.
"""

from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from app.core.schemas import BaseSchema, PaginationParams


# =========================================================================
# Request Schemas
# =========================================================================

class SendEmailRequest(BaseModel):
    """
    Request para envío manual de email (solo admin).

    Útil para testing de templates y envíos manuales.
    """
    to_email: EmailStr = Field(..., description="Email del destinatario")
    to_name: str | None = Field(None, description="Nombre del destinatario")
    subject: str = Field(..., description="Asunto del email")
    template_name: str = Field(..., description="Nombre del template a usar (ej: welcome.html)")
    template_data: dict = Field(default_factory=dict, description="Variables para el template")


# =========================================================================
# Response Schemas
# =========================================================================

class EmailLogResponse(BaseSchema):
    """
    Response con datos de un email log.

    Incluye información completa del envío para tracking y debugging.
    """
    id: int = Field(..., description="ID del log")
    to_email: str = Field(..., description="Email del destinatario")
    to_name: str | None = Field(None, description="Nombre del destinatario")
    subject: str = Field(..., description="Asunto del email")
    email_type: str = Field(..., description="Tipo de email enviado")
    template_name: str | None = Field(None, description="Template utilizado")
    is_sent: bool = Field(..., description="Si fue enviado exitosamente")
    sent_at: datetime | None = Field(None, description="Timestamp del envío")
    error_message: str | None = Field(None, description="Mensaje de error si falló")
    external_id: str | None = Field(None, description="ID externo del proveedor")
    created_at: datetime = Field(..., description="Timestamp de creación del log")

    class Config:
        from_attributes = True


# =========================================================================
# Filter Schemas
# =========================================================================

class EmailLogFilterParams(PaginationParams):
    """
    Parámetros de filtrado para listar email logs.

    Permite filtrar por tipo, estado de envío y email del destinatario.
    """
    email_type: str | None = Field(None, description="Filtrar por tipo de email")
    is_sent: bool | None = Field(None, description="Filtrar por estado de envío")
    to_email: str | None = Field(None, description="Buscar por email del destinatario")
