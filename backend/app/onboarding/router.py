"""
FastAPI router for Onboarding module.
Provides endpoints for flows, modules, assignments and progress tracking.
"""

from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.schemas import SuccessResponse, PaginatedResponse
from app.core.enums import UserRole
from app.core.exceptions import ForbiddenException
from app.auth.dependencies import get_current_user, get_current_active_user, require_any_role
from app.tenants.dependencies import get_current_tenant
from app.tenants.models import Tenant
from app.users.models import User
from app.onboarding import schemas
from app.onboarding.service import OnboardingService


router = APIRouter(prefix="/onboarding", tags=["Onboarding"])


# =============================================================================
# Flow Endpoints
# =============================================================================

@router.post("/flows", response_model=schemas.OnboardingFlowResponse, status_code=status.HTTP_201_CREATED)
async def create_flow(
    data: schemas.OnboardingFlowCreate,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(require_any_role(UserRole.TENANT_ADMIN, UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Create a new onboarding flow.

    - Requires TENANT_ADMIN or SUPER_ADMIN role
    """
    flow = OnboardingService.create_flow(db, tenant.id, data)
    return flow


@router.get("/flows", response_model=list[schemas.OnboardingFlowListResponse])
async def list_flows(
    include_inactive: bool = Query(False, description="Include inactive flows"),
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List all onboarding flows for the tenant.

    - Employees see only active flows
    - Admins can include inactive flows
    """
    # Only admins can see inactive flows
    if include_inactive and current_user.role == UserRole.EMPLOYEE.value:
        include_inactive = False

    flows = OnboardingService.list_flows(db, tenant.id, include_inactive)
    return flows


@router.get("/flows/{flow_id}", response_model=schemas.OnboardingFlowResponse)
async def get_flow(
    flow_id: int,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific onboarding flow with all its modules.
    """
    flow = OnboardingService.get_flow(db, flow_id, tenant.id)
    return flow


@router.patch("/flows/{flow_id}", response_model=schemas.OnboardingFlowResponse)
async def update_flow(
    flow_id: int,
    data: schemas.OnboardingFlowUpdate,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(require_any_role(UserRole.TENANT_ADMIN, UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Update an onboarding flow.

    - Requires TENANT_ADMIN or SUPER_ADMIN role
    """
    flow = OnboardingService.update_flow(db, flow_id, tenant.id, data)
    return flow


@router.delete("/flows/{flow_id}", response_model=SuccessResponse)
async def delete_flow(
    flow_id: int,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(require_any_role(UserRole.TENANT_ADMIN, UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Delete an onboarding flow (soft delete).

    - Requires TENANT_ADMIN or SUPER_ADMIN role
    """
    OnboardingService.delete_flow(db, flow_id, tenant.id)
    return SuccessResponse(message="Flujo eliminado exitosamente")


@router.post("/flows/{flow_id}/clone", response_model=schemas.OnboardingFlowResponse)
async def clone_flow(
    flow_id: int,
    data: schemas.CloneFlowRequest,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(require_any_role(UserRole.TENANT_ADMIN, UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Clone an onboarding flow with all its modules.

    - Requires TENANT_ADMIN or SUPER_ADMIN role
    """
    flow = OnboardingService.clone_flow(db, flow_id, tenant.id, data.new_title)
    return flow


# =============================================================================
# Module Endpoints
# =============================================================================

@router.post("/flows/{flow_id}/modules", response_model=schemas.OnboardingModuleResponse, status_code=status.HTTP_201_CREATED)
async def create_module(
    flow_id: int,
    data: schemas.OnboardingModuleCreate,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(require_any_role(UserRole.TENANT_ADMIN, UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Create a module in a flow.

    - Requires TENANT_ADMIN or SUPER_ADMIN role
    """
    module = OnboardingService.create_module(db, flow_id, tenant.id, data)
    return module


@router.patch("/modules/{module_id}", response_model=schemas.OnboardingModuleResponse)
async def update_module(
    module_id: int,
    data: schemas.OnboardingModuleUpdate,
    current_user: User = Depends(require_any_role(UserRole.TENANT_ADMIN, UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Update a module.

    - Requires TENANT_ADMIN or SUPER_ADMIN role
    """
    module = OnboardingService.update_module(db, module_id, data)
    return module


@router.delete("/modules/{module_id}", response_model=SuccessResponse)
async def delete_module(
    module_id: int,
    current_user: User = Depends(require_any_role(UserRole.TENANT_ADMIN, UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Delete a module.

    - Requires TENANT_ADMIN or SUPER_ADMIN role
    """
    OnboardingService.delete_module(db, module_id)
    return SuccessResponse(message="Módulo eliminado exitosamente")


@router.post("/flows/{flow_id}/modules/reorder", response_model=SuccessResponse)
async def reorder_modules(
    flow_id: int,
    data: schemas.ReorderModulesRequest,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(require_any_role(UserRole.TENANT_ADMIN, UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Reorder modules in a flow.

    - Requires TENANT_ADMIN or SUPER_ADMIN role
    """
    OnboardingService.reorder_modules(db, flow_id, tenant.id, data.module_orders)
    return SuccessResponse(message="Módulos reordenados exitosamente")


# =============================================================================
# Assignment Endpoints
# =============================================================================

@router.post("/assignments", response_model=schemas.OnboardingAssignmentResponse, status_code=status.HTTP_201_CREATED)
async def assign_flow(
    data: schemas.OnboardingAssignmentCreate,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(require_any_role(UserRole.TENANT_ADMIN, UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Assign a flow to a user.

    - Requires TENANT_ADMIN or SUPER_ADMIN role
    """
    assignment = OnboardingService.assign_flow(db, tenant.id, data, current_user.id)
    return _build_assignment_response(assignment)


@router.post("/assignments/bulk", response_model=list[schemas.OnboardingAssignmentListResponse])
async def bulk_assign_flow(
    data: schemas.BulkAssignmentCreate,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(require_any_role(UserRole.TENANT_ADMIN, UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Assign a flow to multiple users.

    - Requires TENANT_ADMIN or SUPER_ADMIN role
    - Skips users who already have the flow assigned
    """
    assignments = OnboardingService.bulk_assign_flow(db, tenant.id, data, current_user.id)
    return [_build_assignment_list_response(a) for a in assignments]


@router.get("/assignments", response_model=PaginatedResponse[schemas.OnboardingAssignmentListResponse])
async def list_assignments(
    filters: schemas.AssignmentFilterParams = Depends(),
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(require_any_role(UserRole.TENANT_ADMIN, UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    List all assignments for the tenant.

    - Requires TENANT_ADMIN or SUPER_ADMIN role
    """
    assignments, total = OnboardingService.list_assignments(db, tenant.id, filters)

    return PaginatedResponse.create(
        data=[_build_assignment_list_response(a) for a in assignments],
        total=total,
        page=filters.page,
        page_size=filters.page_size
    )


@router.get("/my-assignments", response_model=list[schemas.OnboardingAssignmentResponse])
async def get_my_assignments(
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's assignments.

    - Available to all authenticated users
    """
    assignments = OnboardingService.get_user_assignments(db, current_user.id, tenant.id)
    return [_build_assignment_response(a) for a in assignments]


@router.get("/my-dashboard", response_model=schemas.EmployeeDashboardResponse)
async def get_my_dashboard(
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get dashboard summary for current user.

    - Available to all authenticated users
    """
    dashboard = OnboardingService.get_employee_dashboard(db, current_user.id, tenant.id)

    return schemas.EmployeeDashboardResponse(
        total_assignments=dashboard["total_assignments"],
        completed=dashboard["completed"],
        in_progress=dashboard["in_progress"],
        not_started=dashboard["not_started"],
        overdue=dashboard["overdue"],
        assignments=[_build_assignment_response(a) for a in dashboard["assignments"]]
    )


@router.get("/assignments/{assignment_id}", response_model=schemas.OnboardingAssignmentResponse)
async def get_assignment(
    assignment_id: int,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific assignment.

    - Employees can only view their own assignments
    - Admins can view any assignment
    """
    assignment = OnboardingService.get_assignment(db, assignment_id, tenant.id)

    # Check permissions
    if current_user.role == UserRole.EMPLOYEE.value and assignment.user_id != current_user.id:
        raise ForbiddenException("No puedes ver esta asignación")

    return _build_assignment_response(assignment)


@router.delete("/assignments/{assignment_id}", response_model=SuccessResponse)
async def delete_assignment(
    assignment_id: int,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(require_any_role(UserRole.TENANT_ADMIN, UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Delete an assignment.

    - Requires TENANT_ADMIN or SUPER_ADMIN role
    """
    OnboardingService.delete_assignment(db, assignment_id, tenant.id)
    return SuccessResponse(message="Asignación eliminada exitosamente")


# =============================================================================
# Progress Endpoints
# =============================================================================

@router.post("/assignments/{assignment_id}/modules/{module_id}/complete", response_model=schemas.ModuleProgressResponse)
async def complete_module(
    assignment_id: int,
    module_id: int,
    data: schemas.CompleteModuleRequest = schemas.CompleteModuleRequest(),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Mark a module as completed.

    - Users can only complete modules in their own assignments
    """
    progress = OnboardingService.complete_module(
        db, assignment_id, module_id, current_user.id, data
    )
    return _build_progress_response(progress)


@router.post("/assignments/{assignment_id}/modules/{module_id}/submit-quiz", response_model=schemas.QuizResultResponse)
async def submit_quiz(
    assignment_id: int,
    module_id: int,
    data: schemas.SubmitQuizRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Submit quiz answers.

    - Automatically grades the quiz
    - Marks module as completed if passing score is reached
    """
    progress = OnboardingService.submit_quiz(
        db, assignment_id, module_id, current_user.id, data
    )

    # Get passing score from module
    passing_score = progress.module.quiz_data.get("passing_score", 70) if progress.module.quiz_data else 70

    return schemas.QuizResultResponse(
        score=progress.quiz_score or 0,
        passed=progress.quiz_passed or False,
        passing_score=passing_score,
        is_completed=progress.is_completed
    )


# =============================================================================
# Helper Functions
# =============================================================================

def _build_assignment_response(assignment) -> schemas.OnboardingAssignmentResponse:
    """Build full assignment response with progress."""
    return schemas.OnboardingAssignmentResponse(
        id=assignment.id,
        flow_id=assignment.flow_id,
        flow_title=assignment.flow.title,
        user_id=assignment.user_id,
        user_name=assignment.user.full_name,
        user_email=assignment.user.email,
        status=assignment.status,
        completion_percentage=assignment.completion_percentage,
        assigned_at=assignment.assigned_at,
        started_at=assignment.started_at,
        completed_at=assignment.completed_at,
        due_date=assignment.due_date,
        is_overdue=assignment.is_overdue,
        days_since_assignment=assignment.days_since_assignment,
        module_progress=[_build_progress_response(p) for p in assignment.module_progress]
    )


def _build_assignment_list_response(assignment) -> schemas.OnboardingAssignmentListResponse:
    """Build simplified assignment response for lists."""
    return schemas.OnboardingAssignmentListResponse(
        id=assignment.id,
        flow_id=assignment.flow_id,
        flow_title=assignment.flow.title,
        user_id=assignment.user_id,
        user_name=assignment.user.full_name,
        status=assignment.status,
        completion_percentage=assignment.completion_percentage,
        assigned_at=assignment.assigned_at,
        due_date=assignment.due_date,
        is_overdue=assignment.is_overdue
    )


def _build_progress_response(progress) -> schemas.ModuleProgressResponse:
    """Build module progress response."""
    return schemas.ModuleProgressResponse(
        id=progress.id,
        module_id=progress.module_id,
        module_title=progress.module.title,
        module_content_type=progress.module.content_type,
        module_order=progress.module.order,
        is_completed=progress.is_completed,
        completed_at=progress.completed_at,
        time_spent_minutes=progress.time_spent_minutes,
        quiz_score=progress.quiz_score,
        quiz_passed=progress.quiz_passed,
        notes=progress.notes
    )
