"""
Notifications router.
Defines REST endpoints for email logs and notification management.
"""

from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.schemas import PaginatedResponse
from app.auth.dependencies import get_current_user, require_tenant_admin
from app.users.models import User
from app.tenants.models import Tenant
from app.notifications import schemas
from app.notifications.service import NotificationService
from app.notifications.email_service import email_service

router = APIRouter(prefix="/notifications", tags=["Notifications"])


# =========================================================================
# Email Logs
# =========================================================================

@router.get(
    "/email-logs",
    response_model=PaginatedResponse[schemas.EmailLogResponse],
    dependencies=[Depends(require_tenant_admin)]
)
def get_email_logs(
    filters: schemas.EmailLogFilterParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtener logs de emails enviados.

    Permite filtrar por:
    - Tipo de email
    - Estado de envío (exitoso/fallido)
    - Email del destinatario

    **Requiere:** TENANT_ADMIN role
    """
    logs, total = NotificationService.get_email_logs(db, current_user.tenant_id, filters)

    return PaginatedResponse(
        data=[schemas.EmailLogResponse.model_validate(log) for log in logs],
        total=total,
        page=filters.page,
        page_size=filters.page_size,
        total_pages=(total + filters.page_size - 1) // filters.page_size
    )


# =========================================================================
# Test Email
# =========================================================================

@router.post(
    "/send-test-email",
    dependencies=[Depends(require_tenant_admin)]
)
async def send_test_email(
    data: schemas.SendEmailRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Enviar email de prueba (admin only).

    Útil para probar templates y configuración de email.
    El email se envía en background para no bloquear la respuesta.

    **Requiere:** TENANT_ADMIN role
    """
    # Obtener tenant para branding
    tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant no encontrado"
        )

    # Validar que el template existe
    try:
        branding = tenant.branding.to_theme_dict() if tenant.branding else None
        html = email_service.render_template(
            data.template_name,
            data.template_data,
            branding
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error renderizando template: {str(e)}"
        )

    # Enviar en background
    background_tasks.add_task(
        email_service.send_email,
        data.to_email,
        data.subject,
        html,
        data.to_name
    )

    return {
        "success": True,
        "message": "Email enviado en background",
        "details": {
            "to": data.to_email,
            "template": data.template_name
        }
    }
