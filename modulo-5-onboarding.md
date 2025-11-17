# Módulo 5: Onboarding (Flujos y Progreso)

## Descripción

El módulo Onboarding es el corazón de la plataforma. Maneja los flujos de onboarding, módulos/pasos, asignaciones a empleados, tracking de progreso y completación de tareas.

**Límite de líneas:** ~4000-5000 líneas

## Responsabilidades

1. CRUD de flujos de onboarding (OnboardingFlow)
2. Gestión de módulos/pasos dentro de flujos (OnboardingModule)
3. Asignación de flujos a empleados (OnboardingAssignment)
4. Tracking de progreso por módulo (ModuleProgress)
5. Completación de módulos y tareas
6. Cálculo de porcentaje de completación
7. Templates de flujos predefinidos
8. Clonado de flujos

## Estructura de Archivos

```
app/onboarding/
├── __init__.py
├── models.py              # OnboardingFlow, OnboardingModule, OnboardingAssignment, ModuleProgress
├── schemas.py             # Request/Response schemas
├── service.py             # Lógica de negocio
├── router.py              # Endpoints
├── templates.py           # Templates predefinidos de onboarding
├── exceptions.py          # Excepciones
└── utils.py               # Utilidades
```

## 1. Modelos (models.py)

### OnboardingFlow Model

```python
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.core.models import BaseModel, TimestampMixin, TenantMixin, SoftDeleteMixin

class OnboardingFlow(BaseModel, TimestampMixin, TenantMixin, SoftDeleteMixin):
    """
    Flujo de onboarding completo
    """
    __tablename__ = "onboarding_flows"

    # Basic info
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_template = Column(Boolean, default=False, nullable=False)  # Si es un template predefinido

    # Order
    display_order = Column(Integer, default=0, nullable=False)

    # Settings
    settings = Column(JSON, default={}, nullable=False)
    """
    Ejemplo de settings:
    {
        "auto_assign_on_user_create": false,
        "send_welcome_email": true,
        "completion_certificate": false,
        "estimated_duration_days": 7
    }
    """

    # Relationships
    modules = relationship("OnboardingModule", back_populates="flow", cascade="all, delete-orphan", order_by="OnboardingModule.order")
    assignments = relationship("OnboardingAssignment", back_populates="flow", cascade="all, delete-orphan")

    @property
    def module_count(self) -> int:
        return len(self.modules)

    def __repr__(self):
        return f"<OnboardingFlow {self.title}>"
```

### OnboardingModule Model

```python
from app.core.enums import ContentType

class OnboardingModule(BaseModel, TimestampMixin):
    """
    Módulo/paso dentro de un flujo de onboarding
    """
    __tablename__ = "onboarding_modules"

    flow_id = Column(Integer, ForeignKey("onboarding_flows.id", ondelete="CASCADE"), nullable=False)

    # Basic info
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Content
    content_type = Column(String(50), nullable=False)  # text, video, pdf, quiz, task
    content_id = Column(Integer, ForeignKey("content_blocks.id", ondelete="SET NULL"), nullable=True)  # Link a ContentBlock

    # Direct content (para MVP simple)
    content_text = Column(Text, nullable=True)
    content_url = Column(String(500), nullable=True)  # Video URL, PDF URL, etc.

    # Order
    order = Column(Integer, nullable=False)

    # Requirements
    is_required = Column(Boolean, default=True, nullable=False)
    requires_completion_confirmation = Column(Boolean, default=False, nullable=False)

    # Quiz (si content_type = quiz)
    quiz_data = Column(JSON, nullable=True)
    """
    Ejemplo de quiz_data:
    {
        "questions": [
            {
                "question": "¿Cuál es nuestra misión?",
                "type": "multiple_choice",
                "options": ["A", "B", "C"],
                "correct_answer": "A"
            }
        ],
        "passing_score": 80
    }
    """

    # Estimated time
    estimated_minutes = Column(Integer, nullable=True)

    # Relationships
    flow = relationship("OnboardingFlow", back_populates="modules")
    progress_records = relationship("ModuleProgress", back_populates="module", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<OnboardingModule {self.title}>"
```

### OnboardingAssignment Model

