"""
Analytics router.
Defines REST endpoints for analytics and reporting.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import date, timedelta

from app.core.database import get_db
from app.core.enums import UserRole
from app.core.exceptions import NotFoundException, ForbiddenException
from app.auth.dependencies import get_current_user, require_tenant_admin
from app.users.models import User
from app.analytics import schemas
from app.analytics.service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


# =========================================================================
# Dashboard Overview
# =========================================================================

@router.get(
    "/dashboard",
    response_model=schemas.DashboardOverviewResponse,
    dependencies=[Depends(require_tenant_admin)]
)
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Dashboard general de métricas del tenant.

    Proporciona una vista general con:
    - Totales de usuarios, flujos y assignments
    - Breakdown de assignments por status
    - Tasas de completación y tiempo promedio
    - Actividad reciente (última semana)

    **Requiere:** TENANT_ADMIN role
    """
    return AnalyticsService.get_dashboard_overview(db, current_user.tenant_id)


# =========================================================================
# Flow Analytics
# =========================================================================

@router.get(
    "/flows/{flow_id}",
    response_model=schemas.FlowAnalyticsResponse,
    dependencies=[Depends(require_tenant_admin)]
)
def get_flow_analytics(
    flow_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Analytics detallados de un flujo de onboarding específico.

    Incluye:
    - Breakdown de assignments por status
    - Tasas de completación y progreso
    - Tiempo promedio de completación
    - Identificación del módulo más difícil

    **Requiere:** TENANT_ADMIN role
    """
    try:
        return AnalyticsService.get_flow_analytics(db, flow_id, current_user.tenant_id)
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# =========================================================================
# User Progress Report
# =========================================================================

@router.get(
    "/users/{user_id}/progress",
    response_model=schemas.UserProgressReportResponse
)
def get_user_progress(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Reporte detallado de progreso de un usuario.

    Incluye:
    - Información del usuario
    - Resumen de assignments
    - Progreso general y tiempo total invertido
    - Detalles de cada assignment

    **Permisos:**
    - TENANT_ADMIN puede ver cualquier usuario del tenant
    - EMPLOYEE solo puede ver su propio progreso
    """
    # Validar permisos: employee solo puede ver su propio progreso
    if current_user.role == UserRole.EMPLOYEE.value and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No puedes ver el progreso de otros usuarios"
        )

    try:
        return AnalyticsService.get_user_progress_report(db, user_id, current_user.tenant_id)
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# =========================================================================
# Completion Trends
# =========================================================================

@router.get(
    "/trends",
    response_model=schemas.CompletionTrendsReportResponse,
    dependencies=[Depends(require_tenant_admin)]
)
def get_completion_trends(
    start_date: date = Query(..., description="Fecha de inicio del período"),
    end_date: date = Query(..., description="Fecha de fin del período"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Tendencias de completación por fecha.

    Genera una serie temporal con:
    - Completaciones por día
    - Nuevos assignments por día
    - Totales del período

    **Requiere:** TENANT_ADMIN role

    **Nota:** El rango de fechas no debe exceder 365 días.
    """
    # Validar rango de fechas
    if end_date < start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La fecha de fin debe ser mayor o igual a la fecha de inicio"
        )

    # Limitar rango a 365 días
    date_range = (end_date - start_date).days
    if date_range > 365:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El rango de fechas no puede exceder 365 días"
        )

    return AnalyticsService.get_completion_trends(
        db, current_user.tenant_id, start_date, end_date
    )
