"""
FastAPI router for Notifications module.
Provides endpoints for email logs and notifications.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.enums import UserRole
from app.core.exceptions import NotFoundException
from app.auth.dependencies import require_any_role
from app.tenants.dependencies import get_current_tenant
from app.tenants.models import Tenant
from app.notifications import schemas
from app.notifications.service import NotificationService


router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("/emails", response_model=schemas.EmailLogListResponse)
async def get_email_logs(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    email_type: str | None = Query(default=None),
    is_sent: bool | None = Query(default=None),
    tenant: Tenant = Depends(get_current_tenant),
    current_user=Depends(require_any_role(UserRole.TENANT_ADMIN, UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Get paginated email logs.

    - Requires TENANT_ADMIN or SUPER_ADMIN role
    - Supports filtering by email_type and is_sent status
    """
    return NotificationService.get_email_logs(
        db, tenant.id, page, size, email_type, is_sent
    )


@router.get("/emails/stats", response_model=schemas.EmailStatsResponse)
async def get_email_stats(
    tenant: Tenant = Depends(get_current_tenant),
    current_user=Depends(require_any_role(UserRole.TENANT_ADMIN, UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Get email statistics.

    - Requires TENANT_ADMIN or SUPER_ADMIN role
    """
    return NotificationService.get_email_stats(db, tenant.id)


@router.get("/emails/{log_id}", response_model=schemas.EmailLogResponse)
async def get_email_log(
    log_id: int,
    tenant: Tenant = Depends(get_current_tenant),
    current_user=Depends(require_any_role(UserRole.TENANT_ADMIN, UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Get a specific email log.

    - Requires TENANT_ADMIN or SUPER_ADMIN role
    """
    log = NotificationService.get_email_log(db, log_id, tenant.id)
    if not log:
        raise NotFoundException("Email log no encontrado")

    return schemas.EmailLogResponse(
        id=log.id,
        tenant_id=log.tenant_id,
        to_email=log.to_email,
        to_name=log.to_name,
        subject=log.subject,
        email_type=log.email_type,
        template_name=log.template_name,
        is_sent=log.is_sent,
        sent_at=log.sent_at,
        error_message=log.error_message,
        external_id=log.external_id,
        user_id=log.user_id,
        created_at=log.created_at
    )


@router.post("/emails/{log_id}/retry", response_model=schemas.EmailLogResponse)
async def retry_email(
    log_id: int,
    tenant: Tenant = Depends(get_current_tenant),
    current_user=Depends(require_any_role(UserRole.TENANT_ADMIN, UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Retry sending a failed email.

    - Requires TENANT_ADMIN or SUPER_ADMIN role
    - Only works for emails that failed to send
    """
    new_log = NotificationService.retry_failed_email(db, log_id, tenant.id)
    if not new_log:
        raise NotFoundException("Email log no encontrado o ya fue enviado")

    return schemas.EmailLogResponse(
        id=new_log.id,
        tenant_id=new_log.tenant_id,
        to_email=new_log.to_email,
        to_name=new_log.to_name,
        subject=new_log.subject,
        email_type=new_log.email_type,
        template_name=new_log.template_name,
        is_sent=new_log.is_sent,
        sent_at=new_log.sent_at,
        error_message=new_log.error_message,
        external_id=new_log.external_id,
        user_id=new_log.user_id,
        created_at=new_log.created_at
    )
