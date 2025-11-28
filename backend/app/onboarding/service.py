"""
Onboarding service for business logic operations.
Handles CRUD for flows, modules, assignments and progress tracking.
"""

from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.core.enums import OnboardingStatus
from app.onboarding.models import (
    OnboardingFlow,
    OnboardingModule,
    OnboardingAssignment,
    ModuleProgress
)
from app.onboarding import schemas
from app.onboarding.exceptions import (
    FlowNotFoundException,
    ModuleNotFoundException,
    AssignmentNotFoundException,
    ProgressNotFoundException,
    FlowAlreadyAssignedException,
    ModuleNotInFlowException,
    NotAQuizModuleException,
    InvalidQuizDataException
)


class OnboardingService:
    """Service class for onboarding operations."""

    # =========================================================================
    # Flow CRUD Operations
    # =========================================================================

    @staticmethod
    def create_flow(
        db: Session,
        tenant_id: int,
        data: schemas.OnboardingFlowCreate
    ) -> OnboardingFlow:
        """Create a new onboarding flow."""
        flow = OnboardingFlow(
            tenant_id=tenant_id,
            title=data.title,
            description=data.description,
            is_active=data.is_active,
            settings=data.settings or {}
        )

        db.add(flow)
        db.commit()
        db.refresh(flow)

        return flow

    @staticmethod
    def get_flow(db: Session, flow_id: int, tenant_id: int) -> OnboardingFlow:
        """Get flow by ID."""
        flow = db.query(OnboardingFlow).filter(
            OnboardingFlow.id == flow_id,
            OnboardingFlow.tenant_id == tenant_id,
            OnboardingFlow.deleted_at.is_(None)
        ).first()

        if not flow:
            raise FlowNotFoundException()

        return flow

    @staticmethod
    def list_flows(
        db: Session,
        tenant_id: int,
        include_inactive: bool = False
    ) -> list[OnboardingFlow]:
        """List all flows for a tenant."""
        query = db.query(OnboardingFlow).filter(
            OnboardingFlow.tenant_id == tenant_id,
            OnboardingFlow.deleted_at.is_(None)
        )

        if not include_inactive:
            query = query.filter(OnboardingFlow.is_active == True)

        return query.order_by(
            OnboardingFlow.display_order,
            OnboardingFlow.created_at.desc()
        ).all()

    @staticmethod
    def update_flow(
        db: Session,
        flow_id: int,
        tenant_id: int,
        data: schemas.OnboardingFlowUpdate
    ) -> OnboardingFlow:
        """Update a flow."""
        flow = OnboardingService.get_flow(db, flow_id, tenant_id)

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(flow, field, value)

        db.commit()
        db.refresh(flow)

        return flow

    @staticmethod
    def delete_flow(db: Session, flow_id: int, tenant_id: int) -> bool:
        """Soft delete a flow."""
        flow = OnboardingService.get_flow(db, flow_id, tenant_id)

        flow.deleted_at = datetime.now(timezone.utc)
        flow.is_active = False

        db.commit()

        return True

    @staticmethod
    def clone_flow(
        db: Session,
        flow_id: int,
        tenant_id: int,
        new_title: str
    ) -> OnboardingFlow:
        """Clone a flow with all its modules."""
        original = OnboardingService.get_flow(db, flow_id, tenant_id)

        # Clone flow
        new_flow = OnboardingFlow(
            tenant_id=tenant_id,
            title=new_title,
            description=original.description,
            is_active=True,
            is_template=False,
            settings=original.settings.copy() if original.settings else {}
        )

        db.add(new_flow)
        db.flush()

        # Clone modules
        for module in original.modules:
            new_module = OnboardingModule(
                flow_id=new_flow.id,
                title=module.title,
                description=module.description,
                content_type=module.content_type,
                content_text=module.content_text,
                content_url=module.content_url,
                order=module.order,
                is_required=module.is_required,
                requires_completion_confirmation=module.requires_completion_confirmation,
                quiz_data=module.quiz_data.copy() if module.quiz_data else None,
                estimated_minutes=module.estimated_minutes
            )
            db.add(new_module)

        db.commit()
        db.refresh(new_flow)

        return new_flow

    # =========================================================================
    # Module CRUD Operations
    # =========================================================================

    @staticmethod
    def create_module(
        db: Session,
        flow_id: int,
        tenant_id: int,
        data: schemas.OnboardingModuleCreate
    ) -> OnboardingModule:
        """Create a module in a flow."""
        # Verify flow exists and belongs to tenant
        flow = OnboardingService.get_flow(db, flow_id, tenant_id)

        module = OnboardingModule(
            flow_id=flow.id,
            title=data.title,
            description=data.description,
            content_type=data.content_type,
            content_text=data.content_text,
            content_url=data.content_url,
            order=data.order,
            is_required=data.is_required,
            requires_completion_confirmation=data.requires_completion_confirmation,
            quiz_data=data.quiz_data,
            estimated_minutes=data.estimated_minutes
        )

        db.add(module)
        db.commit()
        db.refresh(module)

        return module

    @staticmethod
    def get_module(db: Session, module_id: int) -> OnboardingModule:
        """Get module by ID."""
        module = db.query(OnboardingModule).filter(
            OnboardingModule.id == module_id
        ).first()

        if not module:
            raise ModuleNotFoundException()

        return module

    @staticmethod
    def update_module(
        db: Session,
        module_id: int,
        data: schemas.OnboardingModuleUpdate
    ) -> OnboardingModule:
        """Update a module."""
        module = OnboardingService.get_module(db, module_id)

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(module, field, value)

        db.commit()
        db.refresh(module)

        return module

    @staticmethod
    def delete_module(db: Session, module_id: int) -> bool:
        """Delete a module."""
        module = OnboardingService.get_module(db, module_id)

        db.delete(module)
        db.commit()

        return True

    @staticmethod
    def reorder_modules(
        db: Session,
        flow_id: int,
        tenant_id: int,
        module_orders: dict[int, int]
    ) -> bool:
        """Reorder modules in a flow."""
        # Verify flow exists
        flow = OnboardingService.get_flow(db, flow_id, tenant_id)

        for module_id, new_order in module_orders.items():
            module = OnboardingService.get_module(db, module_id)

            if module.flow_id != flow.id:
                raise ModuleNotInFlowException()

            module.order = new_order

        db.commit()

        return True

    # =========================================================================
    # Assignment Operations
    # =========================================================================

    @staticmethod
    def assign_flow(
        db: Session,
        tenant_id: int,
        data: schemas.OnboardingAssignmentCreate,
        assigned_by_id: int
    ) -> OnboardingAssignment:
        """Assign a flow to a user."""
        # Verify flow exists
        flow = OnboardingService.get_flow(db, data.flow_id, tenant_id)

        # Check for existing active assignment
        existing = db.query(OnboardingAssignment).filter(
            and_(
                OnboardingAssignment.flow_id == data.flow_id,
                OnboardingAssignment.user_id == data.user_id,
                OnboardingAssignment.status != OnboardingStatus.COMPLETED.value
            )
        ).first()

        if existing:
            raise FlowAlreadyAssignedException()

        # Create assignment
        assignment = OnboardingAssignment(
            flow_id=data.flow_id,
            user_id=data.user_id,
            tenant_id=tenant_id,
            assigned_by=assigned_by_id,
            due_date=data.due_date
        )

        db.add(assignment)
        db.flush()

        # Create ModuleProgress for each module
        for module in flow.modules:
            progress = ModuleProgress(
                assignment_id=assignment.id,
                module_id=module.id
            )
            db.add(progress)

        db.commit()
        db.refresh(assignment)

        return assignment

    @staticmethod
    def bulk_assign_flow(
        db: Session,
        tenant_id: int,
        data: schemas.BulkAssignmentCreate,
        assigned_by_id: int
    ) -> list[OnboardingAssignment]:
        """Assign a flow to multiple users."""
        assignments = []

        for user_id in data.user_ids:
            try:
                single_data = schemas.OnboardingAssignmentCreate(
                    flow_id=data.flow_id,
                    user_id=user_id,
                    due_date=data.due_date
                )
                assignment = OnboardingService.assign_flow(
                    db, tenant_id, single_data, assigned_by_id
                )
                assignments.append(assignment)
            except FlowAlreadyAssignedException:
                # Skip users who already have the assignment
                continue

        return assignments

    @staticmethod
    def get_assignment(
        db: Session,
        assignment_id: int,
        tenant_id: int
    ) -> OnboardingAssignment:
        """Get assignment by ID."""
        assignment = db.query(OnboardingAssignment).filter(
            OnboardingAssignment.id == assignment_id,
            OnboardingAssignment.tenant_id == tenant_id
        ).first()

        if not assignment:
            raise AssignmentNotFoundException()

        return assignment

    @staticmethod
    def get_user_assignments(
        db: Session,
        user_id: int,
        tenant_id: int
    ) -> list[OnboardingAssignment]:
        """Get all assignments for a user."""
        return db.query(OnboardingAssignment).filter(
            OnboardingAssignment.user_id == user_id,
            OnboardingAssignment.tenant_id == tenant_id
        ).order_by(OnboardingAssignment.assigned_at.desc()).all()

    @staticmethod
    def list_assignments(
        db: Session,
        tenant_id: int,
        filters: schemas.AssignmentFilterParams
    ) -> tuple[list[OnboardingAssignment], int]:
        """List assignments with filters and pagination."""
        query = db.query(OnboardingAssignment).filter(
            OnboardingAssignment.tenant_id == tenant_id
        )

        # Apply filters
        if filters.status:
            query = query.filter(OnboardingAssignment.status == filters.status)

        if filters.flow_id:
            query = query.filter(OnboardingAssignment.flow_id == filters.flow_id)

        if filters.user_id:
            query = query.filter(OnboardingAssignment.user_id == filters.user_id)

        # Get total count
        total = query.count()

        # Apply pagination
        assignments = query.order_by(
            OnboardingAssignment.assigned_at.desc()
        ).offset(filters.offset).limit(filters.page_size).all()

        # Filter overdue if needed (in memory as it's a computed property)
        if filters.is_overdue is not None:
            assignments = [a for a in assignments if a.is_overdue == filters.is_overdue]

        return assignments, total

    @staticmethod
    def delete_assignment(
        db: Session,
        assignment_id: int,
        tenant_id: int
    ) -> bool:
        """Delete an assignment."""
        assignment = OnboardingService.get_assignment(db, assignment_id, tenant_id)

        db.delete(assignment)
        db.commit()

        return True

    # =========================================================================
    # Progress Operations
    # =========================================================================

    @staticmethod
    def complete_module(
        db: Session,
        assignment_id: int,
        module_id: int,
        user_id: int,
        data: schemas.CompleteModuleRequest
    ) -> ModuleProgress:
        """Mark a module as completed."""
        # Get progress record
        progress = db.query(ModuleProgress).filter(
            ModuleProgress.assignment_id == assignment_id,
            ModuleProgress.module_id == module_id
        ).first()

        if not progress:
            raise ProgressNotFoundException()

        # Verify user owns the assignment
        if progress.assignment.user_id != user_id:
            from app.core.exceptions import ForbiddenException
            raise ForbiddenException("No puedes completar este módulo")

        # Mark as completed
        progress.is_completed = True
        progress.completed_at = datetime.now(timezone.utc)

        if data.notes:
            progress.notes = data.notes

        if data.time_spent_minutes:
            progress.time_spent_minutes = data.time_spent_minutes

        # Update assignment status
        assignment = progress.assignment
        if not assignment.started_at:
            assignment.started_at = datetime.now(timezone.utc)
            assignment.status = OnboardingStatus.IN_PROGRESS.value

        # Recalculate progress
        OnboardingService._update_assignment_progress(db, assignment)

        db.commit()
        db.refresh(progress)

        return progress

    @staticmethod
    def submit_quiz(
        db: Session,
        assignment_id: int,
        module_id: int,
        user_id: int,
        data: schemas.SubmitQuizRequest
    ) -> ModuleProgress:
        """Submit quiz answers and grade."""
        # Get progress and module
        progress = db.query(ModuleProgress).filter(
            ModuleProgress.assignment_id == assignment_id,
            ModuleProgress.module_id == module_id
        ).first()

        if not progress:
            raise ProgressNotFoundException()

        module = progress.module

        if module.content_type != "quiz":
            raise NotAQuizModuleException()

        # Verify user owns the assignment
        if progress.assignment.user_id != user_id:
            from app.core.exceptions import ForbiddenException
            raise ForbiddenException("No puedes enviar este quiz")

        # Grade quiz
        quiz_data = module.quiz_data
        if not quiz_data:
            raise InvalidQuizDataException()

        questions = quiz_data.get("questions", [])
        passing_score = quiz_data.get("passing_score", 70)

        if not questions:
            raise InvalidQuizDataException("El quiz no tiene preguntas")

        correct_count = 0
        for i, question in enumerate(questions):
            user_answer = data.answers.get(str(i))
            if user_answer == question.get("correct_answer"):
                correct_count += 1

        score = int((correct_count / len(questions)) * 100)
        passed = score >= passing_score

        # Update progress
        progress.quiz_score = score
        progress.quiz_passed = passed

        if passed:
            progress.is_completed = True
            progress.completed_at = datetime.now(timezone.utc)

        if data.time_spent_minutes:
            progress.time_spent_minutes = data.time_spent_minutes

        # Update assignment status
        assignment = progress.assignment
        if not assignment.started_at:
            assignment.started_at = datetime.now(timezone.utc)
            assignment.status = OnboardingStatus.IN_PROGRESS.value

        OnboardingService._update_assignment_progress(db, assignment)

        db.commit()
        db.refresh(progress)

        return progress

    @staticmethod
    def _update_assignment_progress(
        db: Session,
        assignment: OnboardingAssignment
    ) -> None:
        """Recalculate assignment completion percentage and status."""
        total_modules = len(assignment.flow.modules)

        if total_modules == 0:
            assignment.completion_percentage = 100
            assignment.status = OnboardingStatus.COMPLETED.value
            assignment.completed_at = datetime.now(timezone.utc)
            return

        completed_count = sum(1 for p in assignment.module_progress if p.is_completed)
        assignment.completion_percentage = int((completed_count / total_modules) * 100)

        # Check if all REQUIRED modules are completed
        required_modules = [m for m in assignment.flow.modules if m.is_required]

        if required_modules:
            required_completed = all(
                any(p.module_id == m.id and p.is_completed for p in assignment.module_progress)
                for m in required_modules
            )

            if required_completed:
                assignment.status = OnboardingStatus.COMPLETED.value
                assignment.completed_at = datetime.now(timezone.utc)
            elif assignment.completion_percentage > 0:
                assignment.status = OnboardingStatus.IN_PROGRESS.value
        else:
            # No required modules, complete when all are done
            if completed_count == total_modules:
                assignment.status = OnboardingStatus.COMPLETED.value
                assignment.completed_at = datetime.now(timezone.utc)

    @staticmethod
    def get_employee_dashboard(
        db: Session,
        user_id: int,
        tenant_id: int
    ) -> dict:
        """Get dashboard summary for an employee."""
        assignments = OnboardingService.get_user_assignments(db, user_id, tenant_id)

        completed = sum(1 for a in assignments if a.status == OnboardingStatus.COMPLETED.value)
        in_progress = sum(1 for a in assignments if a.status == OnboardingStatus.IN_PROGRESS.value)
        not_started = sum(1 for a in assignments if a.status == OnboardingStatus.NOT_STARTED.value)
        overdue = sum(1 for a in assignments if a.is_overdue)

        return {
            "total_assignments": len(assignments),
            "completed": completed,
            "in_progress": in_progress,
            "not_started": not_started,
            "overdue": overdue,
            "assignments": assignments
        }
