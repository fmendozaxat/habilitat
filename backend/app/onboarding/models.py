"""
Onboarding models.
Defines models for onboarding flows, modules, assignments, and progress tracking.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, JSON, DateTime
from sqlalchemy.orm import relationship
from app.core.models import BaseModel, TimestampMixin, SoftDeleteMixin
from app.core.enums import OnboardingStatus, ContentType


class OnboardingFlow(BaseModel, TimestampMixin, SoftDeleteMixin):
    """
    Onboarding flow model.
    Represents a complete onboarding flow/template with multiple modules/steps.
    """

    __tablename__ = "onboarding_flows"

    # Tenant relationship
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)

    # Basic info
    title = Column(String(200), nullable=False, comment="Flow title")
    description = Column(Text, nullable=True, comment="Flow description")

    # Status
    is_active = Column(Boolean, default=True, nullable=False, comment="Whether flow is active")
    is_template = Column(Boolean, default=False, nullable=False, comment="Whether this is a predefined template")

    # Order
    display_order = Column(Integer, default=0, nullable=False, comment="Display order for sorting")

    # Settings (JSON for flexibility)
    settings = Column(JSON, default={}, nullable=False, comment="Flow-specific settings")
    """
    Example settings structure:
    {
        "auto_assign_on_user_create": false,
        "send_welcome_email": true,
        "completion_certificate": false,
        "estimated_duration_days": 7,
        "allow_module_skip": false
    }
    """

    # Relationships
    tenant = relationship("Tenant")
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
        """Returns the number of modules in this flow."""
        return len(self.modules) if self.modules else 0


class OnboardingModule(BaseModel, TimestampMixin):
    """
    Onboarding module model.
    Represents a single step/module within an onboarding flow.
    """

    __tablename__ = "onboarding_modules"

    # Flow relationship
    flow_id = Column(Integer, ForeignKey("onboarding_flows.id", ondelete="CASCADE"), nullable=False, index=True)

    # Basic info
    title = Column(String(200), nullable=False, comment="Module title")
    description = Column(Text, nullable=True, comment="Module description")

    # Content
    content_type = Column(String(50), nullable=False, comment="Type of content: text, video, pdf, quiz, task, link")
    content_id = Column(Integer, ForeignKey("content_blocks.id", ondelete="SET NULL"), nullable=True, comment="Link to ContentBlock (optional)")

    # Direct content (for MVP simple)
    content_text = Column(Text, nullable=True, comment="Direct text content")
    content_url = Column(String(500), nullable=True, comment="Video URL, PDF URL, etc.")

    # Order
    order = Column(Integer, nullable=False, comment="Order within the flow")

    # Requirements
    is_required = Column(Boolean, default=True, nullable=False, comment="Whether module is required")
    requires_completion_confirmation = Column(Boolean, default=False, nullable=False, comment="Whether explicit confirmation is needed")

    # Quiz data (if content_type = quiz)
    quiz_data = Column(JSON, nullable=True, comment="Quiz questions and answers")
    """
    Example quiz_data structure:
    {
        "questions": [
            {
                "question": "¿Cuál es nuestra misión?",
                "type": "multiple_choice",
                "options": ["Opción A", "Opción B", "Opción C"],
                "correct_answer": 0
            }
        ],
        "passing_score": 80
    }
    """

    # Estimated time
    estimated_minutes = Column(Integer, nullable=True, comment="Estimated time to complete in minutes")

    # Relationships
    flow = relationship("OnboardingFlow", back_populates="modules")
    progress_records = relationship(
        "ModuleProgress",
        back_populates="module",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<OnboardingModule {self.title}>"


class OnboardingAssignment(BaseModel, TimestampMixin):
    """
    Onboarding assignment model.
    Represents the assignment of an onboarding flow to a specific user.
    """

    __tablename__ = "onboarding_assignments"

    # Tenant relationship
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)

    # Flow and User relationships
    flow_id = Column(Integer, ForeignKey("onboarding_flows.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Status
    status = Column(
        String(50),
        default=OnboardingStatus.NOT_STARTED.value,
        nullable=False,
        comment="Status: not_started, in_progress, completed, expired"
    )

    # Dates
    assigned_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="When assigned")
    started_at = Column(DateTime, nullable=True, comment="When started")
    completed_at = Column(DateTime, nullable=True, comment="When completed")
    due_date = Column(DateTime, nullable=True, comment="Due date")

    # Progress
    completion_percentage = Column(Integer, default=0, nullable=False, comment="Completion percentage 0-100")

    # Assigned by
    assigned_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, comment="User who assigned")

    # Relationships
    tenant = relationship("Tenant")
    flow = relationship("OnboardingFlow", back_populates="assignments")
    user = relationship("User", foreign_keys=[user_id], back_populates="onboarding_assignments")
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
        """Check if assignment is overdue."""
        if not self.due_date:
            return False
        return datetime.utcnow() > self.due_date and self.status != OnboardingStatus.COMPLETED.value

    @property
    def days_since_assignment(self) -> int:
        """Calculate days since assignment."""
        return (datetime.utcnow() - self.assigned_at).days


class ModuleProgress(BaseModel, TimestampMixin):
    """
    Module progress model.
    Tracks a user's progress on a specific module within an assignment.
    """

    __tablename__ = "module_progress"

    # Assignment and Module relationships
    assignment_id = Column(Integer, ForeignKey("onboarding_assignments.id", ondelete="CASCADE"), nullable=False, index=True)
    module_id = Column(Integer, ForeignKey("onboarding_modules.id", ondelete="CASCADE"), nullable=False, index=True)

    # Progress
    is_completed = Column(Boolean, default=False, nullable=False, comment="Whether module is completed")
    completed_at = Column(DateTime, nullable=True, comment="When completed")

    # Time tracking
    time_spent_minutes = Column(Integer, default=0, nullable=False, comment="Time spent in minutes")

    # Quiz results (if applicable)
    quiz_score = Column(Integer, nullable=True, comment="Quiz score 0-100")
    quiz_passed = Column(Boolean, nullable=True, comment="Whether quiz was passed")
    quiz_answers = Column(JSON, nullable=True, comment="User's quiz answers")

    # Notes from employee
    notes = Column(Text, nullable=True, comment="Employee notes")

    # Relationships
    assignment = relationship("OnboardingAssignment", back_populates="module_progress")
    module = relationship("OnboardingModule", back_populates="progress_records")

    def __repr__(self):
        return f"<ModuleProgress assignment={self.assignment_id} module={self.module_id}>"
