# Módulo 3: Tenants (Gestión Multitenant)

## Descripción

El módulo Tenants maneja todo lo relacionado con organizaciones/empresas en la plataforma: creación de tenants, configuración de branding, personalización visual, y resolución de tenant por subdomain o header.

**Límite de líneas:** ~2500-3500 líneas

## Responsabilidades

1. CRUD de tenants (empresas/organizaciones)
2. Configuración de branding (logo, colores, imágenes)
3. Gestión de subdominios
4. Middleware para resolución de tenant actual
5. Dependency para inyectar tenant en endpoints
6. Validación de límites por plan (usuarios, storage, etc.)
7. Settings personalizados por tenant

## Estructura de Archivos

```
app/tenants/
├── __init__.py
├── models.py              # Tenant, TenantConfig, TenantBranding
├── schemas.py             # Request/Response schemas
├── service.py             # Lógica de negocio
├── router.py              # Endpoints CRUD
├── dependencies.py        # get_current_tenant
├── exceptions.py          # Excepciones de tenant
└── utils.py               # Validación de subdomain, etc.
```

## 1. Modelos (models.py)

### Tenant Model

```python
from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON
from sqlalchemy.orm import relationship
from app.core.models import BaseModel, TimestampMixin, SoftDeleteMixin
from datetime import datetime

class Tenant(BaseModel, TimestampMixin, SoftDeleteMixin):
    """
    Modelo principal de organización/empresa
    """
    __tablename__ = "tenants"

    # Basic info
    name = Column(String(200), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)  # Para subdomain
    subdomain = Column(String(100), unique=True, nullable=True, index=True)

    # Contact
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(50), nullable=True)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)

    # Plan & Limits (para futuro billing)
    plan = Column(String(50), default="free", nullable=False)  # free, starter, business, enterprise
    max_users = Column(Integer, default=10, nullable=False)
    max_storage_mb = Column(Integer, default=1000, nullable=False)  # 1GB default

    # Settings (JSON para flexibilidad)
    settings = Column(JSON, default={}, nullable=False)
    """
    Ejemplo de settings:
    {
        "onboarding_auto_assign": true,
        "require_email_verification": true,
        "allow_self_registration": false,
        "custom_domain": "onboarding.company.com"
    }
    """

    # Relationships
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    branding = relationship("TenantBranding", back_populates="tenant", uselist=False, cascade="all, delete-orphan")
    onboarding_flows = relationship("OnboardingFlow", back_populates="tenant", cascade="all, delete-orphan")
    content_blocks = relationship("ContentBlock", back_populates="tenant", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Tenant {self.name} ({self.slug})>"

    @property
    def full_domain(self) -> str:
        """Retorna el dominio completo"""
        if self.subdomain:
            return f"{self.subdomain}.habilitat.com"
        return None
```

### TenantBranding Model

```python
class TenantBranding(BaseModel, TimestampMixin):
    """
    Configuración de branding visual del tenant
    """
    __tablename__ = "tenant_branding"

    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), unique=True, nullable=False)

    # Logo
    logo_url = Column(String(500), nullable=True)
    logo_dark_url = Column(String(500), nullable=True)  # Logo para tema oscuro (opcional)
    favicon_url = Column(String(500), nullable=True)

    # Colors (hex codes)
    primary_color = Column(String(7), default="#3B82F6", nullable=False)      # Blue
    secondary_color = Column(String(7), default="#10B981", nullable=False)    # Green
    accent_color = Column(String(7), default="#F59E0B", nullable=True)        # Amber
    background_color = Column(String(7), default="#FFFFFF", nullable=False)   # White
    text_color = Column(String(7), default="#1F2937", nullable=False)         # Gray-800

    # Images
    hero_image_url = Column(String(500), nullable=True)
    background_image_url = Column(String(500), nullable=True)

    # Typography (opcional para MVP)
    font_family = Column(String(100), nullable=True)  # e.g., "Inter", "Roboto"

    # Custom CSS (avanzado, post-MVP)
    custom_css = Column(String(5000), nullable=True)

    # Relationships
    tenant = relationship("Tenant", back_populates="branding")

    def to_theme_dict(self) -> dict:
        """Retorna diccionario con tema para el frontend"""
        return {
            "logo": self.logo_url,
            "logo_dark": self.logo_dark_url,
            "favicon": self.favicon_url,
            "colors": {
                "primary": self.primary_color,
                "secondary": self.secondary_color,
                "accent": self.accent_color,
                "background": self.background_color,
                "text": self.text_color
            },
            "images": {
                "hero": self.hero_image_url,
                "background": self.background_image_url
            },
            "typography": {
                "font_family": self.font_family
            }
        }
```

