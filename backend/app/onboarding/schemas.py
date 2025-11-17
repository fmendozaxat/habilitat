"""Onboarding schemas for request/response validation."""

from pydantic import BaseModel, Field
from datetime import datetime
from app.core.schemas import BaseSchema, PaginationParams
from app.core.enums import ContentType, OnboardingStatus


# ============================================================================
# OnboardingFlow Schemas
# ============================================================================

class OnboardingFlowCreate(BaseModel):
    """Schema for creating an onboarding flow."""
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    is_active: bool = True
    settings: dict = {}


class OnboardingFlowUpdate(BaseModel):
    """Schema for updating an onboarding flow."""
    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    is_active: bool | None = None
    display_order: int | None = None
    settings: dict | None = None


class OnboardingFlowClone(BaseModel):
    """Schema for cloning an onboarding flow."""
    new_title: str = Field(..., min_length=1, max_length=200)


# ============================================================================
# OnboardingModule Schemas
# ============================================================================

class OnboardingModuleCreate(BaseModel):
    """Schema for creating an onboarding module."""
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    content_type: ContentType
    content_text: str | None = None
    content_url: str | None = Field(None, max_length=500)
    content_id: int | None = None
    order: int = 0
    is_required: bool = True
    requires_completion_confirmation: bool = False
    quiz_data: dict | None = None
    estimated_minutes: int | None = Field(None, ge=0)


class OnboardingModuleUpdate(BaseModel):
    """Schema for updating an onboarding module."""
    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    content_type: ContentType | None = None
    content_text: str | None = None
    content_url: str | None = Field(None, max_length=500)
    content_id: int | None = None
    order: int | None = None
    is_required: bool | None = None
    requires_completion_confirmation: bool | None = None
    quiz_data: dict | None = None
    estimated_minutes: int | None = Field(None, ge=0)


# ============================================================================
# OnboardingAssignment Schemas
# ============================================================================

class OnboardingAssignmentCreate(BaseModel):
    """Schema for creating an onboarding assignment."""
    flow_id: int
    user_id: int
    due_date: datetime | None = None


class BulkAssignmentCreate(BaseModel):
    """Schema for creating multiple assignments at once."""
    flow_id: int
    user_ids: list[int]
    due_date: datetime | None = None


# ============================================================================
# Module Progress Schemas
# ============================================================================

class CompleteModuleRequest(BaseModel):
    """Schema for completing a module."""
    notes: str | None = None
    time_spent_minutes: int | None = Field(None, ge=0)


class SubmitQuizRequest(BaseModel):
    """Schema for submitting a quiz."""
    answers: dict  # {"question_index": answer_value}
    time_spent_minutes: int | None = Field(None, ge=0)


# ============================================================================
# Filter Schemas
# ============================================================================

class AssignmentFilterParams(PaginationParams):
    """Schema for filtering assignments."""
    status: OnboardingStatus | None = None
    user_id: int | None = None
    flow_id: int | None = None
    overdue_only: bool = False


# ============================================================================
# Response Schemas
# ============================================================================

class OnboardingModuleResponse(BaseSchema):
    """Response schema for onboarding module."""
    id: int
    flow_id: int
    title: str
    description: str | None
    content_type: str
    content_text: str | None
    content_url: str | None
    content_id: int | None
    order: int
    is_required: bool
    requires_completion_confirmation: bool
    quiz_data: dict | None
    estimated_minutes: int | None
    created_at: str
    updated_at: str


class OnboardingFlowResponse(BaseSchema):
    """Full response schema for onboarding flow with modules."""
    id: int
    tenant_id: int
    title: str
    description: str | None
    is_active: bool
    is_template: bool
    display_order: int
    settings: dict
    module_count: int
    modules: list[OnboardingModuleResponse] = []
    created_at: str
    updated_at: str


class OnboardingFlowListResponse(BaseSchema):
    """Simplified response schema for flow lists."""
    id: int
    title: str
    description: str | None
    is_active: bool
    is_template: bool
    module_count: int
    created_at: str


class ModuleProgressResponse(BaseSchema):
    """Response schema for module progress."""
    id: int
    module_id: int
    module_title: str
    module_order: int
    content_type: str
    is_completed: bool
    completed_at: str | None
    time_spent_minutes: int
    quiz_score: int | None
    quiz_passed: bool | None


class OnboardingAssignmentResponse(BaseSchema):
    """Full response schema for onboarding assignment."""
    id: int
    flow_id: int
    flow_title: str
    user_id: int
    status: str
    completion_percentage: int
    assigned_at: str
    started_at: str | None
    completed_at: str | None
    due_date: str | None
    is_overdue: bool
    days_since_assignment: int
    module_progress: list[ModuleProgressResponse] = []


class OnboardingAssignmentListResponse(BaseSchema):
    """Simplified response schema for assignment lists."""
    id: int
    flow_id: int
    flow_title: str
    user_id: int
    user_name: str
    user_email: str
    status: str
    completion_percentage: int
    assigned_at: str
    due_date: str | None
    is_overdue: bool


class EmployeeDashboardResponse(BaseSchema):
    """Dashboard response for employees."""
    total_assignments: int
    completed: int
    in_progress: int
    not_started: int
    overdue: int
    assignments: list[OnboardingAssignmentResponse]


class QuizResultResponse(BaseSchema):
    """Response schema for quiz submission."""
    score: int
    passed: bool
    passing_score: int
    correct_answers: int
    total_questions: int
