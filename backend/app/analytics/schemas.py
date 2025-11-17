"""
Analytics schemas.
Defines response models for analytics and reporting endpoints.
"""

from pydantic import BaseModel, Field
from datetime import datetime, date
from app.core.schemas import BaseSchema


# =========================================================================
# Dashboard Overview
# =========================================================================

class DashboardOverviewResponse(BaseSchema):
    """
    Métricas generales del tenant para el dashboard.

    Proporciona una vista general de:
    - Totales de usuarios, flujos y assignments
    - Breakdown de assignments por status
    - Rates de completación
    - Actividad reciente
    """
    # Counts
    total_users: int = Field(..., description="Total de usuarios activos en el tenant")
    total_flows: int = Field(..., description="Total de flujos activos")
    total_assignments: int = Field(..., description="Total de assignments")

    # Status breakdown
    assignments_not_started: int = Field(..., description="Assignments no iniciados")
    assignments_in_progress: int = Field(..., description="Assignments en progreso")
    assignments_completed: int = Field(..., description="Assignments completados")
    assignments_overdue: int = Field(..., description="Assignments vencidos")

    # Rates
    overall_completion_rate: float = Field(..., description="Tasa de completación general (0-100)")
    avg_completion_time_days: float = Field(..., description="Tiempo promedio de completación en días")

    # Recent activity
    assignments_this_week: int = Field(..., description="Assignments asignados esta semana")
    completions_this_week: int = Field(..., description="Completaciones esta semana")


# =========================================================================
# Flow Analytics
# =========================================================================

class FlowAnalyticsResponse(BaseSchema):
    """
    Métricas específicas de un flujo de onboarding.

    Incluye:
    - Breakdown de assignments por status
    - Tasas de completación y progreso
    - Tiempo promedio de completación
    - Identificación del módulo más difícil
    """
    flow_id: int = Field(..., description="ID del flujo")
    flow_title: str = Field(..., description="Título del flujo")

    # Assignment counts
    total_assignments: int = Field(..., description="Total de assignments del flujo")
    completed_assignments: int = Field(..., description="Assignments completados")
    in_progress_assignments: int = Field(..., description="Assignments en progreso")
    not_started_assignments: int = Field(..., description="Assignments no iniciados")

    # Metrics
    completion_rate: float = Field(..., description="Tasa de completación (0-100)")
    avg_completion_time_days: float = Field(..., description="Tiempo promedio de completación en días")
    avg_progress_percentage: float = Field(..., description="Porcentaje promedio de progreso")

    # Hardest module (menor completion rate)
    hardest_module_id: int | None = Field(None, description="ID del módulo más difícil")
    hardest_module_title: str | None = Field(None, description="Título del módulo más difícil")
    hardest_module_completion_rate: float | None = Field(None, description="Tasa de completación del módulo más difícil")


# =========================================================================
# Module Analytics
# =========================================================================

class ModuleAnalyticsResponse(BaseSchema):
    """
    Métricas específicas de un módulo individual.

    Incluye:
    - Conteos de asignaciones y completaciones
    - Tasa de completación
    - Tiempo promedio invertido
    - Métricas específicas de quizzes
    """
    module_id: int = Field(..., description="ID del módulo")
    module_title: str = Field(..., description="Título del módulo")
    module_type: str = Field(..., description="Tipo de módulo (text, video, quiz, etc)")

    # Counts
    total_assigned: int = Field(..., description="Total de usuarios asignados")
    completed_count: int = Field(..., description="Total de completaciones")
    completion_rate: float = Field(..., description="Tasa de completación (0-100)")

    # Time
    avg_time_spent_minutes: float = Field(..., description="Tiempo promedio invertido en minutos")

    # Quiz metrics (solo para módulos tipo quiz)
    avg_quiz_score: float | None = Field(None, description="Puntuación promedio del quiz (0-100)")
    quiz_pass_rate: float | None = Field(None, description="Tasa de aprobación del quiz (0-100)")


# =========================================================================
# User Progress Report
# =========================================================================

class UserProgressReportResponse(BaseSchema):
    """
    Reporte detallado de progreso de un usuario específico.

    Incluye:
    - Información del usuario
    - Resumen de assignments
    - Progreso general
    - Detalles de cada assignment
    """
    user_id: int = Field(..., description="ID del usuario")
    user_name: str = Field(..., description="Nombre completo del usuario")
    user_email: str = Field(..., description="Email del usuario")
    department: str | None = Field(None, description="Departamento del usuario")

    # Assignment summary
    total_assignments: int = Field(..., description="Total de assignments del usuario")
    completed_assignments: int = Field(..., description="Assignments completados")
    in_progress_assignments: int = Field(..., description="Assignments en progreso")

    # Overall metrics
    overall_progress_percentage: float = Field(..., description="Porcentaje promedio de progreso general")
    total_time_spent_minutes: int = Field(..., description="Tiempo total invertido en minutos")

    # Assignment details
    assignments: list[dict] = Field(..., description="Detalles de cada assignment del usuario")


# =========================================================================
# Department Analytics
# =========================================================================

class DepartmentAnalyticsResponse(BaseSchema):
    """
    Métricas agregadas por departamento.

    Útil para comparar el progreso entre departamentos.
    """
    department: str = Field(..., description="Nombre del departamento")
    user_count: int = Field(..., description="Cantidad de usuarios en el departamento")

    # Assignments
    total_assignments: int = Field(..., description="Total de assignments del departamento")
    completed_assignments: int = Field(..., description="Assignments completados")
    completion_rate: float = Field(..., description="Tasa de completación (0-100)")

    # Progress
    avg_progress_percentage: float = Field(..., description="Porcentaje promedio de progreso")


# =========================================================================
# Completion Trends
# =========================================================================

class CompletionTrendsResponse(BaseModel):
    """
    Datos de tendencia para una fecha específica.

    Representa la actividad de onboarding en un día.
    """
    date: date = Field(..., description="Fecha")
    completions: int = Field(..., description="Número de completaciones en esta fecha")
    new_assignments: int = Field(..., description="Número de nuevos assignments en esta fecha")


class CompletionTrendsReportResponse(BaseModel):
    """
    Reporte completo de tendencias de completación.

    Incluye:
    - Serie temporal de datos por fecha
    - Totales agregados del período
    """
    trends: list[CompletionTrendsResponse] = Field(..., description="Lista de tendencias por fecha")
    total_completions: int = Field(..., description="Total de completaciones en el período")
    total_new_assignments: int = Field(..., description="Total de nuevos assignments en el período")


# =========================================================================
# Export Request (Post-MVP)
# =========================================================================

class ReportExportRequest(BaseModel):
    """
    Solicitud de exportación de reporte.

    Post-MVP: Permite exportar reportes en diferentes formatos.
    """
    report_type: str = Field(..., description="Tipo de reporte (overview, flow, user, department)")
    format: str = Field("csv", description="Formato de exportación (csv, pdf)")
    flow_id: int | None = Field(None, description="ID del flujo (si aplica)")
    start_date: date | None = Field(None, description="Fecha de inicio del período")
    end_date: date | None = Field(None, description="Fecha de fin del período")
