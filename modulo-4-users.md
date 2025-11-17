# Módulo 4: Users (Gestión de Usuarios)

## Descripción

El módulo Users maneja todo lo relacionado con usuarios de la plataforma: creación, actualización, gestión de perfiles, roles, invitaciones y asignación a tenants.

**Límite de líneas:** ~3000-4000 líneas

## Responsabilidades

1. CRUD de usuarios
2. Gestión de perfil de usuario
3. Roles y permisos dentro del tenant
4. Invitaciones de usuarios a tenant
5. Cambio de contraseña
6. Upload de avatar
7. Listado y filtrado de usuarios por tenant

## Estructura de Archivos

```
app/users/
├── __init__.py
├── models.py              # User, UserInvitation
├── schemas.py             # Request/Response schemas
├── service.py             # Lógica de negocio
├── router.py              # Endpoints CRUD
├── exceptions.py          # Excepciones de usuarios
└── utils.py               # Utilidades
```

## 1. Modelos (models.py)

### User Model

```python
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.core.models import BaseModel, TimestampMixin, TenantMixin, SoftDeleteMixin
from app.core.enums import UserRole

class User(BaseModel, TimestampMixin, TenantMixin, SoftDeleteMixin):
    """
    Modelo de usuario
    """
    __tablename__ = "users"

    # Basic info
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)

    # Profile
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    avatar_url = Column(String(500), nullable=True)
    phone = Column(String(50), nullable=True)
    job_title = Column(String(100), nullable=True)
    department = Column(String(100), nullable=True)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_email_verified = Column(Boolean, default=False, nullable=False)

    # Role
    role = Column(SQLEnum(UserRole), default=UserRole.EMPLOYEE, nullable=False)

    # Relationships
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True)
    tenant = relationship("Tenant", back_populates="users")

    # Auth relationships
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    password_reset_tokens = relationship("PasswordResetToken", back_populates="user", cascade="all, delete-orphan")
    email_verification_tokens = relationship("EmailVerificationToken", back_populates="user", cascade="all, delete-orphan")

    # Onboarding relationships
    onboarding_assignments = relationship("OnboardingAssignment", back_populates="user", cascade="all, delete-orphan")

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def is_admin(self) -> bool:
        return self.role in [UserRole.SUPER_ADMIN, UserRole.TENANT_ADMIN]

    @property
    def is_super_admin(self) -> bool:
        return self.role == UserRole.SUPER_ADMIN

    @property
    def is_tenant_admin(self) -> bool:
        return self.role == UserRole.TENANT_ADMIN

    def __repr__(self):
        return f"<User {self.email}>"
```

### UserInvitation Model

```python
from datetime import datetime, timedelta

class UserInvitation(BaseModel, TimestampMixin, TenantMixin):
    """
    Invitaciones de usuarios a un tenant
    """
    __tablename__ = "user_invitations"

    email = Column(String(255), nullable=False, index=True)
    token = Column(String(100), unique=True, nullable=False, index=True)
    role = Column(SQLEnum(UserRole), default=UserRole.EMPLOYEE, nullable=False)

    # Quien invitó
    invited_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Status
    is_accepted = Column(Boolean, default=False, nullable=False)
    accepted_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=False)

    # Relationships
    inviter = relationship("User", foreign_keys=[invited_by])

    @property
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at

    @property
    def is_valid(self) -> bool:
        return not self.is_accepted and not self.is_expired

    def __repr__(self):
        return f"<UserInvitation {self.email}>"
```

## 2. Schemas (schemas.py)

### Request Schemas

