# Módulo 7: Analytics (Reportes y Métricas)

## Descripción

El módulo Analytics proporciona reportes y métricas sobre el progreso de onboarding, completación de usuarios, tiempo promedio, y estadísticas generales para que los admins del tenant puedan hacer seguimiento.

**Límite de líneas:** ~2000-3000 líneas

## Responsabilidades

1. Dashboard de métricas generales del tenant
2. Reportes de progreso por flujo de onboarding
3. Reportes de progreso por usuario
4. Métricas de completación (rates, tiempos promedio)
5. Reportes de módulos más/menos completados
6. Exportación de reportes (CSV, PDF - post-MVP)
7. Filtrado por fechas, departamentos, roles

## Estructura de Archivos

```
app/analytics/
├── __init__.py
├── models.py              # (Opcional) Tablas de analytics pre-calculados
├── schemas.py             # Response schemas de reportes
├── service.py             # Lógica de cálculo de métricas
├── router.py              # Endpoints de reportes
└── utils.py               # Utilidades de agregación
```

## 1. Modelos (models.py)

**Nota:** Para MVP, Analytics no requiere modelos propios. Calcula métricas en tiempo real desde OnboardingAssignment y ModuleProgress.

Para post-MVP (optimización), se pueden crear tablas de métricas pre-calculadas:

```python
# OPCIONAL - Post-MVP
from sqlalchemy import Column, Integer, Date, Float
from app.core.models import BaseModel, TenantMixin

class DailyMetrics(BaseModel, TenantMixin):
    """
    Métricas diarias pre-calculadas (para optimización)
    """
    __tablename__ = "daily_metrics"

    date = Column(Date, nullable=False, index=True)

    # Counts
    total_users = Column(Integer, default=0)
    active_assignments = Column(Integer, default=0)
    completed_assignments = Column(Integer, default=0)
    new_assignments = Column(Integer, default=0)

    # Rates
    completion_rate = Column(Float, default=0.0)
    avg_completion_time_days = Column(Float, default=0.0)

    # Por flujo (JSON)
    flow_metrics = Column(JSON, default={})
```

## 2. Schemas (schemas.py)

### Response Schemas

```python
from pydantic import BaseModel
from datetime import datetime, date
from app.core.schemas import BaseSchema

# Dashboard Overview
class DashboardOverviewResponse(BaseSchema):
    """Métricas generales del tenant"""
    # Counts
    total_users: int
    total_flows: int
    total_assignments: int

    # Status breakdown
    assignments_not_started: int
    assignments_in_progress: int
    assignments_completed: int
    assignments_overdue: int

    # Rates
    overall_completion_rate: float  # 0-100
    avg_completion_time_days: float

    # Recent activity
    assignments_this_week: int
    completions_this_week: int

# Flow Analytics
class FlowAnalyticsResponse(BaseSchema):
    """Métricas por flujo de onboarding"""
    flow_id: int
    flow_title: str

    total_assignments: int
    completed_assignments: int
    in_progress_assignments: int
    not_started_assignments: int

    completion_rate: float  # 0-100
    avg_completion_time_days: float
    avg_progress_percentage: float

    # Módulo más difícil (menor completion rate)
    hardest_module_id: int | None
    hardest_module_title: str | None
    hardest_module_completion_rate: float | None

class ModuleAnalyticsResponse(BaseSchema):
    """Métricas por módulo"""
    module_id: int
    module_title: str
    module_type: str

    total_assigned: int
    completed_count: int
    completion_rate: float  # 0-100

    avg_time_spent_minutes: float

    # Para quizzes
    avg_quiz_score: float | None
    quiz_pass_rate: float | None

# User Progress Report
class UserProgressReportResponse(BaseSchema):
    """Reporte de progreso de un usuario"""
    user_id: int
    user_name: str
    user_email: str
    department: str | None

    total_assignments: int
    completed_assignments: int
    in_progress_assignments: int

    overall_progress_percentage: float
    total_time_spent_minutes: int

    assignments: list[dict]  # Detalle de cada assignment

# Department Analytics
class DepartmentAnalyticsResponse(BaseSchema):
    """Métricas por departamento"""
    department: str
    user_count: int

    total_assignments: int
    completed_assignments: int
    completion_rate: float

    avg_progress_percentage: float

# Completion Trends
class CompletionTrendsResponse(BaseSchema):
    """Tendencias de completación por fecha"""
    date: date
    completions: int
    new_assignments: int

class CompletionTrendsReportResponse(BaseSchema):
    """Reporte de tendencias"""
    trends: list[CompletionTrendsResponse]
    total_completions: int
    total_new_assignments: int

# Export
class ReportExportRequest(BaseModel):
    report_type: str  # "overview", "flow", "user", "department"
    format: str = "csv"  # "csv", "pdf" (post-MVP)
    flow_id: int | None = None
    start_date: date | None = None
    end_date: date | None = None
```

