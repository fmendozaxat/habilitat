"""Onboarding API router."""

from fastapi import APIRouter, Depends, status, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.schemas import SuccessResponse, PaginatedResponse
from app.core.enums import UserRole
from app.core.exceptions import ForbiddenException
from app.onboarding import schemas
from app.onboarding.service import OnboardingService
from app.users.models import User
from app.auth.dependencies import get_current_user, get_current_active_user, require_any_role
from app.tenants.models import Tenant
from app.tenants.dependencies import get_current_tenant
from app.notifications.service import NotificationService

router = APIRouter(prefix="/onboarding", tags=["Onboarding"])


# ============================================================================
# OnboardingFlow Endpoints (Admin)
# ============================================================================

@router.post("/flows", response_model=schemas.OnboardingFlowResponse, status_code=status.HTTP_201_CREATED)
async def create_flow(
    data: schemas.OnboardingFlowCreate,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(require_any_role(UserRole.TENANT_ADMIN, UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Create onboarding flow.

    Requires TENANT_ADMIN or SUPER_ADMIN role.
    """
    flow = OnboardingService.create_flow(db, tenant.id, data)

    return schemas.OnboardingFlowResponse(
        id=flow.id,
        tenant_id=flow.tenant_id,
        title=flow.title,
        description=flow.description,
        is_active=flow.is_active,
        is_template=flow.is_template,
        display_order=flow.display_order,
        settings=flow.settings,
        module_count=flow.module_count,
        modules=[],
        created_at=flow.created_at.isoformat(),
        updated_at=flow.updated_at.isoformat()
    )


@router.get("/flows", response_model=list[schemas.OnboardingFlowListResponse])
async def list_flows(
    include_inactive: bool = False,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List onboarding flows.

    All authenticated users can view flows.
    """
    flows = OnboardingService.list_flows(db, tenant.id, include_inactive)

    return [
        schemas.OnboardingFlowListResponse(
            id=flow.id,
            title=flow.title,
            description=flow.description,
            is_active=flow.is_active,
            is_template=flow.is_template,
            module_count=flow.module_count,
            created_at=flow.created_at.isoformat()
        )
        for flow in flows
    ]


@router.get("/flows/{flow_id}", response_model=schemas.OnboardingFlowResponse)
async def get_flow(
    flow_id: int,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get onboarding flow with all modules.

    All authenticated users can view flow details.
    """
    flow = OnboardingService.get_flow(db, flow_id, tenant.id)

    modules = [
        schemas.OnboardingModuleResponse(
            id=m.id,
            flow_id=m.flow_id,
            title=m.title,
            description=m.description,
            content_type=m.content_type,
            content_text=m.content_text,
            content_url=m.content_url,
            content_id=m.content_id,
            order=m.order,
            is_required=m.is_required,
            requires_completion_confirmation=m.requires_completion_confirmation,
            quiz_data=m.quiz_data,
            estimated_minutes=m.estimated_minutes,
            created_at=m.created_at.isoformat(),
            updated_at=m.updated_at.isoformat()
        )
        for m in flow.modules
    ]

    return schemas.OnboardingFlowResponse(
        id=flow.id,
        tenant_id=flow.tenant_id,
        title=flow.title,
        description=flow.description,
        is_active=flow.is_active,
        is_template=flow.is_template,
        display_order=flow.display_order,
        settings=flow.settings,
        module_count=flow.module_count,
        modules=modules,
        created_at=flow.created_at.isoformat(),
        updated_at=flow.updated_at.isoformat()
    )


@router.patch("/flows/{flow_id}", response_model=schemas.OnboardingFlowResponse)
async def update_flow(
    flow_id: int,
    data: schemas.OnboardingFlowUpdate,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(require_any_role(UserRole.TENANT_ADMIN, UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Update onboarding flow.

    Requires TENANT_ADMIN or SUPER_ADMIN role.
    """
    flow = OnboardingService.update_flow(db, flow_id, tenant.id, data)

    return schemas.OnboardingFlowResponse(
        id=flow.id,
        tenant_id=flow.tenant_id,
        title=flow.title,
        description=flow.description,
        is_active=flow.is_active,
        is_template=flow.is_template,
        display_order=flow.display_order,
        settings=flow.settings,
        module_count=flow.module_count,
        modules=[],
        created_at=flow.created_at.isoformat(),
        updated_at=flow.updated_at.isoformat()
    )


@router.delete("/flows/{flow_id}", response_model=SuccessResponse)
async def delete_flow(
    flow_id: int,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(require_any_role(UserRole.TENANT_ADMIN, UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Delete onboarding flow (soft delete).

    Requires TENANT_ADMIN or SUPER_ADMIN role.
    """
    OnboardingService.delete_flow(db, flow_id, tenant.id)

    return SuccessResponse(message="Flujo eliminado exitosamente")


@router.post("/flows/{flow_id}/clone", response_model=schemas.OnboardingFlowResponse, status_code=status.HTTP_201_CREATED)
async def clone_flow(
    flow_id: int,
    data: schemas.OnboardingFlowClone,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(require_any_role(UserRole.TENANT_ADMIN, UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Clone onboarding flow with all modules.

    Useful for creating variations. The cloned flow starts as inactive.
    Requires TENANT_ADMIN or SUPER_ADMIN role.
    """
    flow = OnboardingService.clone_flow(db, flow_id, tenant.id, data.new_title)

    modules = [
        schemas.OnboardingModuleResponse(
            id=m.id,
            flow_id=m.flow_id,
            title=m.title,
            description=m.description,
            content_type=m.content_type,
            content_text=m.content_text,
            content_url=m.content_url,
            content_id=m.content_id,
            order=m.order,
            is_required=m.is_required,
            requires_completion_confirmation=m.requires_completion_confirmation,
            quiz_data=m.quiz_data,
            estimated_minutes=m.estimated_minutes,
            created_at=m.created_at.isoformat(),
            updated_at=m.updated_at.isoformat()
        )
        for m in flow.modules
    ]

    return schemas.OnboardingFlowResponse(
        id=flow.id,
        tenant_id=flow.tenant_id,
        title=flow.title,
        description=flow.description,
        is_active=flow.is_active,
        is_template=flow.is_template,
        display_order=flow.display_order,
        settings=flow.settings,
        module_count=flow.module_count,
        modules=modules,
        created_at=flow.created_at.isoformat(),
        updated_at=flow.updated_at.isoformat()
    )


# ============================================================================
# OnboardingModule Endpoints (Admin)
# ============================================================================

@router.post("/flows/{flow_id}/modules", response_model=schemas.OnboardingModuleResponse, status_code=status.HTTP_201_CREATED)
async def create_module(
    flow_id: int,
    data: schemas.OnboardingModuleCreate,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(require_any_role(UserRole.TENANT_ADMIN, UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Create module in a flow.

    Requires TENANT_ADMIN or SUPER_ADMIN role.
    """
    module = OnboardingService.create_module(db, flow_id, tenant.id, data)

    return schemas.OnboardingModuleResponse(
        id=module.id,
        flow_id=module.flow_id,
        title=module.title,
        description=module.description,
        content_type=module.content_type,
        content_text=module.content_text,
        content_url=module.content_url,
        content_id=module.content_id,
        order=module.order,
        is_required=module.is_required,
        requires_completion_confirmation=module.requires_completion_confirmation,
        quiz_data=module.quiz_data,
        estimated_minutes=module.estimated_minutes,
        created_at=module.created_at.isoformat(),
        updated_at=module.updated_at.isoformat()
    )


@router.patch("/modules/{module_id}", response_model=schemas.OnboardingModuleResponse)
async def update_module(
    module_id: int,
    data: schemas.OnboardingModuleUpdate,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(require_any_role(UserRole.TENANT_ADMIN, UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Update module.

    Requires TENANT_ADMIN or SUPER_ADMIN role.
    """
    module = OnboardingService.update_module(db, module_id, data)

    # Verify module belongs to tenant
    if module.flow.tenant_id != tenant.id:
        raise ForbiddenException("Este módulo no pertenece a tu organización")

    return schemas.OnboardingModuleResponse(
        id=module.id,
        flow_id=module.flow_id,
        title=module.title,
        description=module.description,
        content_type=module.content_type,
        content_text=module.content_text,
        content_url=module.content_url,
        content_id=module.content_id,
        order=module.order,
        is_required=module.is_required,
        requires_completion_confirmation=module.requires_completion_confirmation,
        quiz_data=module.quiz_data,
        estimated_minutes=module.estimated_minutes,
        created_at=module.created_at.isoformat(),
        updated_at=module.updated_at.isoformat()
    )


@router.delete("/modules/{module_id}", response_model=SuccessResponse)
async def delete_module(
    module_id: int,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(require_any_role(UserRole.TENANT_ADMIN, UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Delete module.

    Requires TENANT_ADMIN or SUPER_ADMIN role.
    """
    module = OnboardingService.get_module(db, module_id)

    # Verify module belongs to tenant
    if module.flow.tenant_id != tenant.id:
        raise ForbiddenException("Este módulo no pertenece a tu organización")

    OnboardingService.delete_module(db, module_id)

    return SuccessResponse(message="Módulo eliminado exitosamente")


# ============================================================================
# Assignment Endpoints (Admin)
# ============================================================================

@router.post("/assignments", response_model=schemas.OnboardingAssignmentResponse, status_code=status.HTTP_201_CREATED)
async def assign_flow(
    data: schemas.OnboardingAssignmentCreate,
    background_tasks: BackgroundTasks,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(require_any_role(UserRole.TENANT_ADMIN, UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Assign flow to a user.

    Creates assignment and module progress records.
    Sends email notification to assigned user.
    Requires TENANT_ADMIN or SUPER_ADMIN role.
    """
    assignment = OnboardingService.assign_flow(db, tenant.id, data, current_user.id)

    # Send onboarding assignment email in background
    assigned_user = db.query(User).filter(User.id == assignment.user_id).first()
    if assigned_user:
        background_tasks.add_task(
            NotificationService.send_onboarding_assigned_email,
            db,
            assigned_user.email,
            assigned_user.full_name,
            assignment.flow.title,
            tenant.id,
            tenant,
            assigned_user.id
        )

    module_progress = [
        schemas.ModuleProgressResponse(
            id=p.id,
            module_id=p.module_id,
            module_title=p.module.title,
            module_order=p.module.order,
            content_type=p.module.content_type,
            is_completed=p.is_completed,
            completed_at=p.completed_at.isoformat() if p.completed_at else None,
            time_spent_minutes=p.time_spent_minutes,
            quiz_score=p.quiz_score,
            quiz_passed=p.quiz_passed
        )
        for p in assignment.module_progress
    ]

    return schemas.OnboardingAssignmentResponse(
        id=assignment.id,
        flow_id=assignment.flow_id,
        flow_title=assignment.flow.title,
        user_id=assignment.user_id,
        status=assignment.status,
        completion_percentage=assignment.completion_percentage,
        assigned_at=assignment.assigned_at.isoformat(),
        started_at=assignment.started_at.isoformat() if assignment.started_at else None,
        completed_at=assignment.completed_at.isoformat() if assignment.completed_at else None,
        due_date=assignment.due_date.isoformat() if assignment.due_date else None,
        is_overdue=assignment.is_overdue,
        days_since_assignment=assignment.days_since_assignment,
        module_progress=module_progress
    )


@router.post("/assignments/bulk", response_model=list[schemas.OnboardingAssignmentResponse], status_code=status.HTTP_201_CREATED)
async def bulk_assign_flow(
    data: schemas.BulkAssignmentCreate,
    background_tasks: BackgroundTasks,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(require_any_role(UserRole.TENANT_ADMIN, UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Assign flow to multiple users at once.

    Skips users who already have the flow assigned.
    Sends email notifications to all assigned users.
    Requires TENANT_ADMIN or SUPER_ADMIN role.
    """
    assignments = OnboardingService.bulk_assign_flow(db, tenant.id, data, current_user.id)

    # Send onboarding assignment emails in background for all new assignments
    for assignment in assignments:
        assigned_user = db.query(User).filter(User.id == assignment.user_id).first()
        if assigned_user:
            background_tasks.add_task(
                NotificationService.send_onboarding_assigned_email,
                db,
                assigned_user.email,
                assigned_user.full_name,
                assignment.flow.title,
                tenant.id,
                tenant,
                assigned_user.id
            )

    return [
        schemas.OnboardingAssignmentResponse(
            id=a.id,
            flow_id=a.flow_id,
            flow_title=a.flow.title,
            user_id=a.user_id,
            status=a.status,
            completion_percentage=a.completion_percentage,
            assigned_at=a.assigned_at.isoformat(),
            started_at=a.started_at.isoformat() if a.started_at else None,
            completed_at=a.completed_at.isoformat() if a.completed_at else None,
            due_date=a.due_date.isoformat() if a.due_date else None,
            is_overdue=a.is_overdue,
            days_since_assignment=a.days_since_assignment,
            module_progress=[]
        )
        for a in assignments
    ]


@router.get("/assignments", response_model=PaginatedResponse[schemas.OnboardingAssignmentListResponse])
async def list_assignments(
    filters: schemas.AssignmentFilterParams = Depends(),
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(require_any_role(UserRole.TENANT_ADMIN, UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    List assignments with filters.

    Requires TENANT_ADMIN or SUPER_ADMIN role.
    """
    assignments, total = OnboardingService.list_assignments(db, tenant.id, filters)

    assignment_responses = [
        schemas.OnboardingAssignmentListResponse(
            id=a.id,
            flow_id=a.flow_id,
            flow_title=a.flow.title,
            user_id=a.user_id,
            user_name=a.user.full_name,
            user_email=a.user.email,
            status=a.status,
            completion_percentage=a.completion_percentage,
            assigned_at=a.assigned_at.isoformat(),
            due_date=a.due_date.isoformat() if a.due_date else None,
            is_overdue=a.is_overdue
        )
        for a in assignments
    ]

    return PaginatedResponse(
        data=assignment_responses,
        total=total,
        page=filters.page,
        page_size=filters.page_size,
        total_pages=(total + filters.page_size - 1) // filters.page_size
    )


@router.get("/assignments/{assignment_id}", response_model=schemas.OnboardingAssignmentResponse)
async def get_assignment(
    assignment_id: int,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get assignment details with progress.

    Users can view their own assignments, admins can view all.
    """
    assignment = OnboardingService.get_assignment(db, assignment_id, tenant.id)

    # Verify user can access this assignment
    if assignment.user_id != current_user.id and current_user.role not in [UserRole.TENANT_ADMIN.value, UserRole.SUPER_ADMIN.value]:
        raise ForbiddenException("No puedes ver esta asignación")

    module_progress = [
        schemas.ModuleProgressResponse(
            id=p.id,
            module_id=p.module_id,
            module_title=p.module.title,
            module_order=p.module.order,
            content_type=p.module.content_type,
            is_completed=p.is_completed,
            completed_at=p.completed_at.isoformat() if p.completed_at else None,
            time_spent_minutes=p.time_spent_minutes,
            quiz_score=p.quiz_score,
            quiz_passed=p.quiz_passed
        )
        for p in assignment.module_progress
    ]

    return schemas.OnboardingAssignmentResponse(
        id=assignment.id,
        flow_id=assignment.flow_id,
        flow_title=assignment.flow.title,
        user_id=assignment.user_id,
        status=assignment.status,
        completion_percentage=assignment.completion_percentage,
        assigned_at=assignment.assigned_at.isoformat(),
        started_at=assignment.started_at.isoformat() if assignment.started_at else None,
        completed_at=assignment.completed_at.isoformat() if assignment.completed_at else None,
        due_date=assignment.due_date.isoformat() if assignment.due_date else None,
        is_overdue=assignment.is_overdue,
        days_since_assignment=assignment.days_since_assignment,
        module_progress=module_progress
    )


# ============================================================================
# Employee Endpoints (Module Completion)
# ============================================================================

@router.get("/my-assignments", response_model=schemas.EmployeeDashboardResponse)
async def get_my_assignments(
    current_user: User = Depends(get_current_active_user),
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    Get employee dashboard with all their assignments.

    Returns statistics and list of assignments.
    """
    dashboard = OnboardingService.get_employee_dashboard(db, current_user.id, tenant.id)

    assignment_responses = [
        schemas.OnboardingAssignmentResponse(
            id=a.id,
            flow_id=a.flow_id,
            flow_title=a.flow.title,
            user_id=a.user_id,
            status=a.status,
            completion_percentage=a.completion_percentage,
            assigned_at=a.assigned_at.isoformat(),
            started_at=a.started_at.isoformat() if a.started_at else None,
            completed_at=a.completed_at.isoformat() if a.completed_at else None,
            due_date=a.due_date.isoformat() if a.due_date else None,
            is_overdue=a.is_overdue,
            days_since_assignment=a.days_since_assignment,
            module_progress=[
                schemas.ModuleProgressResponse(
                    id=p.id,
                    module_id=p.module_id,
                    module_title=p.module.title,
                    module_order=p.module.order,
                    content_type=p.module.content_type,
                    is_completed=p.is_completed,
                    completed_at=p.completed_at.isoformat() if p.completed_at else None,
                    time_spent_minutes=p.time_spent_minutes,
                    quiz_score=p.quiz_score,
                    quiz_passed=p.quiz_passed
                )
                for p in a.module_progress
            ]
        )
        for a in dashboard["assignments"]
    ]

    return schemas.EmployeeDashboardResponse(
        total_assignments=dashboard["total_assignments"],
        completed=dashboard["completed"],
        in_progress=dashboard["in_progress"],
        not_started=dashboard["not_started"],
        overdue=dashboard["overdue"],
        assignments=assignment_responses
    )


@router.post("/assignments/{assignment_id}/modules/{module_id}/complete", response_model=schemas.ModuleProgressResponse)
async def complete_module(
    assignment_id: int,
    module_id: int,
    data: schemas.CompleteModuleRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Mark module as completed.

    Updates assignment progress automatically.
    """
    progress = OnboardingService.complete_module(
        db,
        assignment_id,
        module_id,
        current_user.id,
        data
    )

    return schemas.ModuleProgressResponse(
        id=progress.id,
        module_id=progress.module_id,
        module_title=progress.module.title,
        module_order=progress.module.order,
        content_type=progress.module.content_type,
        is_completed=progress.is_completed,
        completed_at=progress.completed_at.isoformat() if progress.completed_at else None,
        time_spent_minutes=progress.time_spent_minutes,
        quiz_score=progress.quiz_score,
        quiz_passed=progress.quiz_passed
    )


@router.post("/assignments/{assignment_id}/modules/{module_id}/quiz", response_model=schemas.QuizResultResponse)
async def submit_quiz(
    assignment_id: int,
    module_id: int,
    data: schemas.SubmitQuizRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Submit quiz answers.

    Calculates score and marks module as completed if passed.
    """
    result = OnboardingService.submit_quiz(
        db,
        assignment_id,
        module_id,
        current_user.id,
        data
    )

    return schemas.QuizResultResponse(
        score=result["score"],
        passed=result["passed"],
        passing_score=result["passing_score"],
        correct_answers=result["correct_answers"],
        total_questions=result["total_questions"]
    )