```python
from app.core.enums import OnboardingStatus
from datetime import datetime

class OnboardingAssignment(BaseModel, TimestampMixin, TenantMixin):
    """
    Asignación de un flujo de onboarding a un empleado
    """
    __tablename__ = "onboarding_assignments"

    flow_id = Column(Integer, ForeignKey("onboarding_flows.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Status
    status = Column(String(50), default=OnboardingStatus.NOT_STARTED, nullable=False)

    # Dates
    assigned_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    due_date = Column(DateTime, nullable=True)

    # Progress
    completion_percentage = Column(Integer, default=0, nullable=False)  # 0-100

    # Assigned by
    assigned_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    flow = relationship("OnboardingFlow", back_populates="assignments")
    user = relationship("User", foreign_keys=[user_id], back_populates="onboarding_assignments")
    assigner = relationship("User", foreign_keys=[assigned_by])
    module_progress = relationship("ModuleProgress", back_populates="assignment", cascade="all, delete-orphan")

    @property
    def is_overdue(self) -> bool:
        if not self.due_date:
            return False
        return datetime.utcnow() > self.due_date and self.status != OnboardingStatus.COMPLETED

    @property
    def days_since_assignment(self) -> int:
        return (datetime.utcnow() - self.assigned_at).days

    def __repr__(self):
        return f"<OnboardingAssignment user={self.user_id} flow={self.flow_id}>"
```

### ModuleProgress Model

```python
class ModuleProgress(BaseModel, TimestampMixin):
    """
    Progreso de un usuario en un módulo específico
    """
    __tablename__ = "module_progress"

    assignment_id = Column(Integer, ForeignKey("onboarding_assignments.id", ondelete="CASCADE"), nullable=False)
    module_id = Column(Integer, ForeignKey("onboarding_modules.id", ondelete="CASCADE"), nullable=False)

    # Progress
    is_completed = Column(Boolean, default=False, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Time spent (en minutos)
    time_spent_minutes = Column(Integer, default=0, nullable=False)

    # Quiz results (si aplica)
    quiz_score = Column(Integer, nullable=True)  # 0-100
    quiz_passed = Column(Boolean, nullable=True)

    # Notes del empleado
    notes = Column(Text, nullable=True)

    # Relationships
    assignment = relationship("OnboardingAssignment", back_populates="module_progress")
    module = relationship("OnboardingModule", back_populates="progress_records")

    def __repr__(self):
        return f"<ModuleProgress assignment={self.assignment_id} module={self.module_id}>"
```

## 2. Schemas (schemas.py)

### Request Schemas

```python
from pydantic import BaseModel, Field
from datetime import datetime
from app.core.schemas import BaseSchema, PaginationParams

# OnboardingFlow
class OnboardingFlowCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    is_active: bool = True
    settings: dict = {}

class OnboardingFlowUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    is_active: bool | None = None
    display_order: int | None = None
    settings: dict | None = None

# OnboardingModule
class OnboardingModuleCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    content_type: str = Field(..., regex=r'^(text|video|pdf|quiz|task|link)$')
    content_text: str | None = None
    content_url: str | None = None
    content_id: int | None = None
    order: int = 0
    is_required: bool = True
    requires_completion_confirmation: bool = False
    quiz_data: dict | None = None
    estimated_minutes: int | None = None

class OnboardingModuleUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    content_type: str | None = None
    content_text: str | None = None
    content_url: str | None = None
    content_id: int | None = None
    order: int | None = None
    is_required: bool | None = None
    requires_completion_confirmation: bool | None = None
    quiz_data: dict | None = None
    estimated_minutes: int | None = None

# Assignment
class OnboardingAssignmentCreate(BaseModel):
    flow_id: int
    user_id: int
    due_date: datetime | None = None

class BulkAssignmentCreate(BaseModel):
    flow_id: int
    user_ids: list[int]
    due_date: datetime | None = None

# Module Progress
class CompleteModuleRequest(BaseModel):
    notes: str | None = None
    time_spent_minutes: int | None = None

class SubmitQuizRequest(BaseModel):
    answers: dict  # {"question_index": "answer"}
    time_spent_minutes: int | None = None
```

### Response Schemas