## 3. Service (service.py)

### AnalyticsService Class

```python
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta, date
from app.onboarding.models import OnboardingFlow, OnboardingAssignment, ModuleProgress
from app.users.models import User
from app.core.enums import OnboardingStatus
from app.analytics import schemas

class AnalyticsService:
    """Servicio de analytics y reportes"""

    @staticmethod
    def get_dashboard_overview(db: Session, tenant_id: int) -> schemas.DashboardOverviewResponse:
        """
        Dashboard general con métricas del tenant

        Calcula:
        - Totales (users, flows, assignments)
        - Breakdown por status
        - Rates de completación
        - Actividad reciente
        """
        # Total users
        total_users = db.query(func.count(User.id)).filter(
            User.tenant_id == tenant_id,
            User.is_active == True
        ).scalar()

        # Total flows
        total_flows = db.query(func.count(OnboardingFlow.id)).filter(
            OnboardingFlow.tenant_id == tenant_id,
            OnboardingFlow.is_active == True
        ).scalar()

        # Total assignments
        total_assignments = db.query(func.count(OnboardingAssignment.id)).filter(
            OnboardingAssignment.tenant_id == tenant_id
        ).scalar()

        # Status breakdown
        assignments_not_started = db.query(func.count(OnboardingAssignment.id)).filter(
            OnboardingAssignment.tenant_id == tenant_id,
            OnboardingAssignment.status == OnboardingStatus.NOT_STARTED
        ).scalar()

        assignments_in_progress = db.query(func.count(OnboardingAssignment.id)).filter(
            OnboardingAssignment.tenant_id == tenant_id,
            OnboardingAssignment.status == OnboardingStatus.IN_PROGRESS
        ).scalar()

        assignments_completed = db.query(func.count(OnboardingAssignment.id)).filter(
            OnboardingAssignment.tenant_id == tenant_id,
            OnboardingAssignment.status == OnboardingStatus.COMPLETED
        ).scalar()

        # Overdue
        now = datetime.utcnow()
        assignments_overdue = db.query(func.count(OnboardingAssignment.id)).filter(
            OnboardingAssignment.tenant_id == tenant_id,
            OnboardingAssignment.status != OnboardingStatus.COMPLETED,
            OnboardingAssignment.due_date < now
        ).scalar()

        # Completion rate
        completion_rate = (assignments_completed / total_assignments * 100) if total_assignments > 0 else 0

        # Avg completion time
        completed = db.query(OnboardingAssignment).filter(
            OnboardingAssignment.tenant_id == tenant_id,
            OnboardingAssignment.status == OnboardingStatus.COMPLETED,
            OnboardingAssignment.completed_at.isnot(None)
        ).all()

        if completed:
            completion_times = [
                (a.completed_at - a.assigned_at).days
                for a in completed
            ]
            avg_completion_time_days = sum(completion_times) / len(completion_times)
        else:
            avg_completion_time_days = 0

        # This week activity
        week_ago = now - timedelta(days=7)

        assignments_this_week = db.query(func.count(OnboardingAssignment.id)).filter(
            OnboardingAssignment.tenant_id == tenant_id,
            OnboardingAssignment.assigned_at >= week_ago
        ).scalar()

        completions_this_week = db.query(func.count(OnboardingAssignment.id)).filter(
            OnboardingAssignment.tenant_id == tenant_id,
            OnboardingAssignment.completed_at >= week_ago
        ).scalar()

        return schemas.DashboardOverviewResponse(
            total_users=total_users,
            total_flows=total_flows,
            total_assignments=total_assignments,
            assignments_not_started=assignments_not_started,
            assignments_in_progress=assignments_in_progress,
            assignments_completed=assignments_completed,
            assignments_overdue=assignments_overdue,
            overall_completion_rate=round(completion_rate, 2),
            avg_completion_time_days=round(avg_completion_time_days, 2),
            assignments_this_week=assignments_this_week,
            completions_this_week=completions_this_week
        )

    @staticmethod
    def get_flow_analytics(db: Session, flow_id: int, tenant_id: int) -> schemas.FlowAnalyticsResponse:
        """
        Métricas específicas de un flujo

        - Assignments por status
        - Completion rate
        - Avg time
        - Módulo más difícil
        """
        from app.onboarding.service import OnboardingService

        flow = OnboardingService.get_flow(db, flow_id, tenant_id)

        # Assignments
        assignments = db.query(OnboardingAssignment).filter(
            OnboardingAssignment.flow_id == flow_id,
            OnboardingAssignment.tenant_id == tenant_id
        ).all()

        total_assignments = len(assignments)

        if total_assignments == 0:
            return schemas.FlowAnalyticsResponse(
                flow_id=flow_id,
                flow_title=flow.title,
                total_assignments=0,
                completed_assignments=0,
                in_progress_assignments=0,
                not_started_assignments=0,
                completion_rate=0,
                avg_completion_time_days=0,
                avg_progress_percentage=0,
                hardest_module_id=None,
                hardest_module_title=None,
                hardest_module_completion_rate=None
            )

        # Status counts
        completed = sum(1 for a in assignments if a.status == OnboardingStatus.COMPLETED)
        in_progress = sum(1 for a in assignments if a.status == OnboardingStatus.IN_PROGRESS)
        not_started = sum(1 for a in assignments if a.status == OnboardingStatus.NOT_STARTED)

        # Rates
        completion_rate = (completed / total_assignments * 100)

        # Avg progress
        avg_progress = sum(a.completion_percentage for a in assignments) / total_assignments

        # Avg completion time
        completed_assignments = [a for a in assignments if a.status == OnboardingStatus.COMPLETED]
        if completed_assignments:
            completion_times = [(a.completed_at - a.assigned_at).days for a in completed_assignments]
            avg_completion_time = sum(completion_times) / len(completion_times)
        else:
            avg_completion_time = 0

        # Hardest module (menor completion rate)
        module_stats = {}
        for module in flow.modules:
            progress_records = db.query(ModuleProgress).filter(
                ModuleProgress.module_id == module.id
            ).all()

            if progress_records:
                completed_count = sum(1 for p in progress_records if p.is_completed)
                module_stats[module.id] = {
                    "title": module.title,
                    "completion_rate": (completed_count / len(progress_records) * 100)
                }

        hardest_module = None
        if module_stats:
            hardest_id = min(module_stats.keys(), key=lambda k: module_stats[k]["completion_rate"])
            hardest_module = {
                "id": hardest_id,
                "title": module_stats[hardest_id]["title"],
                "completion_rate": module_stats[hardest_id]["completion_rate"]
            }

        return schemas.FlowAnalyticsResponse(
            flow_id=flow_id,
            flow_title=flow.title,
            total_assignments=total_assignments,
            completed_assignments=completed,
            in_progress_assignments=in_progress,
            not_started_assignments=not_started,
            completion_rate=round(completion_rate, 2),
            avg_completion_time_days=round(avg_completion_time, 2),
            avg_progress_percentage=round(avg_progress, 2),
            hardest_module_id=hardest_module["id"] if hardest_module else None,
            hardest_module_title=hardest_module["title"] if hardest_module else None,
            hardest_module_completion_rate=round(hardest_module["completion_rate"], 2) if hardest_module else None
        )

    @staticmethod
    def get_user_progress_report(
        db: Session,
        user_id: int,
        tenant_id: int
    ) -> schemas.UserProgressReportResponse:
        """
        Reporte detallado de progreso de un usuario

        - Todos sus assignments
        - Progreso general
        - Tiempo total invertido
        """
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            raise NotFoundException("Usuario")

        # Assignments del usuario
        assignments = db.query(OnboardingAssignment).filter(
            OnboardingAssignment.user_id == user_id,
            OnboardingAssignment.tenant_id == tenant_id
        ).all()

        total_assignments = len(assignments)
        completed = sum(1 for a in assignments if a.status == OnboardingStatus.COMPLETED)
        in_progress = sum(1 for a in assignments if a.status == OnboardingStatus.IN_PROGRESS)

        # Overall progress
        if total_assignments > 0:
            overall_progress = sum(a.completion_percentage for a in assignments) / total_assignments
        else:
            overall_progress = 0

        # Total time spent
        total_time = 0
        for assignment in assignments:
            for progress in assignment.module_progress:
                total_time += progress.time_spent_minutes

        # Assignment details
        assignment_details = []
        for a in assignments:
            assignment_details.append({
                "assignment_id": a.id,
                "flow_title": a.flow.title,
                "status": a.status,
                "progress_percentage": a.completion_percentage,
                "assigned_at": a.assigned_at,
                "completed_at": a.completed_at,
                "is_overdue": a.is_overdue
            })

        return schemas.UserProgressReportResponse(
            user_id=user_id,
            user_name=user.full_name,
            user_email=user.email,
            department=user.department,
            total_assignments=total_assignments,
            completed_assignments=completed,
            in_progress_assignments=in_progress,
            overall_progress_percentage=round(overall_progress, 2),
            total_time_spent_minutes=total_time,
            assignments=assignment_details
        )

    @staticmethod
    def get_completion_trends(
        db: Session,
        tenant_id: int,
        start_date: date,
        end_date: date
    ) -> schemas.CompletionTrendsReportResponse:
        """
        Tendencias de completación por día

        - Completados por día
        - Nuevos assignments por día
        """
        # Query assignments completados en el rango
        completed_by_date = db.query(
            func.date(OnboardingAssignment.completed_at).label('date'),
            func.count(OnboardingAssignment.id).label('count')
        ).filter(
            OnboardingAssignment.tenant_id == tenant_id,
            OnboardingAssignment.completed_at.isnot(None),
            func.date(OnboardingAssignment.completed_at) >= start_date,
            func.date(OnboardingAssignment.completed_at) <= end_date
        ).group_by(func.date(OnboardingAssignment.completed_at)).all()

        # Query nuevos assignments por día
        new_by_date = db.query(
            func.date(OnboardingAssignment.assigned_at).label('date'),
            func.count(OnboardingAssignment.id).label('count')
        ).filter(
            OnboardingAssignment.tenant_id == tenant_id,
            func.date(OnboardingAssignment.assigned_at) >= start_date,
            func.date(OnboardingAssignment.assigned_at) <= end_date
        ).group_by(func.date(OnboardingAssignment.assigned_at)).all()

        # Crear diccionarios
        completed_dict = {row.date: row.count for row in completed_by_date}
        new_dict = {row.date: row.count for row in new_by_date}

        # Generar lista de fechas
        trends = []
        current_date = start_date
        while current_date <= end_date:
            trends.append(schemas.CompletionTrendsResponse(
                date=current_date,
                completions=completed_dict.get(current_date, 0),
                new_assignments=new_dict.get(current_date, 0)
            ))
            current_date += timedelta(days=1)

        return schemas.CompletionTrendsReportResponse(
            trends=trends,
            total_completions=sum(completed_dict.values()),
            total_new_assignments=sum(new_dict.values())
        )
```