## 2. Schemas (schemas.py)

### Request Schemas

```python
from pydantic import BaseModel, Field, validator
from app.core.schemas import BaseSchema
from app.core.utils import slugify

# Tenant
class TenantCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    slug: str | None = None  # Auto-generado si no se proporciona
    subdomain: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None

    @validator('slug', always=True)
    def generate_slug(cls, v, values):
        if v:
            return slugify(v)
        if 'name' in values:
            return slugify(values['name'])
        return None

    @validator('subdomain')
    def validate_subdomain(cls, v):
        if v:
            # Solo letras, números y guiones, mínimo 3 caracteres
            import re
            if not re.match(r'^[a-z0-9-]{3,}$', v):
                raise ValueError('Subdomain inválido. Solo letras minúsculas, números y guiones.')
        return v

class TenantUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=200)
    contact_email: str | None = None
    contact_phone: str | None = None
    is_active: bool | None = None
    settings: dict | None = None

# Branding
class TenantBrandingUpdate(BaseModel):
    logo_url: str | None = None
    logo_dark_url: str | None = None
    favicon_url: str | None = None
    primary_color: str | None = Field(None, regex=r'^#[0-9A-Fa-f]{6}$')
    secondary_color: str | None = Field(None, regex=r'^#[0-9A-Fa-f]{6}$')
    accent_color: str | None = Field(None, regex=r'^#[0-9A-Fa-f]{6}$')
    background_color: str | None = Field(None, regex=r'^#[0-9A-Fa-f]{6}$')
    text_color: str | None = Field(None, regex=r'^#[0-9A-Fa-f]{6}$')
    hero_image_url: str | None = None
    background_image_url: str | None = None
    font_family: str | None = None

# Logo Upload
class LogoUploadResponse(BaseSchema):
    url: str
```

### Response Schemas

```python
from datetime import datetime

class TenantBrandingResponse(BaseSchema):
    id: int
    tenant_id: int
    logo_url: str | None
    logo_dark_url: str | None
    favicon_url: str | None
    primary_color: str
    secondary_color: str
    accent_color: str | None
    background_color: str
    text_color: str
    hero_image_url: str | None
    background_image_url: str | None
    font_family: str | None

class TenantResponse(BaseSchema):
    id: int
    name: str
    slug: str
    subdomain: str | None
    contact_email: str | None
    contact_phone: str | None
    is_active: bool
    plan: str
    max_users: int
    max_storage_mb: int
    settings: dict
    branding: TenantBrandingResponse | None
    created_at: datetime
    updated_at: datetime

class TenantListResponse(BaseSchema):
    id: int
    name: str
    slug: str
    subdomain: str | None
    is_active: bool
    plan: str
    created_at: datetime

class TenantThemeResponse(BaseSchema):
    """Respuesta simplificada para el frontend"""
    logo: str | None
    logo_dark: str | None
    favicon: str | None
    colors: dict
    images: dict
    typography: dict
```

## 3. Service (service.py)

### TenantService Class

