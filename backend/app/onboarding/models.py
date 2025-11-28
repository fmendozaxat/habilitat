"""
Onboarding models for flows, modules, assignments and progress tracking.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, JSON, DateTime
from sqlalchemy.orm import relationship
from app.core.models import BaseModel, BaseTenantModel, TimestampMixin, SoftDeleteMixin
from app.core.enums import OnboardingStatus


class OnboardingFlow(BaseTenantModel, SoftDeleteMixin):
    """
    Onboarding flow - a complete onboarding program.

    Attributes:
        title: Flow title
        description: Flow description
        is_active: Whether flow is active
        is_template: Whether this is a template flow
        display_order: Order for display
        settings: JSON settings for the flow
    """

    __tablename__ = "onboarding_flows"

    # Override tenant_id with explicit FK
    tenant_id = Column(
        Integer,
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Basic info
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_template = Column(Boolean, default=False, nullable=False)

    # Order
    display_order = Column(Integer, default=0, nullable=False)

    # Settings (JSON)
    settings = Column(JSON, default=dict, nullable=False)

    # Relationships
    tenant = relationship("Tenant", backref="onboarding_flows")
    modules = relationship(
        "OnboardingModule",
        back_populates="flow",
        cascade="all, delete-orphan",
        order_by="OnboardingModule.order"
    )
    assignments = relationship(
        "OnboardingAssignment",
        back_populates="flow",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<OnboardingFlow {self.title}>"

    @property
    def module_count(self) -> int:
        """Return number of modules in this flow."""
        return len(self.modules) if self.modules else 0

    @property
    def total_estimated_minutes(self) -> int:
        """Return total estimated time for all modules."""
        return sum(m.estimated_minutes or 0 for m in self.modules)


class OnboardingModule(BaseModel, TimestampMixin):
    """
    Module/step within an onboarding flow.

    Attributes:
        flow_id: Parent flow ID
        title: Module title
        description: Module description
        content_type: Type of content (text, video, pdf, quiz, task, link)
        content_text: Direct text content
        content_url: URL for video/pdf/link content
        order: Display order within flow
        is_required: Whether module must be completed
        quiz_data: Quiz questions and answers (JSON)
        estimated_minutes: Estimated time to complete
    """

    __tablename__ = "onboarding_modules"

    flow_id = Column(
        Integer,
        ForeignKey("onboarding_flows.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Basic info
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Content
    content_type = Column(String(50), nullable=False)  # text, video, pdf, quiz, task, link
    content_text = Column(Text, nullable=True)
    content_url = Column(String(500), nullable=True)

    # Order
    order = Column(Integer, nullable=False, default=0)

    # Requirements
    is_required = Column(Boolean, default=True, nullable=False)
    requires_completion_confirmation = Column(Boolean, default=False, nullable=False)

    # Quiz data (JSON)
    quiz_data = Column(JSON, nullable=True)

    # Estimated time
    estimated_minutes = Column(Integer, nullable=True)

    # Relationships
    flow = relationship("OnboardingFlow", back_populates="modules")
    progress_records = relationship(
        "ModuleProgress",
        back_populates="module",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<OnboardingModule {self.title}>"


class OnboardingAssignment(BaseTenantModel):
    """
    Assignment of a flow to a user.

    Attributes:
        flow_id: Flow being assigned
        user_id: User receiving the assignment
        status: Current status (not_started, in_progress, completed, expired)
        completion_percentage: Percentage of modules completed
        assigned_by: User who created the assignment
        due_date: Optional due date
    """

    __tablename__ = "onboarding_assignments"

    # Override tenant_id with explicit FK
    tenant_id = Column(
        Integer,
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    flow_id = Column(
        Integer,
        ForeignKey("onboarding_flows.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Status
    status = Column(String(50), default=OnboardingStatus.NOT_STARTED.value, nullable=False)

    # Dates
    assigned_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    due_date = Column(DateTime, nullable=True)

    # Progress
    completion_percentage = Column(Integer, default=0, nullable=False)

    # Assigned by
    assigned_by = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    # Relationships
    flow = relationship("OnboardingFlow", back_populates="assignments")
    user = relationship("User", foreign_keys=[user_id], backref="onboarding_assignments")
    assigner = relationship("User", foreign_keys=[assigned_by])
    module_progress = relationship(
        "ModuleProgress",
        back_populates="assignment",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<OnboardingAssignment user={self.user_id} flow={self.flow_id}>"

    @property
    def is_overdue(self) -> bool:
        """Check if assignment is past due date."""
        if not self.due_date:
            return False
        return datetime.now(timezone.utc) > self.due_date.replace(tzinfo=timezone.utc) and self.status != OnboardingStatus.COMPLETED.value

    @property
    def days_since_assignment(self) -> int:
        """Return days since assignment was created."""
        delta = datetime.now(timezone.utc) - self.assigned_at.replace(tzinfo=timezone.utc)
        return delta.days


class ModuleProgress(BaseModel, TimestampMixin):
    """
    Progress tracking for a user on a specific module.

    Attributes:
        assignment_id: Parent assignment
        module_id: Module being tracked
        is_completed: Whether module is completed
        completed_at: When module was completed
        time_spent_minutes: Time spent on module
        quiz_score: Score if module is a quiz
        quiz_passed: Whether quiz was passed
        notes: User notes
    """

    __tablename__ = "module_progress"

    assignment_id = Column(
        Integer,
        ForeignKey("onboarding_assignments.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    module_id = Column(
        Integer,
        ForeignKey("onboarding_modules.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Progress
    is_completed = Column(Boolean, default=False, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Time tracking
    time_spent_minutes = Column(Integer, default=0, nullable=False)

    # Quiz results
    quiz_score = Column(Integer, nullable=True)
    quiz_passed = Column(Boolean, nullable=True)

    # Notes
    notes = Column(Text, nullable=True)

    # Relationships
    assignment = relationship("OnboardingAssignment", back_populates="module_progress")
    module = relationship("OnboardingModule", back_populates="progress_records")

    def __repr__(self):
        return f"<ModuleProgress assignment={self.assignment_id} module={self.module_id}>"