## 4. Router (router.py)

### Analytics Endpoints

```python
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import date, timedelta
from app.core.database import get_db
from app.core.enums import UserRole
from app.analytics import schemas, service
from app.auth.dependencies import get_current_user, require_role
from app.tenants.models import Tenant
from app.tenants.dependencies import get_current_tenant
from app.users.models import User

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/dashboard", response_model=schemas.DashboardOverviewResponse)
async def get_dashboard(
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(require_role(UserRole.TENANT_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Dashboard general de métricas

    - Solo TENANT_ADMIN
    """
    return service.AnalyticsService.get_dashboard_overview(db, tenant.id)

@router.get("/flows/{flow_id}", response_model=schemas.FlowAnalyticsResponse)
async def get_flow_analytics(
    flow_id: int,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(require_role(UserRole.TENANT_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Analytics de un flujo específico

    - Solo TENANT_ADMIN
    """
    return service.AnalyticsService.get_flow_analytics(db, flow_id, tenant.id)

@router.get("/users/{user_id}/progress", response_model=schemas.UserProgressReportResponse)
async def get_user_progress(
    user_id: int,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Reporte de progreso de un usuario

    - TENANT_ADMIN puede ver cualquier usuario
    - EMPLOYEE solo puede ver su propio progreso
    """
    # Validar permisos
    if current_user.role == UserRole.EMPLOYEE and current_user.id != user_id:
        raise ForbiddenException("No puedes ver el progreso de otros usuarios")

    return service.AnalyticsService.get_user_progress_report(db, user_id, tenant.id)

@router.get("/trends", response_model=schemas.CompletionTrendsReportResponse)
async def get_completion_trends(
    start_date: date = Query(...),
    end_date: date = Query(...),
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(require_role(UserRole.TENANT_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Tendencias de completación por fecha

    - Solo TENANT_ADMIN
    """
    return service.AnalyticsService.get_completion_trends(db, tenant.id, start_date, end_date)
```

## Dependencias entre Módulos

**Depende de:**
- Core
- Onboarding (lee OnboardingAssignment, ModuleProgress)
- Users (lee User)

**Es usado por:**
- Nadie (es el final de la cadena)

## Testing

Tests de cálculo de métricas, agregaciones y reportes.

## Checklist

- [ ] Service con cálculo de métricas
- [ ] Endpoints de reportes
- [ ] Dashboard overview
- [ ] Analytics por flujo
- [ ] Reporte de usuario
- [ ] Tendencias
- [ ] Tests 80%+

## Notas

1. Implementar al final (depende de Onboarding y Users)
2. Para MVP, calcular métricas en tiempo real
3. Post-MVP: pre-calcular y cachear métricas
4. Optimizar queries con joins y eager loading

## Dependencias

Ninguna adicional.
