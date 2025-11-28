"""
FastAPI router for Analytics module.
Provides endpoints for metrics and reporting.
"""

from datetime import date, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.enums import UserRole
from app.core.exceptions import ForbiddenException
from app.auth.dependencies import get_current_active_user, require_any_role
from app.tenants.dependencies import get_current_tenant
from app.tenants.models import Tenant
from app.users.models import User
from app.analytics import schemas
from app.analytics.service import AnalyticsService


router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/dashboard", response_model=schemas.DashboardOverviewResponse)
async def get_dashboard(
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(require_any_role(UserRole.TENANT_ADMIN, UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Get dashboard overview metrics.

    - Requires TENANT_ADMIN or SUPER_ADMIN role
    """
    return AnalyticsService.get_dashboard_overview(db, tenant.id)


@router.get("/flows", response_model=schemas.FlowsComparisonResponse)
async def get_all_flows_analytics(
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(require_any_role(UserRole.TENANT_ADMIN, UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Get analytics for all active flows.

    - Requires TENANT_ADMIN or SUPER_ADMIN role
    """
    flows = AnalyticsService.get_all_flows_analytics(db, tenant.id)
    return schemas.FlowsComparisonResponse(flows=flows)


@router.get("/flows/{flow_id}", response_model=schemas.FlowAnalyticsResponse)
async def get_flow_analytics(
    flow_id: int,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(require_any_role(UserRole.TENANT_ADMIN, UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Get analytics for a specific flow.

    - Requires TENANT_ADMIN or SUPER_ADMIN role
    """
    return AnalyticsService.get_flow_analytics(db, flow_id, tenant.id)


@router.get("/users/{user_id}/progress", response_model=schemas.UserProgressReportResponse)
async def get_user_progress(
    user_id: int,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get progress report for a user.

    - TENANT_ADMIN/SUPER_ADMIN can view any user
    - EMPLOYEE can only view their own progress
    """
    # Permission check
    if current_user.role == UserRole.EMPLOYEE.value and current_user.id != user_id:
        raise ForbiddenException("No puedes ver el progreso de otros usuarios")

    return AnalyticsService.get_user_progress_report(db, user_id, tenant.id)


@router.get("/my-progress", response_model=schemas.UserProgressReportResponse)
async def get_my_progress(
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get progress report for current user.

    - Available to all authenticated users
    """
    return AnalyticsService.get_user_progress_report(db, current_user.id, tenant.id)


@router.get("/trends", response_model=schemas.CompletionTrendsReportResponse)
async def get_completion_trends(
    start_date: date = Query(default=None, description="Start date (defaults to 30 days ago)"),
    end_date: date = Query(default=None, description="End date (defaults to today)"),
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(require_any_role(UserRole.TENANT_ADMIN, UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Get completion trends over a date range.

    - Requires TENANT_ADMIN or SUPER_ADMIN role
    - Default range: last 30 days
    """
    if end_date is None:
        end_date = date.today()
    if start_date is None:
        start_date = end_date - timedelta(days=30)

    return AnalyticsService.get_completion_trends(db, tenant.id, start_date, end_date)
