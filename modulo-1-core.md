# Módulo 1: Core (Infraestructura Base)

## Descripción

El módulo Core es la base de toda la aplicación. Proporciona la infraestructura común que todos los demás módulos utilizan: configuración, base de datos, middlewares, utilidades, excepciones y servicios de storage.

**Límite de líneas:** ~3000-4000 líneas

## Responsabilidades

1. Configuración global de la aplicación
2. Gestión de conexión a base de datos
3. Middlewares compartidos (CORS, tenant resolution, logging)
4. Excepciones personalizadas
5. Utilidades comunes (hashing, validaciones, helpers)
6. Servicio de storage (S3/Cloudinary)
7. Base models y mixins
8. Constantes y enums globales

## Estructura de Archivos

```
app/core/
├── __init__.py
├── config.py              # Configuración y environment variables
├── database.py            # SQLAlchemy setup y sesiones
├── middleware.py          # Middlewares customizados
├── exceptions.py          # Excepciones personalizadas
├── security.py            # Hashing, password utils
├── storage.py             # AWS S3 / Cloudinary integration
├── models.py              # Base models y mixins
├── schemas.py             # Schemas base (paginación, respuestas)
├── constants.py           # Constantes globales
├── enums.py               # Enums globales
└── utils.py               # Utilidades comunes
```

## 1. Configuración (config.py)

### Settings Class

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # App
    APP_NAME: str = "Habilitat"
    APP_ENV: str = "development"
    API_PREFIX: str = "/api/v1"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    CORS_ALLOW_CREDENTIALS: bool = True

    # Storage (AWS S3)
    AWS_ACCESS_KEY_ID: str | None = None
    AWS_SECRET_ACCESS_KEY: str | None = None
    AWS_BUCKET_NAME: str | None = None
    AWS_REGION: str = "us-east-1"

    # Cloudinary (alternativa)
    CLOUDINARY_CLOUD_NAME: str | None = None
    CLOUDINARY_API_KEY: str | None = None
    CLOUDINARY_API_SECRET: str | None = None

    # Email
    SENDGRID_API_KEY: str | None = None
    FROM_EMAIL: str = "noreply@habilitat.com"

    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

## 2. Base de Datos (database.py)

### SQLAlchemy Setup

```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

## 3. Models Base (models.py)

### Mixins y Base Models

```python
from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, String
from sqlalchemy.ext.declarative import declared_attr

class TimestampMixin:
    """Agrega created_at y updated_at a modelos"""
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class TenantMixin:
    """Agrega tenant_id a modelos multitenant"""
    @declared_attr
    def tenant_id(cls):
        return Column(Integer, nullable=False, index=True)

class BaseModel(Base):
    """Base model para todos los modelos"""
    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True)

class SoftDeleteMixin:
    """Soft delete functionality"""
    deleted_at = Column(DateTime, nullable=True, default=None)

    @property
    def is_deleted(self):
        return self.deleted_at is not None
```

## 4. Schemas Base (schemas.py)

### Pydantic Schemas Comunes

```python
from pydantic import BaseModel, ConfigDict
from typing import Generic, TypeVar

class BaseSchema(BaseModel):
    """Base para todos los schemas"""
    model_config = ConfigDict(from_attributes=True)

# Paginación
class PaginationParams(BaseModel):
    page: int = 1
    page_size: int = 20

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

DataT = TypeVar('DataT')

class PaginatedResponse(BaseModel, Generic[DataT]):
    data: list[DataT]
    total: int
    page: int
    page_size: int
    total_pages: int

# Respuestas estándar
class SuccessResponse(BaseModel):
    success: bool = True
    message: str

class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    detail: str | None = None
```

## 5. Excepciones (exceptions.py)

### Custom Exceptions

```python
from fastapi import HTTPException, status

class HabilitatException(HTTPException):
    """Base exception para la aplicación"""
    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(status_code=status_code, detail=detail)

# Auth
class UnauthorizedException(HabilitatException):
    def __init__(self, detail: str = "No autorizado"):
        super().__init__(detail=detail, status_code=status.HTTP_401_UNAUTHORIZED)

class ForbiddenException(HabilitatException):
    def __init__(self, detail: str = "Acceso denegado"):
        super().__init__(detail=detail, status_code=status.HTTP_403_FORBIDDEN)

# Resources
class NotFoundException(HabilitatException):
    def __init__(self, resource: str = "Recurso"):
        super().__init__(detail=f"{resource} no encontrado", status_code=status.HTTP_404_NOT_FOUND)