```python
from sqlalchemy.orm import Session
from app.core.exceptions import NotFoundException, AlreadyExistsException, ValidationException
from app.tenants.models import Tenant, TenantBranding
from app.tenants import schemas
from app.core.utils import slugify

class TenantService:
    """Servicio de gestión de tenants"""

    @staticmethod
    def get_tenant_by_id(db: Session, tenant_id: int) -> Tenant:
        """Obtener tenant por ID"""
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            raise NotFoundException("Tenant")
        return tenant

    @staticmethod
    def get_tenant_by_slug(db: Session, slug: str) -> Tenant | None:
        """Obtener tenant por slug"""
        return db.query(Tenant).filter(Tenant.slug == slug).first()

    @staticmethod
    def get_tenant_by_subdomain(db: Session, subdomain: str) -> Tenant | None:
        """Obtener tenant por subdomain"""
        return db.query(Tenant).filter(Tenant.subdomain == subdomain).first()

    @staticmethod
    def create_tenant(db: Session, data: schemas.TenantCreate) -> Tenant:
        """
        Crear nuevo tenant

        Raises:
            AlreadyExistsException si el slug o subdomain ya existe
        """
        # Validar que slug no exista
        existing = TenantService.get_tenant_by_slug(db, data.slug)
        if existing:
            raise AlreadyExistsException(f"Tenant con slug '{data.slug}'")

        # Validar subdomain si se proporciona
        if data.subdomain:
            existing = TenantService.get_tenant_by_subdomain(db, data.subdomain)
            if existing:
                raise AlreadyExistsException(f"Tenant con subdomain '{data.subdomain}'")

        # Crear tenant
        tenant = Tenant(**data.model_dump())
        db.add(tenant)
        db.flush()  # Para obtener el ID

        # Crear branding default
        branding = TenantBranding(tenant_id=tenant.id)
        db.add(branding)

        db.commit()
        db.refresh(tenant)

        return tenant

    @staticmethod
    def update_tenant(db: Session, tenant_id: int, data: schemas.TenantUpdate) -> Tenant:
        """Actualizar tenant"""
        tenant = TenantService.get_tenant_by_id(db, tenant_id)

        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(tenant, field, value)

        db.commit()
        db.refresh(tenant)

        return tenant

    @staticmethod
    def delete_tenant(db: Session, tenant_id: int) -> bool:
        """
        Soft delete de tenant

        Esto marcará el tenant como eliminado pero no lo borrará de la DB
        """
        tenant = TenantService.get_tenant_by_id(db, tenant_id)
        tenant.deleted_at = datetime.utcnow()
        tenant.is_active = False
        db.commit()
        return True

    @staticmethod
    def get_tenant_branding(db: Session, tenant_id: int) -> TenantBranding:
        """Obtener branding del tenant"""
        branding = db.query(TenantBranding).filter(
            TenantBranding.tenant_id == tenant_id
        ).first()

        if not branding:
            raise NotFoundException("Branding")

        return branding

    @staticmethod
    def update_branding(
        db: Session,
        tenant_id: int,
        data: schemas.TenantBrandingUpdate
    ) -> TenantBranding:
        """Actualizar branding del tenant"""
        branding = TenantService.get_tenant_branding(db, tenant_id)

        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(branding, field, value)

        db.commit()
        db.refresh(branding)

        return branding

    @staticmethod
    def check_user_limit(db: Session, tenant_id: int) -> bool:
        """
        Verificar si el tenant puede agregar más usuarios

        Returns:
            True si puede agregar más usuarios
        """
        tenant = TenantService.get_tenant_by_id(db, tenant_id)

        current_user_count = len(tenant.users)

        return current_user_count < tenant.max_users

    @staticmethod
    def get_tenant_stats(db: Session, tenant_id: int) -> dict:
        """
        Obtener estadísticas del tenant

        Returns:
            dict con users_count, storage_used_mb, etc.
        """
        tenant = TenantService.get_tenant_by_id(db, tenant_id)

        return {
            "users_count": len(tenant.users),
            "max_users": tenant.max_users,
            "storage_used_mb": 0,  # TODO: Calcular storage usado
            "max_storage_mb": tenant.max_storage_mb,
            "onboarding_flows_count": len(tenant.onboarding_flows),
            "is_active": tenant.is_active,
            "plan": tenant.plan
        }
```

## 4. Dependencies (dependencies.py)

### Tenant Dependencies

```python
from fastapi import Depends, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.exceptions import TenantNotFoundException, TenantResolutionException
from app.tenants.models import Tenant
from app.tenants.service import TenantService

async def get_current_tenant(
    request: Request,
    db: Session = Depends(get_db)
) -> Tenant:
    """
    Dependency para resolver y obtener el tenant actual

    Resuelve desde:
    1. request.state.tenant_identifier (establecido por middleware)
    2. Header X-Tenant-ID

    Raises:
        TenantResolutionException si no se puede resolver
        TenantNotFoundException si el tenant no existe
    """
    # Obtener identifier del middleware
    tenant_identifier = getattr(request.state, 'tenant_identifier', None)

    if not tenant_identifier:
        # Fallback: intentar desde header directo
        tenant_identifier = request.headers.get('X-Tenant-ID')

    if not tenant_identifier:
        raise TenantResolutionException()

    # Resolver tenant (puede ser ID, slug o subdomain)
    tenant = None

    # Intentar como ID
    if tenant_identifier.isdigit():
        tenant = db.query(Tenant).filter(Tenant.id == int(tenant_identifier)).first()

    # Intentar como subdomain
    if not tenant:
        tenant = TenantService.get_tenant_by_subdomain(db, tenant_identifier)

    # Intentar como slug
    if not tenant:
        tenant = TenantService.get_tenant_by_slug(db, tenant_identifier)

    if not tenant:
        raise TenantNotFoundException()

    if not tenant.is_active:
        raise TenantResolutionException()

    return tenant

async def get_optional_tenant(
    request: Request,
    db: Session = Depends(get_db)
) -> Tenant | None:
    """
    Dependency para endpoints que pueden o no tener tenant
    Retorna None si no hay tenant
    """
    try:
        return await get_current_tenant(request, db)
    except:
        return None
```

