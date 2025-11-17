"""
Onboarding service.
Business logic for onboarding flows, modules, assignments, and progress tracking.
"""

from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.core.exceptions import NotFoundException, ValidationException, ForbiddenException
from app.onboarding.models import (
    OnboardingFlow,
    OnboardingModule,
    OnboardingAssignment,
    ModuleProgress
)
from app.onboarding import schemas
from app.core.enums import OnboardingStatus


class OnboardingService:
    """Service for onboarding management."""

    # =========================================================================
    # OnboardingFlow CRUD
    # =========================================================================

    @staticmethod
    def create_flow(db: Session, tenant_id: int, data: schemas.OnboardingFlowCreate) -> OnboardingFlow:
        """Create onboarding flow."""
        flow = OnboardingFlow(
            **data.model_dump(),
            tenant_id=tenant_id
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
            raise NotFoundException("Flujo de onboarding")

        return flow

    @staticmethod
    def list_flows(
        db: Session,
        tenant_id: int,
        include_inactive: bool = False
    ) -> list[OnboardingFlow]:
        """List flows for tenant."""
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
        """Update flow."""
        flow = OnboardingService.get_flow(db, flow_id, tenant_id)

        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(flow, field, value)

        db.commit()
        db.refresh(flow)

        return flow

    @staticmethod
    def delete_flow(db: Session, flow_id: int, tenant_id: int) -> bool:
        """Soft delete flow."""
        flow = OnboardingService.get_flow(db, flow_id, tenant_id)
        flow.deleted_at = datetime.utcnow()
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
        """
        Clone flow with all its modules.

        Useful for creating variations of existing flows.
        """
        original = OnboardingService.get_flow(db, flow_id, tenant_id)

        # Clone flow
        new_flow = OnboardingFlow(
            tenant_id=tenant_id,
            title=new_title,
            description=original.description,
            settings=original.settings.copy() if original.settings else {},
            is_active=False  # Start as inactive
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
                content_id=module.content_id,
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
    # OnboardingModule CRUD
    # =========================================================================

    @staticmethod
    def create_module(
        db: Session,
        flow_id: int,
        tenant_id: int,
        data: schemas.OnboardingModuleCreate
    ) -> OnboardingModule:
        """Create module in a flow."""
        # Verify flow exists and belongs to tenant
        flow = OnboardingService.get_flow(db, flow_id, tenant_id)

        module = OnboardingModule(
            **data.model_dump(),
            flow_id=flow_id
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
            raise NotFoundException("Módulo")

        return module

    @staticmethod
    def update_module(
        db: Session,
        module_id: int,
        data: schemas.OnboardingModuleUpdate
    ) -> OnboardingModule:
        """Update module."""
        module = OnboardingService.get_module(db, module_id)

        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(module, field, value)

        db.commit()
        db.refresh(module)

        return module

    @staticmethod
    def delete_module(db: Session, module_id: int) -> bool:
        """Delete module."""
        module = OnboardingService.get_module(db, module_id)
        db.delete(module)
        db.commit()

        return True

    @staticmethod
    def reorder_modules(
        db: Session,
        flow_id: int,
        module_orders: dict[int, int]
    ) -> bool:
        """
        Reorder modules in a flow.

        Args:
            flow_id: Flow ID
            module_orders: {module_id: new_order}
        """
        for module_id, new_order in module_orders.items():
            module = OnboardingService.get_module(db, module_id)
            if module.flow_id != flow_id:
                raise ValidationException("Módulo no pertenece a este flujo")
            module.order = new_order

        db.commit()
        return True

    # =========================================================================
    # Assignments
    # =========================================================================

    @staticmethod
    def assign_flow(
        db: Session,
        tenant_id: int,
        data: schemas.OnboardingAssignmentCreate,
        assigned_by_id: int
    ) -> OnboardingAssignment:
        """
        Assign flow to an employee.

        Creates the assignment and ModuleProgress for each module.
        """
        # Verify flow exists
        flow = OnboardingService.get_flow(db, data.flow_id, tenant_id)

        # Check user doesn't already have this flow assigned
        existing = db.query(OnboardingAssignment).filter(
            and_(
                OnboardingAssignment.flow_id == data.flow_id,
                OnboardingAssignment.user_id == data.user_id,
                OnboardingAssignment.status != OnboardingStatus.COMPLETED.value
            )
        ).first()

        if existing:
            raise ValidationException("Usuario ya tiene este flujo asignado")

        # Create assignment
        assignment = OnboardingAssignment(
            **data.model_dump(),
            tenant_id=tenant_id,
            assigned_by=assigned_by_id
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
        """Assign flow to multiple users."""
        assignments = []

        for user_id in data.user_ids:
            assignment_data = schemas.OnboardingAssignmentCreate(
                flow_id=data.flow_id,
                user_id=user_id,
                due_date=data.due_date
            )

            try:
                assignment = OnboardingService.assign_flow(
                    db,
                    tenant_id,
                    assignment_data,
                    assigned_by_id
                )
                assignments.append(assignment)
            except ValidationException:
                # Skip if user already has flow assigned
                continue

        return assignments

    @staticmethod
    def get_assignment(db: Session, assignment_id: int, tenant_id: int) -> OnboardingAssignment:
        """Get assignment by ID."""
        assignment = db.query(OnboardingAssignment).filter(
            OnboardingAssignment.id == assignment_id,
            OnboardingAssignment.tenant_id == tenant_id
        ).first()

        if not assignment:
            raise NotFoundException("Asignación")

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
            query = query.filter(OnboardingAssignment.status == filters.status.value)

        if filters.user_id:
            query = query.filter(OnboardingAssignment.user_id == filters.user_id)

        if filters.flow_id:
            query = query.filter(OnboardingAssignment.flow_id == filters.flow_id)

        if filters.overdue_only:
            query = query.filter(
                OnboardingAssignment.due_date.isnot(None),
                OnboardingAssignment.due_date < datetime.utcnow(),
                OnboardingAssignment.status != OnboardingStatus.COMPLETED.value
            )

        # Get total count
        total = query.count()

        # Apply pagination
        assignments = query.offset(filters.offset).limit(filters.page_size).all()

        return assignments, total

    # =========================================================================
    # Module Progress
    # =========================================================================

    @staticmethod
    def complete_module(
        db: Session,
        assignment_id: int,
        module_id: int,
        user_id: int,
        data: schemas.CompleteModuleRequest
    ) -> ModuleProgress:
        """
        Mark module as completed.

        Updates overall assignment progress.
        """
        # Get progress
        progress = db.query(ModuleProgress).filter(
            ModuleProgress.assignment_id == assignment_id,
            ModuleProgress.module_id == module_id
        ).first()

        if not progress:
            raise NotFoundException("Progreso de módulo")

        # Verify assignment belongs to user
        if progress.assignment.user_id != user_id:
            raise ForbiddenException("No puedes completar este módulo")

        # Mark as completed
        progress.is_completed = True
        progress.completed_at = datetime.utcnow()

        if data.notes:
            progress.notes = data.notes

        if data.time_spent_minutes:
            progress.time_spent_minutes += data.time_spent_minutes

        # Update assignment status
        assignment = progress.assignment
        if assignment.status == OnboardingStatus.NOT_STARTED.value:
            assignment.status = OnboardingStatus.IN_PROGRESS.value
            assignment.started_at = datetime.utcnow()

        # Calculate completion percentage
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
    ) -> dict:
        """
        Submit quiz answers and calculate score.

        Returns quiz results and marks module as completed if passed.
        """
        # Get progress
        progress = db.query(ModuleProgress).filter(
            ModuleProgress.assignment_id == assignment_id,
            ModuleProgress.module_id == module_id
        ).first()

        if not progress:
            raise NotFoundException("Progreso de módulo")

        # Verify assignment belongs to user
        if progress.assignment.user_id != user_id:
            raise ForbiddenException("No puedes enviar este quiz")

        # Get module and quiz data
        module = progress.module
        if not module.quiz_data:
            raise ValidationException("Este módulo no es un quiz")

        quiz_data = module.quiz_data
        questions = quiz_data.get("questions", [])
        passing_score = quiz_data.get("passing_score", 70)

        # Calculate score
        correct_answers = 0
        for i, question in enumerate(questions):
            user_answer = data.answers.get(str(i))
            correct = question.get("correct_answer")

            if user_answer == correct:
                correct_answers += 1

        score = int((correct_answers / len(questions)) * 100) if questions else 0
        passed = score >= passing_score

        # Update progress
        progress.quiz_score = score
        progress.quiz_passed = passed
        progress.quiz_answers = data.answers

        if data.time_spent_minutes:
            progress.time_spent_minutes += data.time_spent_minutes

        # Mark as completed if passed
        if passed:
            progress.is_completed = True
            progress.completed_at = datetime.utcnow()

            # Update assignment progress
            assignment = progress.assignment
            if assignment.status == OnboardingStatus.NOT_STARTED.value:
                assignment.status = OnboardingStatus.IN_PROGRESS.value
                assignment.started_at = datetime.utcnow()

            OnboardingService._update_assignment_progress(db, assignment)

        db.commit()

        return {
            "score": score,
            "passed": passed,
            "passing_score": passing_score,
            "correct_answers": correct_answers,
            "total_questions": len(questions)
        }

    @staticmethod
    def _update_assignment_progress(db: Session, assignment: OnboardingAssignment) -> None:
        """
        Update assignment completion percentage and status.

        Internal helper method.
        """
        # Get all progress records
        total_modules = len(assignment.module_progress)
        if total_modules == 0:
            assignment.completion_percentage = 0
            return

        completed_modules = sum(1 for p in assignment.module_progress if p.is_completed)
        percentage = int((completed_modules / total_modules) * 100)

        assignment.completion_percentage = percentage

        # Update status if fully completed
        if percentage == 100:
            assignment.status = OnboardingStatus.COMPLETED.value
            if not assignment.completed_at:
                assignment.completed_at = datetime.utcnow()

    @staticmethod
    def get_employee_dashboard(
        db: Session,
        user_id: int,
        tenant_id: int
    ) -> dict:
        """
        Get employee dashboard with all assignments and stats.

        Returns summary statistics and list of assignments.
        """
        assignments = OnboardingService.get_user_assignments(db, user_id, tenant_id)

        stats = {
            "total_assignments": len(assignments),
            "completed": 0,
            "in_progress": 0,
            "not_started": 0,
            "overdue": 0
        }

        for assignment in assignments:
            if assignment.status == OnboardingStatus.COMPLETED.value:
                stats["completed"] += 1
            elif assignment.status == OnboardingStatus.IN_PROGRESS.value:
                stats["in_progress"] += 1
            elif assignment.status == OnboardingStatus.NOT_STARTED.value:
                stats["not_started"] += 1

            if assignment.is_overdue:
                stats["overdue"] += 1

        return {
            **stats,
            "assignments": assignments
        }