```python
from pydantic import BaseModel, EmailStr, Field, validator
from app.core.schemas import BaseSchema, PaginationParams
from app.core.enums import UserRole

# User Create/Update
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    role: UserRole = UserRole.EMPLOYEE
    tenant_id: int | None = None

    @validator('password')
    def validate_password(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('Debe contener al menos una mayúscula')
        if not any(c.islower() for c in v):
            raise ValueError('Debe contener al menos una minúscula')
        if not any(c.isdigit() for c in v):
            raise ValueError('Debe contener al menos un número')
        return v

class UserUpdate(BaseModel):
    first_name: str | None = Field(None, min_length=1, max_length=100)
    last_name: str | None = Field(None, min_length=1, max_length=100)
    phone: str | None = None
    job_title: str | None = None
    department: str | None = None
    avatar_url: str | None = None

class UserUpdateByAdmin(UserUpdate):
    """Update schema para admins (más campos)"""
    email: EmailStr | None = None
    role: UserRole | None = None
    is_active: bool | None = None

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)

    @validator('new_password')
    def validate_password(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('Debe contener al menos una mayúscula')
        if not any(c.islower() for c in v):
            raise ValueError('Debe contener al menos una minúscula')
        if not any(c.isdigit() for c in v):
            raise ValueError('Debe contener al menos un número')
        return v

# Invitations
class InviteUserRequest(BaseModel):
    email: EmailStr
    role: UserRole = UserRole.EMPLOYEE
    first_name: str | None = None
    last_name: str | None = None

class AcceptInvitationRequest(BaseModel):
    token: str
    password: str = Field(..., min_length=8)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)

# Filters
class UserFilterParams(PaginationParams):
    search: str | None = None  # Buscar por nombre o email
    role: UserRole | None = None
    is_active: bool | None = None
    department: str | None = None
```

### Response Schemas

```python
from datetime import datetime
from app.core.schemas import PaginatedResponse

class UserResponse(BaseSchema):
    id: int
    email: str
    first_name: str
    last_name: str
    full_name: str
    avatar_url: str | None
    phone: str | None
    job_title: str | None
    department: str | None
    role: str
    is_active: bool
    is_email_verified: bool
    tenant_id: int | None
    created_at: datetime
    updated_at: datetime

class UserListResponse(BaseSchema):
    """Respuesta simplificada para listas"""
    id: int
    email: str
    first_name: str
    last_name: str
    full_name: str
    avatar_url: str | None
    job_title: str | None
    department: str | None
    role: str
    is_active: bool

class UserInvitationResponse(BaseSchema):
    id: int
    email: str
    role: str
    is_accepted: bool
    expires_at: datetime
    created_at: datetime
    invited_by: int | None

class AvatarUploadResponse(BaseSchema):
    url: str
```

## 3. Service (service.py)

### UserService Class