## 5. Router (router.py)

### Tenant Endpoints

```python
from fastapi import APIRouter, Depends, status, UploadFile, File
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.schemas import SuccessResponse
from app.core.enums import UserRole
from app.tenants import schemas, service
from app.tenants.models import Tenant
from app.tenants.dependencies import get_current_tenant
from app.auth.dependencies import get_current_user, require_role
from app.users.models import User
from app.core.storage import storage_service

router = APIRouter(prefix="/tenants", tags=["Tenants"])

@router.post("", response_model=schemas.TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    data: schemas.TenantCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPER_ADMIN))
):
    """
    Crear nuevo tenant

    - Solo SUPER_ADMIN puede crear tenants
    """
    tenant = service.TenantService.create_tenant(db, data)
    return tenant

@router.get("/me", response_model=schemas.TenantResponse)
async def get_my_tenant(
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user)
):
    """
    Obtener información del tenant actual
    """
    return tenant

@router.get("/{tenant_id}", response_model=schemas.TenantResponse)
async def get_tenant(
    tenant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPER_ADMIN))
):
    """
    Obtener tenant por ID

    - Solo SUPER_ADMIN
    """
    tenant = service.TenantService.get_tenant_by_id(db, tenant_id)
    return tenant

@router.patch("/{tenant_id}", response_model=schemas.TenantResponse)
async def update_tenant(
    tenant_id: int,
    data: schemas.TenantUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Actualizar tenant

    - SUPER_ADMIN puede actualizar cualquier tenant
    - TENANT_ADMIN solo puede actualizar su propio tenant
    """
    # Validar permisos
    if current_user.role != UserRole.SUPER_ADMIN:
        if current_user.tenant_id != tenant_id:
            raise ForbiddenException("No puedes actualizar este tenant")

    tenant = service.TenantService.update_tenant(db, tenant_id, data)
    return tenant

@router.delete("/{tenant_id}", response_model=SuccessResponse)
async def delete_tenant(
    tenant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPER_ADMIN))
):
    """
    Eliminar tenant (soft delete)

    - Solo SUPER_ADMIN
    """
    service.TenantService.delete_tenant(db, tenant_id)
    return SuccessResponse(message="Tenant eliminado exitosamente")

# Branding Endpoints

@router.get("/me/branding", response_model=schemas.TenantBrandingResponse)
async def get_my_tenant_branding(
    tenant: Tenant = Depends(get_current_tenant)
):
    """
    Obtener branding del tenant actual
    """
    return tenant.branding

@router.get("/me/theme", response_model=schemas.TenantThemeResponse)
async def get_my_tenant_theme(
    tenant: Tenant = Depends(get_current_tenant)
):
    """
    Obtener tema (branding simplificado) del tenant actual

    - Endpoint público para el frontend
    """
    if not tenant.branding:
        # Retornar tema default
        return {
            "logo": None,
            "logo_dark": None,
            "favicon": None,
            "colors": {
                "primary": "#3B82F6",
                "secondary": "#10B981",
                "accent": "#F59E0B",
                "background": "#FFFFFF",
                "text": "#1F2937"
            },
            "images": {
                "hero": None,
                "background": None
            },
            "typography": {
                "font_family": None
            }
        }

    return tenant.branding.to_theme_dict()

@router.patch("/me/branding", response_model=schemas.TenantBrandingResponse)
async def update_my_tenant_branding(
    data: schemas.TenantBrandingUpdate,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(require_role(UserRole.TENANT_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Actualizar branding del tenant actual

    - Solo TENANT_ADMIN
    """
    branding = service.TenantService.update_branding(db, tenant.id, data)
    return branding

@router.post("/me/branding/logo", response_model=schemas.LogoUploadResponse)
async def upload_logo(
    file: UploadFile = File(...),
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(require_role(UserRole.TENANT_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Subir logo del tenant

    - Solo TENANT_ADMIN
    - Max 2MB
    - Formatos: PNG, JPG, SVG
    """
    # Validar tamaño
    file_data = await file.read()
    if len(file_data) > 2 * 1024 * 1024:  # 2MB
        raise ValidationException("Archivo muy grande. Máximo 2MB")

    # Validar tipo
    if file.content_type not in ["image/png", "image/jpeg", "image/svg+xml"]:
        raise ValidationException("Formato inválido. Solo PNG, JPG, SVG")

    # Subir a storage
    filename = f"logo_{tenant.id}_{file.filename}"
    url = await storage_service.upload_file(
        file_data,
        filename,
        folder=f"tenants/{tenant.id}/branding",
        content_type=file.content_type
    )

    # Actualizar branding
    branding = service.TenantService.update_branding(
        db,
        tenant.id,
        schemas.TenantBrandingUpdate(logo_url=url)
    )

    return {"url": url}

@router.get("/me/stats")
async def get_my_tenant_stats(
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(require_role(UserRole.TENANT_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Obtener estadísticas del tenant

    - Solo TENANT_ADMIN
    """
    stats = service.TenantService.get_tenant_stats(db, tenant.id)
    return stats
```

