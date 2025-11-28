"""
Pydantic schemas for Analytics module.
"""

from datetime import datetime, date
from typing import Any
from pydantic import BaseModel
from app.core.schemas import BaseSchema


class DashboardOverviewResponse(BaseSchema):
    """Dashboard overview with tenant metrics."""

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
    overall_completion_rate: float
    avg_completion_time_days: float

    # Recent activity
    assignments_this_week: int
    completions_this_week: int


class FlowAnalyticsResponse(BaseSchema):
    """Analytics for a specific flow."""

    flow_id: int
    flow_title: str

    total_assignments: int
    completed_assignments: int
    in_progress_assignments: int
    not_started_assignments: int

    completion_rate: float
    avg_completion_time_days: float
    avg_progress_percentage: float

    # Hardest module
    hardest_module_id: int | None
    hardest_module_title: str | None
    hardest_module_completion_rate: float | None


class ModuleAnalyticsResponse(BaseSchema):
    """Analytics for a specific module."""

    module_id: int
    module_title: str
    module_type: str

    total_assigned: int
    completed_count: int
    completion_rate: float

    avg_time_spent_minutes: float

    # Quiz specific
    avg_quiz_score: float | None
    quiz_pass_rate: float | None


class UserProgressReportResponse(BaseSchema):
    """User progress report."""

    user_id: int
    user_name: str
    user_email: str
    department: str | None

    total_assignments: int
    completed_assignments: int
    in_progress_assignments: int

    overall_progress_percentage: float
    total_time_spent_minutes: int

    assignments: list[dict[str, Any]]


class DepartmentAnalyticsResponse(BaseSchema):
    """Analytics by department."""

    department: str
    user_count: int

    total_assignments: int
    completed_assignments: int
    completion_rate: float

    avg_progress_percentage: float


class CompletionTrendResponse(BaseSchema):
    """Single day completion trend."""

    date: date
    completions: int
    new_assignments: int


class CompletionTrendsReportResponse(BaseSchema):
    """Completion trends report."""

    trends: list[CompletionTrendResponse]
    total_completions: int
    total_new_assignments: int


class FlowsComparisonResponse(BaseSchema):
    """Comparison of multiple flows."""

    flows: list[FlowAnalyticsResponse]
