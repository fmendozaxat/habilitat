"""
Analytics service for metrics and reporting.
"""

from datetime import datetime, timedelta, date, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.enums import OnboardingStatus
from app.onboarding.models import OnboardingFlow, OnboardingAssignment, ModuleProgress
from app.users.models import User
from app.analytics import schemas


class AnalyticsService:
    """Service class for analytics and reporting."""

    @staticmethod
    def get_dashboard_overview(db: Session, tenant_id: int) -> schemas.DashboardOverviewResponse:
        """Get dashboard overview metrics."""
        now = datetime.now(timezone.utc)
        week_ago = now - timedelta(days=7)

        # Total users
        total_users = db.query(func.count(User.id)).filter(
            User.tenant_id == tenant_id,
            User.is_active == True,
            User.deleted_at.is_(None)
        ).scalar() or 0

        # Total flows
        total_flows = db.query(func.count(OnboardingFlow.id)).filter(
            OnboardingFlow.tenant_id == tenant_id,
            OnboardingFlow.is_active == True,
            OnboardingFlow.deleted_at.is_(None)
        ).scalar() or 0

        # Total assignments
        total_assignments = db.query(func.count(OnboardingAssignment.id)).filter(
            OnboardingAssignment.tenant_id == tenant_id
        ).scalar() or 0

        # Status breakdown
        assignments_not_started = db.query(func.count(OnboardingAssignment.id)).filter(
            OnboardingAssignment.tenant_id == tenant_id,
            OnboardingAssignment.status == OnboardingStatus.NOT_STARTED.value
        ).scalar() or 0

        assignments_in_progress = db.query(func.count(OnboardingAssignment.id)).filter(
            OnboardingAssignment.tenant_id == tenant_id,
            OnboardingAssignment.status == OnboardingStatus.IN_PROGRESS.value
        ).scalar() or 0

        assignments_completed = db.query(func.count(OnboardingAssignment.id)).filter(
            OnboardingAssignment.tenant_id == tenant_id,
            OnboardingAssignment.status == OnboardingStatus.COMPLETED.value
        ).scalar() or 0

        # Overdue
        assignments_overdue = db.query(func.count(OnboardingAssignment.id)).filter(
            OnboardingAssignment.tenant_id == tenant_id,
            OnboardingAssignment.status != OnboardingStatus.COMPLETED.value,
            OnboardingAssignment.due_date < now,
            OnboardingAssignment.due_date.isnot(None)
        ).scalar() or 0

        # Completion rate
        completion_rate = (assignments_completed / total_assignments * 100) if total_assignments > 0 else 0

        # Avg completion time
        completed_assignments = db.query(OnboardingAssignment).filter(
            OnboardingAssignment.tenant_id == tenant_id,
            OnboardingAssignment.status == OnboardingStatus.COMPLETED.value,
            OnboardingAssignment.completed_at.isnot(None)
        ).all()

        if completed_assignments:
            completion_times = []
            for a in completed_assignments:
                assigned = a.assigned_at.replace(tzinfo=timezone.utc) if a.assigned_at.tzinfo is None else a.assigned_at
                completed = a.completed_at.replace(tzinfo=timezone.utc) if a.completed_at.tzinfo is None else a.completed_at
                completion_times.append((completed - assigned).days)
            avg_completion_time_days = sum(completion_times) / len(completion_times)
        else:
            avg_completion_time_days = 0

        # This week activity
        assignments_this_week = db.query(func.count(OnboardingAssignment.id)).filter(
            OnboardingAssignment.tenant_id == tenant_id,
            OnboardingAssignment.assigned_at >= week_ago
        ).scalar() or 0

        completions_this_week = db.query(func.count(OnboardingAssignment.id)).filter(
            OnboardingAssignment.tenant_id == tenant_id,
            OnboardingAssignment.completed_at >= week_ago,
            OnboardingAssignment.completed_at.isnot(None)
        ).scalar() or 0

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
        """Get analytics for a specific flow."""
        from app.onboarding.service import OnboardingService

        flow = OnboardingService.get_flow(db, flow_id, tenant_id)

        # Get all assignments for this flow
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
        completed = sum(1 for a in assignments if a.status == OnboardingStatus.COMPLETED.value)
        in_progress = sum(1 for a in assignments if a.status == OnboardingStatus.IN_PROGRESS.value)
        not_started = sum(1 for a in assignments if a.status == OnboardingStatus.NOT_STARTED.value)

        # Rates
        completion_rate = (completed / total_assignments * 100)
        avg_progress = sum(a.completion_percentage for a in assignments) / total_assignments

        # Avg completion time
        completed_list = [a for a in assignments if a.status == OnboardingStatus.COMPLETED.value and a.completed_at]
        if completed_list:
            completion_times = []
            for a in completed_list:
                assigned = a.assigned_at.replace(tzinfo=timezone.utc) if a.assigned_at.tzinfo is None else a.assigned_at
                completed_at = a.completed_at.replace(tzinfo=timezone.utc) if a.completed_at.tzinfo is None else a.completed_at
                completion_times.append((completed_at - assigned).days)
            avg_completion_time = sum(completion_times) / len(completion_times)
        else:
            avg_completion_time = 0

        # Hardest module
        hardest_module = None
        if flow.modules:
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
        """Get progress report for a specific user."""
        from app.users.exceptions import UserNotFoundException

        user = db.query(User).filter(
            User.id == user_id,
            User.deleted_at.is_(None)
        ).first()

        if not user:
            raise UserNotFoundException()

        # Get user assignments
        assignments = db.query(OnboardingAssignment).filter(
            OnboardingAssignment.user_id == user_id,
            OnboardingAssignment.tenant_id == tenant_id
        ).all()

        total_assignments = len(assignments)
        completed = sum(1 for a in assignments if a.status == OnboardingStatus.COMPLETED.value)
        in_progress = sum(1 for a in assignments if a.status == OnboardingStatus.IN_PROGRESS.value)

        # Overall progress
        overall_progress = (sum(a.completion_percentage for a in assignments) / total_assignments) if total_assignments > 0 else 0

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
                "assigned_at": a.assigned_at.isoformat() if a.assigned_at else None,
                "completed_at": a.completed_at.isoformat() if a.completed_at else None,
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
        """Get completion trends over a date range."""
        # Query completions by date
        completed_by_date = db.query(
            func.date(OnboardingAssignment.completed_at).label('date'),
            func.count(OnboardingAssignment.id).label('count')
        ).filter(
            OnboardingAssignment.tenant_id == tenant_id,
            OnboardingAssignment.completed_at.isnot(None),
            func.date(OnboardingAssignment.completed_at) >= start_date,
            func.date(OnboardingAssignment.completed_at) <= end_date
        ).group_by(func.date(OnboardingAssignment.completed_at)).all()

        # Query new assignments by date
        new_by_date = db.query(
            func.date(OnboardingAssignment.assigned_at).label('date'),
            func.count(OnboardingAssignment.id).label('count')
        ).filter(
            OnboardingAssignment.tenant_id == tenant_id,
            func.date(OnboardingAssignment.assigned_at) >= start_date,
            func.date(OnboardingAssignment.assigned_at) <= end_date
        ).group_by(func.date(OnboardingAssignment.assigned_at)).all()

        # Create dictionaries
        completed_dict = {row.date: row.count for row in completed_by_date}
        new_dict = {row.date: row.count for row in new_by_date}

        # Generate date list
        trends = []
        current_date = start_date
        while current_date <= end_date:
            trends.append(schemas.CompletionTrendResponse(
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

    @staticmethod
    def get_all_flows_analytics(
        db: Session,
        tenant_id: int
    ) -> list[schemas.FlowAnalyticsResponse]:
        """Get analytics for all active flows."""
        flows = db.query(OnboardingFlow).filter(
            OnboardingFlow.tenant_id == tenant_id,
            OnboardingFlow.is_active == True,
            OnboardingFlow.deleted_at.is_(None)
        ).all()

        return [
            AnalyticsService.get_flow_analytics(db, flow.id, tenant_id)
            for flow in flows
        ]