```python
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from app.core.security import hash_password, verify_password
from app.core.exceptions import NotFoundException, AlreadyExistsException, ValidationException, ForbiddenException
from app.core.utils import generate_random_string
from app.users.models import User, UserInvitation
from app.users import schemas
from app.tenants.service import TenantService
from datetime import datetime, timedelta

class UserService:
    """Servicio de gestión de usuarios"""

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> User:
        """Obtener usuario por ID"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundException("Usuario")
        return user

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> User | None:
        """Obtener usuario por email"""
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def create_user(db: Session, data: schemas.UserCreate) -> User:
        """
        Crear nuevo usuario

        Raises:
            AlreadyExistsException si el email ya existe
            ValidationException si se excede límite de usuarios del tenant
        """
        # Validar email único
        existing = UserService.get_user_by_email(db, data.email)
        if existing:
            raise AlreadyExistsException(f"Usuario con email '{data.email}'")

        # Si tiene tenant_id, validar límites
        if data.tenant_id:
            if not TenantService.check_user_limit(db, data.tenant_id):
                raise ValidationException("Límite de usuarios alcanzado para este tenant")

        # Hash password
        hashed_password = hash_password(data.password)

        # Crear usuario
        user_data = data.model_dump(exclude={'password'})
        user = User(
            **user_data,
            hashed_password=hashed_password
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        return user

    @staticmethod
    def update_user(
        db: Session,
        user_id: int,
        data: schemas.UserUpdate | schemas.UserUpdateByAdmin
    ) -> User:
        """Actualizar usuario"""
        user = UserService.get_user_by_id(db, user_id)

        # Si se actualiza email, validar que no exista
        if isinstance(data, schemas.UserUpdateByAdmin) and data.email:
            existing = UserService.get_user_by_email(db, data.email)
            if existing and existing.id != user_id:
                raise AlreadyExistsException(f"Usuario con email '{data.email}'")

        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(user, field, value)

        db.commit()
        db.refresh(user)

        return user

    @staticmethod
    def delete_user(db: Session, user_id: int) -> bool:
        """Soft delete de usuario"""
        user = UserService.get_user_by_id(db, user_id)
        user.deleted_at = datetime.utcnow()
        user.is_active = False
        db.commit()
        return True

    @staticmethod
    def change_password(
        db: Session,
        user_id: int,
        current_password: str,
        new_password: str
    ) -> bool:
        """
        Cambiar contraseña del usuario

        Raises:
            ValidationException si la contraseña actual es incorrecta
        """
        user = UserService.get_user_by_id(db, user_id)

        # Verificar contraseña actual
        if not verify_password(current_password, user.hashed_password):
            raise ValidationException("Contraseña actual incorrecta")

        # Actualizar
        user.hashed_password = hash_password(new_password)
        db.commit()

        return True

    @staticmethod
    def list_users(
        db: Session,
        tenant_id: int,
        filters: schemas.UserFilterParams
    ) -> tuple[list[User], int]:
        """
        Listar usuarios de un tenant con filtros y paginación

        Returns:
            (users, total_count)
        """
        query = db.query(User).filter(User.tenant_id == tenant_id)

        # Filtros
        if filters.search:
            search_term = f"%{filters.search}%"
            query = query.filter(
                or_(
                    User.email.ilike(search_term),
                    User.first_name.ilike(search_term),
                    User.last_name.ilike(search_term)
                )
            )

        if filters.role:
            query = query.filter(User.role == filters.role)

        if filters.is_active is not None:
            query = query.filter(User.is_active == filters.is_active)

        if filters.department:
            query = query.filter(User.department == filters.department)

        # Total count
        total = query.count()

        # Paginación
        users = query.offset(filters.offset).limit(filters.page_size).all()

        return users, total

    # Invitations

    @staticmethod
    def create_invitation(
        db: Session,
        tenant_id: int,
        inviter_id: int,
        data: schemas.InviteUserRequest
    ) -> UserInvitation:
        """
        Crear invitación de usuario

        Raises:
            AlreadyExistsException si el email ya existe o tiene invitación pendiente
            ValidationException si se excede límite de usuarios
        """
        # Validar que el email no exista
        existing_user = UserService.get_user_by_email(db, data.email)
        if existing_user:
            raise AlreadyExistsException(f"Usuario con email '{data.email}' ya existe")

        # Validar invitación pendiente
        existing_invitation = db.query(UserInvitation).filter(
            and_(
                UserInvitation.email == data.email,
                UserInvitation.tenant_id == tenant_id,
                UserInvitation.is_accepted == False
            )
        ).first()

        if existing_invitation and existing_invitation.is_valid:
            raise AlreadyExistsException("Ya existe una invitación pendiente para este email")

        # Validar límites del tenant
        if not TenantService.check_user_limit(db, tenant_id):
            raise ValidationException("Límite de usuarios alcanzado")

        # Crear invitación
        token = generate_random_string(32)
        expires_at = datetime.utcnow() + timedelta(days=7)  # 7 días

        invitation = UserInvitation(
            email=data.email,
            token=token,
            role=data.role,
            tenant_id=tenant_id,
            invited_by=inviter_id,
            expires_at=expires_at
        )

        db.add(invitation)
        db.commit()
        db.refresh(invitation)

        return invitation

    @staticmethod
    def accept_invitation(
        db: Session,
        token: str,
        data: schemas.AcceptInvitationRequest
    ) -> User:
        """
        Aceptar invitación y crear usuario

        Raises:
            ValidationException si el token es inválido
        """
        # Buscar invitación
        invitation = db.query(UserInvitation).filter(
            UserInvitation.token == token
        ).first()

        if not invitation or not invitation.is_valid:
            raise ValidationException("Invitación inválida o expirada")

        # Crear usuario
        user_data = schemas.UserCreate(
            email=invitation.email,
            password=data.password,
            first_name=data.first_name,
            last_name=data.last_name,
            role=invitation.role,
            tenant_id=invitation.tenant_id
        )

        user = UserService.create_user(db, user_data)

        # Marcar invitación como aceptada
        invitation.is_accepted = True
        invitation.accepted_at = datetime.utcnow()
        db.commit()

        return user

    @staticmethod
    def cancel_invitation(db: Session, invitation_id: int, tenant_id: int) -> bool:
        """Cancelar invitación"""
        invitation = db.query(UserInvitation).filter(
            UserInvitation.id == invitation_id,
            UserInvitation.tenant_id == tenant_id
        ).first()

        if not invitation:
            raise NotFoundException("Invitación")

        if invitation.is_accepted:
            raise ValidationException("No se puede cancelar una invitación ya aceptada")

        db.delete(invitation)
        db.commit()

        return True

    @staticmethod
    def list_invitations(
        db: Session,
        tenant_id: int,
        include_accepted: bool = False
    ) -> list[UserInvitation]:
        """Listar invitaciones de un tenant"""
        query = db.query(UserInvitation).filter(
            UserInvitation.tenant_id == tenant_id
        )

        if not include_accepted:
            query = query.filter(UserInvitation.is_accepted == False)

        return query.order_by(UserInvitation.created_at.desc()).all()
```