## 6. Utils (utils.py)

```python
import re

def is_valid_subdomain(subdomain: str) -> bool:
    """
    Validar formato de subdomain

    - Solo letras minúsculas, números y guiones
    - Mínimo 3 caracteres
    - No puede empezar ni terminar con guión
    """
    pattern = r'^[a-z0-9]([a-z0-9-]{1,})[a-z0-9]$'
    return bool(re.match(pattern, subdomain)) and len(subdomain) >= 3

def get_reserved_subdomains() -> list[str]:
    """
    Subdomains reservados que no se pueden usar
    """
    return [
        "www", "api", "app", "admin", "dashboard",
        "mail", "email", "smtp", "ftp", "cdn",
        "static", "assets", "media", "images",
        "dev", "staging", "test", "demo"
    ]

def validate_subdomain_availability(subdomain: str) -> tuple[bool, str]:
    """
    Validar que un subdomain esté disponible

    Returns:
        (is_valid, error_message)
    """
    if not is_valid_subdomain(subdomain):
        return False, "Formato de subdomain inválido"

    if subdomain in get_reserved_subdomains():
        return False, "Este subdomain está reservado"

    return True, ""
```

## Dependencias entre Módulos

**Depende de:**
- Core (config, database, exceptions, models base, storage)

**Es usado por:**
- Auth (al registrar usuarios)
- Users (relación de usuario a tenant)
- Onboarding (flujos por tenant)
- Content (contenido por tenant)
- Todos los módulos que necesiten saber el tenant actual

## Testing

### Tests Requeridos

1. **CRUD:** Create, read, update, delete tenants
2. **Branding:** Get, update branding
3. **Validation:** Subdomain validation, reserved names
4. **Dependencies:** get_current_tenant resolution
5. **Logo Upload:** Upload, size/type validation
6. **Stats:** User count, storage, etc.

### Ejemplo Test

```python
# tests/tenants/test_service.py
from app.tenants.service import TenantService
from app.tenants.schemas import TenantCreate

def test_create_tenant(db):
    data = TenantCreate(
        name="Test Company",
        slug="test-company",
        contact_email="test@example.com"
    )

    tenant = TenantService.create_tenant(db, data)

    assert tenant.id is not None
    assert tenant.name == "Test Company"
    assert tenant.slug == "test-company"
    assert tenant.branding is not None  # Debe crear branding default

def test_duplicate_slug_raises_error(db, test_tenant):
    data = TenantCreate(
        name="Another Company",
        slug=test_tenant.slug  # Mismo slug
    )

    with pytest.raises(AlreadyExistsException):
        TenantService.create_tenant(db, data)
```

## Checklist de Implementación

- [ ] Modelos Tenant y TenantBranding
- [ ] Schemas de request/response
- [ ] TenantService con CRUD completo
- [ ] Dependencies (get_current_tenant)
- [ ] Router con endpoints
- [ ] Utils de validación de subdomain
- [ ] Upload de logos
- [ ] Integración con middleware de Core
- [ ] Tests con 80%+ coverage

## Notas de Implementación

1. **Orden:** Implementar después de Core, en paralelo con Auth/Users
2. **Middleware:** Asegurar que el TenantMiddleware en Core funcione correctamente
3. **Branding:** Crear branding default al crear tenant
4. **Subdomain:** Por ahora resolver desde header, subdomains reales en producción
5. **Limits:** Implementar checks de límites (max_users) antes de crear usuarios

## Dependencias de Python

Ninguna adicional, usa las de Core.
