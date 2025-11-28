"""
Pydantic schemas for Onboarding module.
Request/Response validation schemas for flows, modules, assignments and progress.
"""

from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field, field_validator
from app.core.schemas import BaseSchema, PaginationParams


# =============================================================================
# OnboardingFlow Schemas
# =============================================================================

class OnboardingFlowCreate(BaseModel):
    """Schema for creating an onboarding flow."""

    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    is_active: bool = True
    settings: dict[str, Any] = Field(default_factory=dict)


class OnboardingFlowUpdate(BaseModel):
    """Schema for updating an onboarding flow."""

    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    is_active: bool | None = None
    display_order: int | None = None
    settings: dict[str, Any] | None = None


class CloneFlowRequest(BaseModel):
    """Schema for cloning a flow."""

    new_title: str = Field(..., min_length=1, max_length=200)


# =============================================================================
# OnboardingModule Schemas
# =============================================================================

class OnboardingModuleCreate(BaseModel):
    """Schema for creating a module within a flow."""

    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    content_type: str = Field(..., pattern=r'^(text|video|pdf|quiz|task|link)$')
    content_text: str | None = None
    content_url: str | None = Field(None, max_length=500)
    order: int = 0
    is_required: bool = True
    requires_completion_confirmation: bool = False
    quiz_data: dict[str, Any] | None = None
    estimated_minutes: int | None = Field(None, ge=1)

    @field_validator('quiz_data')
    @classmethod
    def validate_quiz_data(cls, v, info):
        if info.data.get('content_type') == 'quiz' and not v:
            raise ValueError('quiz_data is required for quiz content type')
        return v


class OnboardingModuleUpdate(BaseModel):
    """Schema for updating a module."""

    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    content_type: str | None = Field(None, pattern=r'^(text|video|pdf|quiz|task|link)$')
    content_text: str | None = None
    content_url: str | None = Field(None, max_length=500)
    order: int | None = None
    is_required: bool | None = None
    requires_completion_confirmation: bool | None = None
    quiz_data: dict[str, Any] | None = None
    estimated_minutes: int | None = Field(None, ge=1)


class ReorderModulesRequest(BaseModel):
    """Schema for reordering modules."""

    module_orders: dict[int, int] = Field(..., description="Map of module_id to new order")


# =============================================================================
# OnboardingAssignment Schemas
# =============================================================================

class OnboardingAssignmentCreate(BaseModel):
    """Schema for creating an assignment."""

    flow_id: int
    user_id: int
    due_date: datetime | None = None


class BulkAssignmentCreate(BaseModel):
    """Schema for bulk assignment creation."""

    flow_id: int
    user_ids: list[int] = Field(..., min_length=1)
    due_date: datetime | None = None


class AssignmentFilterParams(PaginationParams):
    """Filter parameters for listing assignments."""

    status: str | None = Field(None, description="Filter by status")
    flow_id: int | None = Field(None, description="Filter by flow")
    user_id: int | None = Field(None, description="Filter by user")
    is_overdue: bool | None = Field(None, description="Filter overdue assignments")


# =============================================================================
# ModuleProgress Schemas
# =============================================================================

class CompleteModuleRequest(BaseModel):
    """Schema for completing a module."""

    notes: str | None = None
    time_spent_minutes: int | None = Field(None, ge=0)


class SubmitQuizRequest(BaseModel):
    """Schema for submitting quiz answers."""

    answers: dict[str, str] = Field(..., description="Map of question_index to answer")
    time_spent_minutes: int | None = Field(None, ge=0)


# =============================================================================
# Response Schemas
# =============================================================================

class OnboardingModuleResponse(BaseSchema):
    """Response schema for a module."""

    id: int
    flow_id: int
    title: str
    description: str | None
    content_type: str
    content_text: str | None
    content_url: str | None
    order: int
    is_required: bool
    requires_completion_confirmation: bool
    quiz_data: dict[str, Any] | None
    estimated_minutes: int | None
    created_at: datetime


class OnboardingFlowResponse(BaseSchema):
    """Full response schema for a flow with modules."""

    id: int
    tenant_id: int
    title: str
    description: str | None
    is_active: bool
    is_template: bool
    display_order: int
    settings: dict[str, Any]
    module_count: int
    total_estimated_minutes: int
    modules: list[OnboardingModuleResponse] = []
    created_at: datetime
    updated_at: datetime


class OnboardingFlowListResponse(BaseSchema):
    """Simplified response for flow listings."""

    id: int
    title: str
    description: str | None
    is_active: bool
    is_template: bool
    module_count: int
    total_estimated_minutes: int
    created_at: datetime


class ModuleProgressResponse(BaseSchema):
    """Response schema for module progress."""

    id: int
    module_id: int
    module_title: str
    module_content_type: str
    module_order: int
    is_completed: bool
    completed_at: datetime | None
    time_spent_minutes: int
    quiz_score: int | None
    quiz_passed: bool | None
    notes: str | None


class OnboardingAssignmentResponse(BaseSchema):
    """Full response schema for an assignment."""

    id: int
    flow_id: int
    flow_title: str
    user_id: int
    user_name: str
    user_email: str
    status: str
    completion_percentage: int
    assigned_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    due_date: datetime | None
    is_overdue: bool
    days_since_assignment: int
    module_progress: list[ModuleProgressResponse] = []


class OnboardingAssignmentListResponse(BaseSchema):
    """Simplified response for assignment listings."""

    id: int
    flow_id: int
    flow_title: str
    user_id: int
    user_name: str
    status: str
    completion_percentage: int
    assigned_at: datetime
    due_date: datetime | None
    is_overdue: bool


class EmployeeDashboardResponse(BaseSchema):
    """Dashboard summary for employees."""

    total_assignments: int
    completed: int
    in_progress: int
    not_started: int
    overdue: int
    assignments: list[OnboardingAssignmentResponse]


class QuizResultResponse(BaseSchema):
    """Response for quiz submission."""

    score: int
    passed: bool
    passing_score: int
    is_completed: bool