## 4. Router (router.py)

### User Endpoints

```python
from fastapi import APIRouter, Depends, status, UploadFile, File, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.schemas import SuccessResponse, PaginatedResponse
from app.core.enums import UserRole
from app.core.storage import storage_service
from app.core.exceptions import ForbiddenException, ValidationException
from app.users import schemas, service
from app.users.models import User
from app.auth.dependencies import get_current_user, require_role
from app.tenants.models import Tenant
from app.tenants.dependencies import get_current_tenant

router = APIRouter(prefix="/users", tags=["Users"])

# User CRUD

@router.get("/me", response_model=schemas.UserResponse)
async def get_my_profile(current_user: User = Depends(get_current_user)):
    """Obtener perfil del usuario actual"""
    return current_user

@router.patch("/me", response_model=schemas.UserResponse)
async def update_my_profile(
    data: schemas.UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Actualizar perfil del usuario actual"""
    user = service.UserService.update_user(db, current_user.id, data)
    return user

@router.post("/me/change-password", response_model=SuccessResponse)
async def change_my_password(
    data: schemas.ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cambiar contraseña del usuario actual"""
    service.UserService.change_password(
        db,
        current_user.id,
        data.current_password,
        data.new_password
    )
    return SuccessResponse(message="Contraseña actualizada exitosamente")

@router.post("/me/avatar", response_model=schemas.AvatarUploadResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Subir avatar del usuario

    - Max 2MB
    - Formatos: PNG, JPG
    """
    # Validar tamaño
    file_data = await file.read()
    if len(file_data) > 2 * 1024 * 1024:  # 2MB
        raise ValidationException("Archivo muy grande. Máximo 2MB")

    # Validar tipo
    if file.content_type not in ["image/png", "image/jpeg"]:
        raise ValidationException("Formato inválido. Solo PNG, JPG")

    # Subir
    filename = f"avatar_{current_user.id}_{file.filename}"
    url = await storage_service.upload_file(
        file_data,
        filename,
        folder=f"users/{current_user.id}/avatar",
        content_type=file.content_type
    )

    # Actualizar usuario
    service.UserService.update_user(
        db,
        current_user.id,
        schemas.UserUpdate(avatar_url=url)
    )

    return {"url": url}

# Admin endpoints

@router.get("", response_model=PaginatedResponse[schemas.UserListResponse])
async def list_users(
    filters: schemas.UserFilterParams = Depends(),
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(require_role(UserRole.TENANT_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Listar usuarios del tenant

    - Solo TENANT_ADMIN o SUPER_ADMIN
    """
    users, total = service.UserService.list_users(db, tenant.id, filters)

    return PaginatedResponse(
        data=users,
        total=total,
        page=filters.page,
        page_size=filters.page_size,
        total_pages=(total + filters.page_size - 1) // filters.page_size
    )

@router.get("/{user_id}", response_model=schemas.UserResponse)
async def get_user(
    user_id: int,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(require_role(UserRole.TENANT_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Obtener usuario por ID

    - Solo TENANT_ADMIN o SUPER_ADMIN
    """
    user = service.UserService.get_user_by_id(db, user_id)

    # Validar que pertenece al tenant
    if user.tenant_id != tenant.id and current_user.role != UserRole.SUPER_ADMIN:
        raise ForbiddenException("Este usuario no pertenece a tu organización")

    return user

@router.patch("/{user_id}", response_model=schemas.UserResponse)
async def update_user(
    user_id: int,
    data: schemas.UserUpdateByAdmin,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(require_role(UserRole.TENANT_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Actualizar usuario

    - Solo TENANT_ADMIN o SUPER_ADMIN
    """
    user = service.UserService.get_user_by_id(db, user_id)

    # Validar tenant
    if user.tenant_id != tenant.id and current_user.role != UserRole.SUPER_ADMIN:
        raise ForbiddenException("Este usuario no pertenece a tu organización")

    updated_user = service.UserService.update_user(db, user_id, data)
    return updated_user

@router.delete("/{user_id}", response_model=SuccessResponse)
async def delete_user(
    user_id: int,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(require_role(UserRole.TENANT_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Eliminar usuario (soft delete)

    - Solo TENANT_ADMIN o SUPER_ADMIN
    """
    user = service.UserService.get_user_by_id(db, user_id)

    # Validar tenant
    if user.tenant_id != tenant.id and current_user.role != UserRole.SUPER_ADMIN:
        raise ForbiddenException("Este usuario no pertenece a tu organización")

    # No puede eliminarse a sí mismo
    if user.id == current_user.id:
        raise ValidationException("No puedes eliminarte a ti mismo")

    service.UserService.delete_user(db, user_id)
    return SuccessResponse(message="Usuario eliminado exitosamente")

# Invitations

@router.post("/invitations", response_model=schemas.UserInvitationResponse, status_code=status.HTTP_201_CREATED)
async def invite_user(
    data: schemas.InviteUserRequest,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(require_role(UserRole.TENANT_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Invitar usuario al tenant

    - Solo TENANT_ADMIN
    - Envía email con link de invitación
    """
    invitation = service.UserService.create_invitation(
        db,
        tenant.id,
        current_user.id,
        data
    )

    # TODO: Enviar email de invitación (módulo notifications)
    # await notifications_service.send_invitation_email(invitation)

    return invitation

@router.get("/invitations", response_model=list[schemas.UserInvitationResponse])
async def list_invitations(
    include_accepted: bool = Query(False),
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(require_role(UserRole.TENANT_ADMIN)),
    db: Session = Depends(get_db)
):
    """Listar invitaciones del tenant"""
    invitations = service.UserService.list_invitations(db, tenant.id, include_accepted)
    return invitations

@router.post("/invitations/accept", response_model=schemas.UserResponse)
async def accept_invitation(
    data: schemas.AcceptInvitationRequest,
    db: Session = Depends(get_db)
):
    """
    Aceptar invitación y crear cuenta

    - Endpoint público (no requiere auth)
    """
    user = service.UserService.accept_invitation(db, data.token, data)
    return user

@router.delete("/invitations/{invitation_id}", response_model=SuccessResponse)
async def cancel_invitation(
    invitation_id: int,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(require_role(UserRole.TENANT_ADMIN)),
    db: Session = Depends(get_db)
):
    """Cancelar invitación"""
    service.UserService.cancel_invitation(db, invitation_id, tenant.id)
    return SuccessResponse(message="Invitación cancelada")
```