class AlreadyExistsException(HabilitatException):
    def __init__(self, resource: str = "Recurso"):
        super().__init__(detail=f"{resource} ya existe", status_code=status.HTTP_409_CONFLICT)

# Validation
class ValidationException(HabilitatException):
    def __init__(self, detail: str):
        super().__init__(detail=detail, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)

# Tenant
class TenantNotFoundException(NotFoundException):
    def __init__(self):
        super().__init__(resource="Tenant")

class TenantResolutionException(HabilitatException):
    def __init__(self):
        super().__init__(detail="No se pudo resolver el tenant", status_code=status.HTTP_400_BAD_REQUEST)
```

## 6. Middleware (middleware.py)

### Tenant Resolution Middleware

```python
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request

class TenantMiddleware(BaseHTTPMiddleware):
    """
    Resuelve el tenant desde:
    1. Subdomain (tenant.habilitat.com)
    2. Header X-Tenant-ID
    3. Query param ?tenant=xxx (solo para desarrollo)
    """

    async def dispatch(self, request: Request, call_next):
        tenant_identifier = None

        # 1. Desde subdomain
        host = request.headers.get("host", "")
        parts = host.split(".")
        if len(parts) > 2:  # tiene subdomain
            tenant_identifier = parts[0]

        # 2. Desde header (fallback)
        if not tenant_identifier:
            tenant_identifier = request.headers.get("X-Tenant-ID")

        # 3. Desde query (solo dev)
        if not tenant_identifier and settings.APP_ENV == "development":
            tenant_identifier = request.query_params.get("tenant")

        # Guardar en request.state para acceso posterior
        request.state.tenant_identifier = tenant_identifier

        response = await call_next(request)
        return response

class LoggingMiddleware(BaseHTTPMiddleware):
    """Logs de requests"""
    async def dispatch(self, request: Request, call_next):
        # Log request
        logger.info(f"{request.method} {request.url.path}")

        response = await call_next(request)

        # Log response
        logger.info(f"Status: {response.status_code}")

        return response
```

## 7. Security (security.py)

### Password Hashing y JWT Utilities

```python
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "type": "access"})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({"exp": expire, "type": "refresh"})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt

def decode_token(token: str) -> dict:
    """Decode and validate JWT token"""
    return jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM]
    )
```

## 8. Storage (storage.py)

### AWS S3 / Cloudinary Integration

```python
import boto3
from botocore.exceptions import ClientError
import cloudinary
import cloudinary.uploader

class StorageService:
    """Abstracción para storage de archivos"""

    def __init__(self):
        self.use_cloudinary = bool(settings.CLOUDINARY_CLOUD_NAME)

        if self.use_cloudinary:
            cloudinary.config(
                cloud_name=settings.CLOUDINARY_CLOUD_NAME,
                api_key=settings.CLOUDINARY_API_KEY,
                api_secret=settings.CLOUDINARY_API_SECRET
            )
        else:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION
            )

    async def upload_file(
        self,
        file_data: bytes,
        filename: str,
        folder: str = "uploads",
        content_type: str | None = None
    ) -> str:
        """
        Upload file and return public URL

        Args:
            file_data: File bytes
            filename: Name of file
            folder: Folder/prefix
            content_type: MIME type

        Returns:
            Public URL of uploaded file
        """
        if self.use_cloudinary:
            return await self._upload_cloudinary(file_data, filename, folder)
        else:
            return await self._upload_s3(file_data, filename, folder, content_type)

    async def _upload_s3(self, file_data, filename, folder, content_type):
        key = f"{folder}/{filename}"

        try:
            self.s3_client.put_object(
                Bucket=settings.AWS_BUCKET_NAME,
                Key=key,
                Body=file_data,
                ContentType=content_type or 'application/octet-stream'
            )

            url = f"https://{settings.AWS_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{key}"
            return url
        except ClientError as e:
            raise Exception(f"Error uploading to S3: {str(e)}")

    async def _upload_cloudinary(self, file_data, filename, folder):
        result = cloudinary.uploader.upload(
            file_data,
            folder=folder,
            public_id=filename
        )
        return result['secure_url']

    async def delete_file(self, url: str) -> bool:
        """Delete file from storage"""
        # Implementation
        pass

storage_service = StorageService()
```

## 9. Utils (utils.py)

### Utilidades Comunes

```python
import re
from typing import Any
from datetime import datetime