```python
class OnboardingModuleResponse(BaseSchema):
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
    created_at: datetime

class OnboardingFlowResponse(BaseSchema):
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
    created_at: datetime
    updated_at: datetime

class OnboardingFlowListResponse(BaseSchema):
    """Respuesta simplificada para listados"""
    id: int
    title: str
    description: str | None
    is_active: bool
    module_count: int
    created_at: datetime

class ModuleProgressResponse(BaseSchema):
    id: int
    module_id: int
    module_title: str
    is_completed: bool
    completed_at: datetime | None
    time_spent_minutes: int
    quiz_score: int | None
    quiz_passed: bool | None

class OnboardingAssignmentResponse(BaseSchema):
    id: int
    flow_id: int
    flow_title: str
    user_id: int
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
    """Respuesta simplificada"""
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
    """Dashboard para empleados"""
    total_assignments: int
    completed: int
    in_progress: int
    not_started: int
    overdue: int
    assignments: list[OnboardingAssignmentResponse]
```

## 3. Service (service.py)

### OnboardingService Class

```python
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.core.exceptions import NotFoundException, ValidationException, ForbiddenException
from app.onboarding.models import OnboardingFlow, OnboardingModule, OnboardingAssignment, ModuleProgress
from app.onboarding import schemas
from app.core.enums import OnboardingStatus
from datetime import datetime

class OnboardingService:
    """Servicio de gestión de onboarding"""

    # OnboardingFlow CRUD

    @staticmethod
    def create_flow(db: Session, tenant_id: int, data: schemas.OnboardingFlowCreate) -> OnboardingFlow:
        """Crear flujo de onboarding"""
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
        """Obtener flujo por ID"""
        flow = db.query(OnboardingFlow).filter(
            OnboardingFlow.id == flow_id,
            OnboardingFlow.tenant_id == tenant_id
        ).first()

        if not flow:
            raise NotFoundException("Flujo de onboarding")

        return flow

    @staticmethod
    def list_flows(db: Session, tenant_id: int, include_inactive: bool = False) -> list[OnboardingFlow]:
        """Listar flujos del tenant"""
        query = db.query(OnboardingFlow).filter(
            OnboardingFlow.tenant_id == tenant_id
        )

        if not include_inactive:
            query = query.filter(OnboardingFlow.is_active == True)

        return query.order_by(OnboardingFlow.display_order, OnboardingFlow.created_at.desc()).all()

    @staticmethod
    def update_flow(
        db: Session,
        flow_id: int,
        tenant_id: int,
        data: schemas.OnboardingFlowUpdate
    ) -> OnboardingFlow:
        """Actualizar flujo"""
        flow = OnboardingService.get_flow(db, flow_id, tenant_id)

        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(flow, field, value)

        db.commit()
        db.refresh(flow)

        return flow

    @staticmethod
    def delete_flow(db: Session, flow_id: int, tenant_id: int) -> bool:
        """Soft delete de flujo"""
        flow = OnboardingService.get_flow(db, flow_id, tenant_id)
        flow.deleted_at = datetime.utcnow()
        flow.is_active = False
        db.commit()
        return True

    @staticmethod
    def clone_flow(db: Session, flow_id: int, tenant_id: int, new_title: str) -> OnboardingFlow:
        """
        Clonar flujo completo con todos sus módulos

        Útil para crear variaciones de flujos existentes
        """
        original = OnboardingService.get_flow(db, flow_id, tenant_id)

        # Clonar flow
        new_flow = OnboardingFlow(
            tenant_id=tenant_id,
            title=new_title,
            description=original.description,
            settings=original.settings.copy() if original.settings else {}
        )

        db.add(new_flow)
        db.flush()

        # Clonar módulos
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

    # OnboardingModule CRUD

    @staticmethod
    def create_module(
        db: Session,
        flow_id: int,
        tenant_id: int,
        data: schemas.OnboardingModuleCreate
    ) -> OnboardingModule:
        """Crear módulo en un flujo"""
        # Verificar que el flow existe y pertenece al tenant
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
        """Obtener módulo por ID"""
        module = db.query(OnboardingModule).filter(OnboardingModule.id == module_id).first()

        if not module:
            raise NotFoundException("Módulo")

        return module

    @staticmethod
    def update_module(
        db: Session,
        module_id: int,
        data: schemas.OnboardingModuleUpdate
    ) -> OnboardingModule:
        """Actualizar módulo"""
        module = OnboardingService.get_module(db, module_id)

        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(module, field, value)

        db.commit()
        db.refresh(module)

        return module

    @staticmethod
    def delete_module(db: Session, module_id: int) -> bool:
        """Eliminar módulo"""
        module = OnboardingService.get_module(db, module_id)
        db.delete(module)
        db.commit()
        return True

    @staticmethod
    def reorder_modules(db: Session, flow_id: int, module_orders: dict[int, int]) -> bool:
        """
        Reordenar módulos de un flujo

        Args:
            module_orders: {module_id: new_order}
        """
        for module_id, new_order in module_orders.items():
            module = OnboardingService.get_module(db, module_id)
            if module.flow_id != flow_id:
                raise ValidationException("Módulo no pertenece a este flujo")
            module.order = new_order

        db.commit()
        return True

    # Assignments

    @staticmethod
    def assign_flow(
        db: Session,
        tenant_id: int,
        data: schemas.OnboardingAssignmentCreate,
        assigned_by_id: int
    ) -> OnboardingAssignment:
        """
        Asignar flujo a un empleado

        Crea el assignment y los ModuleProgress para cada módulo
        """
        # Verificar que el flow existe
        flow = OnboardingService.get_flow(db, data.flow_id, tenant_id)

        # Verificar que el usuario no tenga ya este flow asignado
        existing = db.query(OnboardingAssignment).filter(
            and_(
                OnboardingAssignment.flow_id == data.flow_id,
                OnboardingAssignment.user_id == data.user_id,
                OnboardingAssignment.status != OnboardingStatus.COMPLETED
            )
        ).first()

        if existing:
            raise ValidationException("Usuario ya tiene este flujo asignado")

        # Crear assignment
        assignment = OnboardingAssignment(
            **data.model_dump(),
            tenant_id=tenant_id,
            assigned_by=assigned_by_id
        )

        db.add(assignment)
        db.flush()

        # Crear ModuleProgress para cada módulo
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
    def get_assignment(db: Session, assignment_id: int, tenant_id: int) -> OnboardingAssignment:
        """Obtener assignment por ID"""
        assignment = db.query(OnboardingAssignment).filter(
            OnboardingAssignment.id == assignment_id,
            OnboardingAssignment.tenant_id == tenant_id
        ).first()

        if not assignment:
            raise NotFoundException("Asignación")

        return assignment

    @staticmethod
    def get_user_assignments(db: Session, user_id: int, tenant_id: int) -> list[OnboardingAssignment]:
        """Obtener todos los assignments de un usuario"""
        return db.query(OnboardingAssignment).filter(
            OnboardingAssignment.user_id == user_id,
            OnboardingAssignment.tenant_id == tenant_id
        ).order_by(OnboardingAssignment.assigned_at.desc()).all()

    @staticmethod
    def complete_module(
        db: Session,
        assignment_id: int,
        module_id: int,
        user_id: int,
        data: schemas.CompleteModuleRequest
    ) -> ModuleProgress:
        """
        Marcar módulo como completado

        Actualiza el progreso general del assignment
        """
        # Obtener progress
        progress = db.query(ModuleProgress).filter(
            ModuleProgress.assignment_id == assignment_id,
            ModuleProgress.module_id == module_id
        ).first()

        if not progress:
            raise NotFoundException("Progreso de módulo")

        # Verificar que el assignment pertenece al usuario
        if progress.assignment.user_id != user_id:
            raise ForbiddenException("No puedes completar este módulo")

        # Marcar como completado
        progress.is_completed = True
        progress.completed_at = datetime.utcnow()

        if data.notes:
            progress.notes = data.notes

        if data.time_spent_minutes:
            progress.time_spent_minutes = data.time_spent_minutes

        # Actualizar started_at del assignment si es el primer módulo
        assignment = progress.assignment
        if not assignment.started_at:
            assignment.started_at = datetime.utcnow()
            assignment.status = OnboardingStatus.IN_PROGRESS

        # Recalcular completion percentage
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
        """
        Enviar respuestas de quiz

        Califica automáticamente y marca como completado si pasa
        """
        # Obtener progress y module
        progress = db.query(ModuleProgress).filter(
            ModuleProgress.assignment_id == assignment_id,
            ModuleProgress.module_id == module_id
        ).first()

        if not progress:
            raise NotFoundException("Progreso de módulo")

        module = progress.module

        if module.content_type != "quiz":
            raise ValidationException("Este módulo no es un quiz")

        # Verificar permisos
        if progress.assignment.user_id != user_id:
            raise ForbiddenException("No puedes enviar este quiz")

        # Calificar quiz
        quiz_data = module.quiz_data
        questions = quiz_data.get("questions", [])
        passing_score = quiz_data.get("passing_score", 70)

        correct_count = 0
        for i, question in enumerate(questions):
            user_answer = data.answers.get(str(i))
            if user_answer == question.get("correct_answer"):
                correct_count += 1

        score = int((correct_count / len(questions)) * 100) if questions else 0
        passed = score >= passing_score

        # Actualizar progress
        progress.quiz_score = score
        progress.quiz_passed = passed

        if passed:
            progress.is_completed = True
            progress.completed_at = datetime.utcnow()

        if data.time_spent_minutes:
            progress.time_spent_minutes = data.time_spent_minutes

        # Actualizar assignment progress
        assignment = progress.assignment
        if not assignment.started_at:
            assignment.started_at = datetime.utcnow()
            assignment.status = OnboardingStatus.IN_PROGRESS

        OnboardingService._update_assignment_progress(db, assignment)

        db.commit()
        db.refresh(progress)

        return progress

    @staticmethod
    def _update_assignment_progress(db: Session, assignment: OnboardingAssignment):
        """
        Recalcular y actualizar el porcentaje de completación del assignment

        Marca como COMPLETED si todos los módulos requeridos están completados
        """
        total_modules = len(assignment.flow.modules)
        if total_modules == 0:
            assignment.completion_percentage = 100
            assignment.status = OnboardingStatus.COMPLETED
            assignment.completed_at = datetime.utcnow()
            return

        completed_count = sum(1 for p in assignment.module_progress if p.is_completed)

        assignment.completion_percentage = int((completed_count / total_modules) * 100)

        # Verificar si todos los módulos REQUERIDOS están completados
        required_modules = [m for m in assignment.flow.modules if m.is_required]
        required_completed = all(
            any(p.module_id == m.id and p.is_completed for p in assignment.module_progress)
            for m in required_modules
        )

        if required_completed:
            assignment.status = OnboardingStatus.COMPLETED
            assignment.completed_at = datetime.utcnow()
        elif assignment.completion_percentage > 0:
            assignment.status = OnboardingStatus.IN_PROGRESS
```