## 5. Exceptions (exceptions.py)

```python
from app.core.exceptions import HabilitatException
from fastapi import status

class UserNotFoundException(HabilitatException):
    def __init__(self):
        super().__init__(
            detail="Usuario no encontrado",
            status_code=status.HTTP_404_NOT_FOUND
        )

class UserLimitReachedException(HabilitatException):
    def __init__(self):
        super().__init__(
            detail="Límite de usuarios alcanzado",
            status_code=status.HTTP_400_BAD_REQUEST
        )

class InvitationNotFoundException(HabilitatException):
    def __init__(self):
        super().__init__(
            detail="Invitación no encontrada",
            status_code=status.HTTP_404_NOT_FOUND
        )

class InvitationExpiredException(HabilitatException):
    def __init__(self):
        super().__init__(
            detail="Invitación expirada",
            status_code=status.HTTP_400_BAD_REQUEST
        )
```

## Dependencias entre Módulos

**Depende de:**
- Core (config, database, security, exceptions)
- Tenants (validación de límites)

**Es usado por:**
- Auth (creación de usuarios en register)
- Onboarding (asignaciones a usuarios)
- Analytics (reportes de usuarios)

## Testing

### Tests Requeridos

1. **CRUD:** Create, read, update, delete users
2. **Password:** Change password, validación
3. **Invitations:** Create, accept, cancel, expired
4. **Filters:** List con búsqueda, roles, departamentos
5. **Avatar:** Upload, validación de tamaño/tipo
6. **Permissions:** Validar que usuarios solo vean su tenant