def slugify(text: str) -> str:
    """Convert text to URL-friendly slug"""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    text = re.sub(r'^-+|-+$', '', text)
    return text

def is_valid_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def generate_random_string(length: int = 32) -> str:
    """Generate random string"""
    import secrets
    return secrets.token_urlsafe(length)

def format_datetime(dt: datetime, format: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format datetime to string"""
    return dt.strftime(format)

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for storage"""
    # Remove path separators
    filename = filename.replace('/', '_').replace('\\', '_')
    # Remove dangerous characters
    filename = re.sub(r'[^\w\s.-]', '', filename)
    return filename

def calculate_pagination(total: int, page: int, page_size: int) -> dict:
    """Calculate pagination metadata"""
    total_pages = (total + page_size - 1) // page_size

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1
    }
```

## 10. Enums (enums.py)

### Enums Globales

```python
from enum import Enum

class UserRole(str, Enum):
    """Roles de usuario"""
    SUPER_ADMIN = "super_admin"      # Admin de la plataforma
    TENANT_ADMIN = "tenant_admin"    # Admin de empresa
    EMPLOYEE = "employee"            # Empleado

class OnboardingStatus(str, Enum):
    """Estados de onboarding"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    EXPIRED = "expired"

class ContentType(str, Enum):
    """Tipos de contenido"""
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    PDF = "pdf"
    LINK = "link"

class NotificationType(str, Enum):
    """Tipos de notificación"""
    EMAIL = "email"
    IN_APP = "in_app"
    PUSH = "push"
```

## 11. Constants (constants.py)

```python
# Roles
SUPER_ADMIN_ROLE = "super_admin"
TENANT_ADMIN_ROLE = "tenant_admin"
EMPLOYEE_ROLE = "employee"

# File uploads
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/gif", "image/webp"]
ALLOWED_VIDEO_TYPES = ["video/mp4", "video/webm"]
ALLOWED_DOCUMENT_TYPES = ["application/pdf"]

# Tenant
DEFAULT_TENANT_THEME = {
    "primary_color": "#3B82F6",
    "secondary_color": "#10B981",
    "background_color": "#FFFFFF",
    "text_color": "#1F2937"
}
```

## Dependencias entre Módulos

**Este módulo NO depende de ningún otro módulo.**

Todos los demás módulos dependen de Core.

## Testing

### Tests Requeridos

1. **Config:** Validar que settings carguen correctamente
2. **Database:** Test de conexión y sesiones
3. **Security:** Tests de hashing y JWT
4. **Storage:** Mock de S3/Cloudinary uploads
5. **Utils:** Tests de utilidades (slugify, email validation, etc.)
6. **Middleware:** Test de tenant resolution

### Ejemplo Test

```python
# tests/core/test_security.py
from app.core.security import hash_password, verify_password, create_access_token, decode_token

def test_password_hashing():
    password = "SecurePass123!"
    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("WrongPassword", hashed)

def test_jwt_tokens():
    data = {"user_id": 1, "email": "test@example.com"}
    token = create_access_token(data)

    decoded = decode_token(token)
    assert decoded["user_id"] == 1
    assert decoded["email"] == "test@example.com"
    assert decoded["type"] == "access"
```

## Checklist de Implementación

- [ ] Configuración y settings con Pydantic
- [ ] SQLAlchemy setup con engine y session
- [ ] Base models con mixins (Timestamp, Tenant, SoftDelete)
- [ ] Schemas base (PaginatedResponse, SuccessResponse, etc.)
- [ ] Excepciones personalizadas
- [ ] Middleware de tenant resolution
- [ ] Middleware de logging
- [ ] Security utils (password hash, JWT)
- [ ] Storage service (S3 o Cloudinary)
- [ ] Utils comunes (slugify, email validation, etc.)
- [ ] Enums globales
- [ ] Constants globales
- [ ] Tests con 80%+ coverage

## Notas de Implementación

1. **Prioridad:** Este módulo debe ser el primero en implementarse
2. **Testing:** Fundamental tener buena cobertura en este módulo
3. **Configuración:** Usar .env.example como template
4. **Storage:** Implementar primero con archivos locales si no hay S3/Cloudinary configurado
5. **Middleware:** El TenantMiddleware es crítico para el resto de la app

## Dependencias de Python

```txt
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
sqlalchemy>=2.0.0
alembic>=1.12.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
python-multipart>=0.0.6
boto3>=1.28.0
cloudinary>=1.36.0
```