## 4. Router (router.py)

```python
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.schemas import SuccessResponse
from app.core.enums import UserRole
from app.onboarding import schemas, service
from app.auth.dependencies import get_current_user, require_role
from app.tenants.models import Tenant
from app.tenants.dependencies import get_current_tenant
from app.users.models import User

router = APIRouter(prefix="/onboarding", tags=["Onboarding"])

# Flows

@router.post("/flows", response_model=schemas.OnboardingFlowResponse, status_code=status.HTTP_201_CREATED)
async def create_flow(
    data: schemas.OnboardingFlowCreate,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(require_role(UserRole.TENANT_ADMIN)),
    db: Session = Depends(get_db)
):
    """Crear flujo de onboarding"""
    flow = service.OnboardingService.create_flow(db, tenant.id, data)
    return flow

@router.get("/flows", response_model=list[schemas.OnboardingFlowListResponse])
async def list_flows(
    include_inactive: bool = False,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Listar flujos"""
    flows = service.OnboardingService.list_flows(db, tenant.id, include_inactive)
    return flows

@router.get("/flows/{flow_id}", response_model=schemas.OnboardingFlowResponse)
async def get_flow(
    flow_id: int,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener flujo por ID"""
    flow = service.OnboardingService.get_flow(db, flow_id, tenant.id)
    return flow

@router.patch("/flows/{flow_id}", response_model=schemas.OnboardingFlowResponse)
async def update_flow(
    flow_id: int,
    data: schemas.OnboardingFlowUpdate,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(require_role(UserRole.TENANT_ADMIN)),
    db: Session = Depends(get_db)
):
    """Actualizar flujo"""
    flow = service.OnboardingService.update_flow(db, flow_id, tenant.id, data)
    return flow

@router.delete("/flows/{flow_id}", response_model=SuccessResponse)
async def delete_flow(
    flow_id: int,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(require_role(UserRole.TENANT_ADMIN)),
    db: Session = Depends(get_db)
):
    """Eliminar flujo"""
    service.OnboardingService.delete_flow(db, flow_id, tenant.id)
    return SuccessResponse(message="Flujo eliminado exitosamente")

@router.post("/flows/{flow_id}/clone", response_model=schemas.OnboardingFlowResponse)
async def clone_flow(
    flow_id: int,
    new_title: str,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(require_role(UserRole.TENANT_ADMIN)),
    db: Session = Depends(get_db)
):
    """Clonar flujo completo"""
    flow = service.OnboardingService.clone_flow(db, flow_id, tenant.id, new_title)
    return flow

# Modules

@router.post("/flows/{flow_id}/modules", response_model=schemas.OnboardingModuleResponse, status_code=status.HTTP_201_CREATED)
async def create_module(
    flow_id: int,
    data: schemas.OnboardingModuleCreate,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(require_role(UserRole.TENANT_ADMIN)),
    db: Session = Depends(get_db)
):
    """Crear módulo en flujo"""
    module = service.OnboardingService.create_module(db, flow_id, tenant.id, data)
    return module

@router.patch("/modules/{module_id}", response_model=schemas.OnboardingModuleResponse)
async def update_module(
    module_id: int,
    data: schemas.OnboardingModuleUpdate,
    current_user: User = Depends(require_role(UserRole.TENANT_ADMIN)),
    db: Session = Depends(get_db)
):
    """Actualizar módulo"""
    module = service.OnboardingService.update_module(db, module_id, data)
    return module

@router.delete("/modules/{module_id}", response_model=SuccessResponse)
async def delete_module(
    module_id: int,
    current_user: User = Depends(require_role(UserRole.TENANT_ADMIN)),
    db: Session = Depends(get_db)
):
    """Eliminar módulo"""
    service.OnboardingService.delete_module(db, module_id)
    return SuccessResponse(message="Módulo eliminado exitosamente")

# Assignments

@router.post("/assignments", response_model=schemas.OnboardingAssignmentResponse, status_code=status.HTTP_201_CREATED)
async def assign_flow(
    data: schemas.OnboardingAssignmentCreate,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(require_role(UserRole.TENANT_ADMIN)),
    db: Session = Depends(get_db)
):
    """Asignar flujo a empleado"""
    assignment = service.OnboardingService.assign_flow(db, tenant.id, data, current_user.id)
    return assignment

@router.get("/my-assignments", response_model=list[schemas.OnboardingAssignmentResponse])
async def get_my_assignments(
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener mis assignments (empleado)"""
    assignments = service.OnboardingService.get_user_assignments(db, current_user.id, tenant.id)
    return assignments

@router.get("/assignments/{assignment_id}", response_model=schemas.OnboardingAssignmentResponse)
async def get_assignment(
    assignment_id: int,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener assignment"""
    assignment = service.OnboardingService.get_assignment(db, assignment_id, tenant.id)

    # Empleados solo pueden ver sus propios assignments
    if current_user.role == UserRole.EMPLOYEE and assignment.user_id != current_user.id:
        raise ForbiddenException()

    return assignment

# Module Progress

@router.post("/assignments/{assignment_id}/modules/{module_id}/complete", response_model=schemas.ModuleProgressResponse)
async def complete_module(
    assignment_id: int,
    module_id: int,
    data: schemas.CompleteModuleRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Marcar módulo como completado"""
    progress = service.OnboardingService.complete_module(
        db, assignment_id, module_id, current_user.id, data
    )
    return progress

@router.post("/assignments/{assignment_id}/modules/{module_id}/submit-quiz", response_model=schemas.ModuleProgressResponse)
async def submit_quiz(
    assignment_id: int,
    module_id: int,
    data: schemas.SubmitQuizRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Enviar respuestas de quiz"""
    progress = service.OnboardingService.submit_quiz(
        db, assignment_id, module_id, current_user.id, data
    )
    return progress
```

## Dependencias entre Módulos

**Depende de:**
- Core
- Tenants (tenant_id)
- Users (user_id, assignments)
- Content (content_id opcional)

**Es usado por:**
- Analytics (reportes de progreso)

## Testing

Tests críticos para flujos, asignaciones, progreso y quizzes.

## Checklist

- [ ] Modelos Flow, Module, Assignment, Progress
- [ ] CRUD completo
- [ ] Sistema de progreso
- [ ] Quizzes con calificación automática
- [ ] Clonado de flujos
- [ ] Tests 80%+

## Notas

1. Implementar después de Core, Tenants, Users, Content
2. Progress tracking es crítico
3. Optimizar queries con eager loading

## Dependencias

Ninguna adicional.