### Ejemplo Test

```python
# tests/users/test_service.py
from app.users.service import UserService
from app.users.schemas import UserCreate

def test_create_user(db, test_tenant):
    data = UserCreate(
        email="newuser@example.com",
        password="SecurePass123!",
        first_name="John",
        last_name="Doe",
        tenant_id=test_tenant.id
    )

    user = UserService.create_user(db, data)

    assert user.id is not None
    assert user.email == "newuser@example.com"
    assert user.full_name == "John Doe"
    assert user.hashed_password != "SecurePass123!"  # Debe estar hasheado

def test_duplicate_email_raises_error(db, test_user):
    data = UserCreate(
        email=test_user.email,  # Email duplicado
        password="SecurePass123!",
        first_name="Jane",
        last_name="Doe"
    )

    with pytest.raises(AlreadyExistsException):
        UserService.create_user(db, data)
```

## Checklist de Implementación

- [ ] Modelos User y UserInvitation
- [ ] Schemas de request/response
- [ ] UserService con CRUD completo
- [ ] Router con endpoints
- [ ] Sistema de invitaciones
- [ ] Upload de avatar
- [ ] Filtros y búsqueda
- [ ] Validación de límites de tenant
- [ ] Tests con 80%+ coverage

## Notas de Implementación

1. **Orden:** Implementar después de Core, Auth y Tenants
2. **Passwords:** Siempre hashear antes de guardar
3. **Invitations:** Validar que no existan usuarios o invitaciones duplicadas
4. **Limits:** Verificar límites del tenant antes de crear usuarios
5. **Soft Delete:** No borrar físicamente, usar deleted_at

## Dependencias de Python

Ninguna adicional, usa las de Core y Auth.
