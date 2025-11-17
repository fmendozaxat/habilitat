# Módulo 2: Auth (Autenticación y Autorización)

## Descripción

El módulo Auth maneja todo lo relacionado con autenticación y autorización de usuarios: login, registro, tokens JWT, recuperación de contraseña, verificación de email y control de permisos basado en roles.

**Límite de líneas:** ~2500-3500 líneas

## Responsabilidades

1. Login y logout de usuarios
2. Generación y validación de JWT tokens (access + refresh)
3. Recuperación y reset de contraseña
4. Verificación de email
5. Refresh de tokens
6. Permisos y roles (RBAC - Role Based Access Control)
7. Dependencies para proteger endpoints

## Estructura de Archivos

```
app/auth/
├── __init__.py
├── models.py              # Modelos de RefreshToken, PasswordReset
├── schemas.py             # Login, Register, Token responses
├── service.py             # Lógica de autenticación
├── router.py              # Endpoints de auth
├── dependencies.py        # get_current_user, require_role
├── exceptions.py          # Excepciones de auth
└── utils.py               # Email verification tokens, etc.
```

## 1. Modelos (models.py)

### RefreshToken Model

```python
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
from app.core.models import BaseModel, TimestampMixin

class RefreshToken(BaseModel, TimestampMixin):
    """
    Almacena refresh tokens para invalidarlos si es necesario
    """
    __tablename__ = "refresh_tokens"

    token = Column(String(500), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_revoked = Column(Boolean, default=False, nullable=False)

    # Relationships
    user = relationship("User", back_populates="refresh_tokens")

    @property
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at

    @property
    def is_valid(self) -> bool:
        return not self.is_revoked and not self.is_expired
```

### PasswordResetToken Model

```python
class PasswordResetToken(BaseModel, TimestampMixin):
    """
    Tokens para reset de contraseña
    """
    __tablename__ = "password_reset_tokens"

    token = Column(String(100), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False, nullable=False)

    # Relationships
    user = relationship("User", back_populates="password_reset_tokens")

    @property
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at

    @property
    def is_valid(self) -> bool:
        return not self.is_used and not self.is_expired
```

### EmailVerificationToken Model

```python
class EmailVerificationToken(BaseModel, TimestampMixin):
    """
    Tokens para verificación de email
    """
    __tablename__ = "email_verification_tokens"

    token = Column(String(100), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False, nullable=False)

    # Relationships
    user = relationship("User", back_populates="email_verification_tokens")

    @property
    def is_valid(self) -> bool:
        return not self.is_used and not self.is_expired

    @property
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at
```

## 2. Schemas (schemas.py)

### Request Schemas

```python
from pydantic import BaseModel, EmailStr, Field, validator
from app.core.schemas import BaseSchema

# Login
class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)

# Register
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    tenant_id: int | None = None  # Para invitaciones a tenant existente

    @validator('password')
    def validate_password(cls, v):
        """
        Validar que la contraseña tenga al menos:
        - 1 mayúscula
        - 1 minúscula
        - 1 número
        """
        if not any(c.isupper() for c in v):
            raise ValueError('Debe contener al menos una mayúscula')
        if not any(c.islower() for c in v):
            raise ValueError('Debe contener al menos una minúscula')
        if not any(c.isdigit() for c in v):
            raise ValueError('Debe contener al menos un número')
        return v

# Password Reset
class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
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

# Email Verification
class EmailVerificationRequest(BaseModel):
    token: str

# Refresh Token
class RefreshTokenRequest(BaseModel):
    refresh_token: str
```

### Response Schemas

```python
from datetime import datetime

class TokenResponse(BaseSchema):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds

class UserAuthResponse(BaseSchema):
    id: int
    email: str
    first_name: str
    last_name: str
    role: str
    tenant_id: int | None
    is_email_verified: bool

class LoginResponse(BaseSchema):
    user: UserAuthResponse
    tokens: TokenResponse

class RefreshTokenResponse(BaseSchema):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
```

## 3. Service (service.py)

### AuthService Class

```python
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.core.security import verify_password, hash_password, create_access_token, create_refresh_token
from app.core.exceptions import UnauthorizedException, ValidationException
from app.core.utils import generate_random_string
from app.auth.models import RefreshToken, PasswordResetToken, EmailVerificationToken
from app.users.models import User

class AuthService:
    """Servicio de autenticación"""

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> User | None:
        """
        Autenticar usuario por email y contraseña

        Returns:
            User si las credenciales son correctas, None si no
        """
        user = db.query(User).filter(User.email == email).first()

        if not user:
            return None

        if not verify_password(password, user.hashed_password):
            return None

        return user

    @staticmethod
    def create_tokens(db: Session, user: User) -> dict:
        """
        Crear access y refresh tokens para un usuario

        Returns:
            dict con access_token, refresh_token y expires_in
        """
        # Access token
        access_token_data = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
            "tenant_id": user.tenant_id
        }
        access_token = create_access_token(access_token_data)

        # Refresh token
        refresh_token = create_refresh_token({"sub": str(user.id)})

        # Guardar refresh token en DB
        expires_at = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)

        db_refresh_token = RefreshToken(
            token=refresh_token,
            user_id=user.id,
            expires_at=expires_at
        )
        db.add(db_refresh_token)
        db.commit()

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }

    @staticmethod
    def refresh_access_token(db: Session, refresh_token: str) -> str:
        """
        Generar nuevo access token usando refresh token

        Returns:
            Nuevo access token

        Raises:
            UnauthorizedException si el refresh token es inválido
        """
        # Buscar refresh token en DB
        db_token = db.query(RefreshToken).filter(
            RefreshToken.token == refresh_token
        ).first()

        if not db_token or not db_token.is_valid:
            raise UnauthorizedException("Refresh token inválido o expirado")

        # Obtener usuario
        user = db_token.user

        # Crear nuevo access token
        access_token_data = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
            "tenant_id": user.tenant_id
        }
        access_token = create_access_token(access_token_data)

        return access_token

    @staticmethod
    def revoke_refresh_token(db: Session, refresh_token: str) -> bool:
        """Revocar un refresh token (logout)"""
        db_token = db.query(RefreshToken).filter(
            RefreshToken.token == refresh_token
        ).first()

        if db_token:
            db_token.is_revoked = True
            db.commit()
            return True

        return False

    @staticmethod
    def create_password_reset_token(db: Session, email: str) -> PasswordResetToken:
        """
        Crear token de reset de contraseña

        Returns:
            PasswordResetToken

        Raises:
            ValidationException si el email no existe
        """
        user = db.query(User).filter(User.email == email).first()

        if not user:
            # Por seguridad, no revelar si el email existe
            raise ValidationException("Si el email existe, recibirás instrucciones")

        # Generar token
        token = generate_random_string(32)
        expires_at = datetime.utcnow() + timedelta(hours=1)  # 1 hora

        reset_token = PasswordResetToken(
            token=token,
            user_id=user.id,
            expires_at=expires_at
        )

        db.add(reset_token)
        db.commit()
        db.refresh(reset_token)

        return reset_token

    @staticmethod
    def reset_password(db: Session, token: str, new_password: str) -> bool:
        """
        Resetear contraseña usando token

        Returns:
            True si fue exitoso

        Raises:
            ValidationException si el token es inválido
        """
        db_token = db.query(PasswordResetToken).filter(
            PasswordResetToken.token == token
        ).first()

        if not db_token or not db_token.is_valid:
            raise ValidationException("Token inválido o expirado")

        # Update password
        user = db_token.user
        user.hashed_password = hash_password(new_password)

        # Marcar token como usado
        db_token.is_used = True

        db.commit()

        return True

    @staticmethod
    def create_email_verification_token(db: Session, user_id: int) -> EmailVerificationToken:
        """Crear token de verificación de email"""
        token = generate_random_string(32)
        expires_at = datetime.utcnow() + timedelta(days=7)  # 7 días

        verification_token = EmailVerificationToken(
            token=token,
            user_id=user_id,
            expires_at=expires_at
        )

        db.add(verification_token)
        db.commit()
        db.refresh(verification_token)

        return verification_token

    @staticmethod
    def verify_email(db: Session, token: str) -> bool:
        """
        Verificar email usando token

        Returns:
            True si fue exitoso

        Raises:
            ValidationException si el token es inválido
        """
        db_token = db.query(EmailVerificationToken).filter(
            EmailVerificationToken.token == token
        ).first()

        if not db_token or not db_token.is_valid:
            raise ValidationException("Token de verificación inválido o expirado")

        # Marcar email como verificado
        user = db_token.user
        user.is_email_verified = True

        # Marcar token como usado
        db_token.is_used = True

        db.commit()

        return True
```

## 4. Dependencies (dependencies.py)

### Auth Dependencies

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError
from app.core.database import get_db
from app.core.security import decode_token
from app.core.exceptions import UnauthorizedException, ForbiddenException
from app.users.models import User
from app.core.enums import UserRole

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency para obtener el usuario actual desde el JWT token

    Raises:
        UnauthorizedException si el token es inválido o el usuario no existe
    """
    token = credentials.credentials

    try:
        payload = decode_token(token)

        if payload.get("type") != "access":
            raise UnauthorizedException("Token inválido")

        user_id = payload.get("sub")

        if user_id is None:
            raise UnauthorizedException("Token inválido")

    except JWTError:
        raise UnauthorizedException("Token inválido o expirado")

    user = db.query(User).filter(User.id == int(user_id)).first()

    if user is None:
        raise UnauthorizedException("Usuario no encontrado")

    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency para asegurar que el usuario esté activo

    Raises:
        ForbiddenException si el usuario está inactivo
    """
    if not current_user.is_active:
        raise ForbiddenException("Usuario inactivo")

    return current_user

def require_role(required_role: UserRole):
    """
    Dependency factory para requerir un rol específico

    Usage:
        @router.get("/admin-only", dependencies=[Depends(require_role(UserRole.TENANT_ADMIN))])
    """
    async def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role != required_role:
            raise ForbiddenException(f"Requiere rol: {required_role}")
        return current_user

    return role_checker

def require_any_role(*roles: UserRole):
    """
    Dependency factory para requerir uno de varios roles

    Usage:
        @router.get("/admin-area", dependencies=[Depends(require_any_role(UserRole.SUPER_ADMIN, UserRole.TENANT_ADMIN))])
    """
    async def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in roles:
            raise ForbiddenException(f"Requiere uno de los roles: {', '.join(roles)}")
        return current_user

    return role_checker

async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db)
) -> User | None:
    """
    Dependency para endpoints que pueden o no requerir autenticación
    Retorna None si no hay token
    """
    if not credentials:
        return None

    try:
        return await get_current_user(credentials, db)
    except:
        return None
```

## 5. Router (router.py)

### Auth Endpoints

```python
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.schemas import SuccessResponse
from app.core.exceptions import UnauthorizedException
from app.auth import schemas, service
from app.auth.dependencies import get_current_user
from app.users.models import User
from app.users import service as user_service

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=schemas.LoginResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: schemas.RegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Registrar nuevo usuario

    - Crea usuario y tenant si no se proporciona tenant_id
    - Envía email de verificación
    - Retorna tokens de autenticación
    """
    # Crear usuario (esto también crea tenant si es necesario)
    user = user_service.create_user(db, data)

    # Crear token de verificación de email
    verification_token = service.AuthService.create_email_verification_token(db, user.id)

    # TODO: Enviar email de verificación (módulo notifications)
    # await notifications_service.send_verification_email(user.email, verification_token.token)

    # Crear tokens
    tokens = service.AuthService.create_tokens(db, user)

    return {
        "user": user,
        "tokens": tokens
    }

@router.post("/login", response_model=schemas.LoginResponse)
async def login(
    data: schemas.LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Login de usuario

    - Valida credenciales
    - Retorna access y refresh tokens
    """
    user = service.AuthService.authenticate_user(db, data.email, data.password)

    if not user:
        raise UnauthorizedException("Credenciales inválidas")

    # Crear tokens
    tokens = service.AuthService.create_tokens(db, user)

    return {
        "user": user,
        "tokens": tokens
    }

@router.post("/logout", response_model=SuccessResponse)
async def logout(
    refresh_token: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Logout de usuario

    - Revoca el refresh token
    """
    service.AuthService.revoke_refresh_token(db, refresh_token)

    return SuccessResponse(message="Logout exitoso")

@router.post("/refresh", response_model=schemas.RefreshTokenResponse)
async def refresh_token(
    data: schemas.RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Renovar access token usando refresh token
    """
    new_access_token = service.AuthService.refresh_access_token(db, data.refresh_token)

    return {
        "access_token": new_access_token,
        "token_type": "bearer",
        "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@router.post("/password-reset/request", response_model=SuccessResponse)
async def request_password_reset(
    data: schemas.PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """
    Solicitar reset de contraseña

    - Genera token y envía email
    """
    reset_token = service.AuthService.create_password_reset_token(db, data.email)

    # TODO: Enviar email con token (módulo notifications)
    # await notifications_service.send_password_reset_email(data.email, reset_token.token)

    return SuccessResponse(message="Si el email existe, recibirás instrucciones")

@router.post("/password-reset/confirm", response_model=SuccessResponse)
async def confirm_password_reset(
    data: schemas.PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """
    Confirmar reset de contraseña con token
    """
    service.AuthService.reset_password(db, data.token, data.new_password)

    return SuccessResponse(message="Contraseña actualizada exitosamente")

@router.post("/verify-email", response_model=SuccessResponse)
async def verify_email(
    data: schemas.EmailVerificationRequest,
    db: Session = Depends(get_db)
):
    """
    Verificar email con token
    """
    service.AuthService.verify_email(db, data.token)

    return SuccessResponse(message="Email verificado exitosamente")

@router.get("/me", response_model=schemas.UserAuthResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Obtener información del usuario actual
    """
    return current_user
```

## 6. Exceptions (exceptions.py)

```python
from app.core.exceptions import HabilitatException
from fastapi import status

class InvalidCredentialsException(HabilitatException):
    def __init__(self):
        super().__init__(
            detail="Credenciales inválidas",
            status_code=status.HTTP_401_UNAUTHORIZED
        )

class TokenExpiredException(HabilitatException):
    def __init__(self):
        super().__init__(
            detail="Token expirado",
            status_code=status.HTTP_401_UNAUTHORIZED
        )

class EmailAlreadyVerifiedException(HabilitatException):
    def __init__(self):
        super().__init__(
            detail="Email ya verificado",
            status_code=status.HTTP_400_BAD_REQUEST
        )

class EmailNotVerifiedException(HabilitatException):
    def __init__(self):
        super().__init__(
            detail="Email no verificado",
            status_code=status.HTTP_403_FORBIDDEN
        )
```

## Dependencias entre Módulos

**Depende de:**
- Core (config, security, exceptions, models base)
- Users (modelos de User) - relación circular manejada

**Es usado por:**
- Todos los módulos que requieran autenticación

## Testing

### Tests Requeridos

1. **Login:** Credenciales correctas/incorrectas
2. **Register:** Usuario nuevo, email duplicado
3. **Tokens:** Generación, validación, refresh, revoke
4. **Password Reset:** Request, confirm, token inválido
5. **Email Verification:** Verify, token expirado
6. **Dependencies:** get_current_user, require_role

### Ejemplo Test

```python
# tests/auth/test_login.py
from fastapi.testclient import TestClient

def test_login_success(client: TestClient, test_user):
    response = client.post("/api/v1/auth/login", json={
        "email": test_user.email,
        "password": "TestPassword123"
    })

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data["tokens"]
    assert "refresh_token" in data["tokens"]
    assert data["user"]["email"] == test_user.email

def test_login_invalid_credentials(client: TestClient):
    response = client.post("/api/v1/auth/login", json={
        "email": "wrong@example.com",
        "password": "WrongPass123"
    })

    assert response.status_code == 401
```

## Checklist de Implementación

- [ ] Modelos de RefreshToken, PasswordResetToken, EmailVerificationToken
- [ ] Schemas de request/response
- [ ] AuthService con todos los métodos
- [ ] Dependencies (get_current_user, require_role, etc.)
- [ ] Router con endpoints de auth
- [ ] Excepciones personalizadas
- [ ] Tests con 80%+ coverage
- [ ] Integración con módulo Users
- [ ] Integración con módulo Notifications (placeholders para MVP)

## Notas de Implementación

1. **Orden:** Implementar después de Core y en paralelo con Users/Tenants
2. **Seguridad:** Validar bien las contraseñas (complejidad mínima)
3. **Tokens:** Almacenar refresh tokens en DB para poder revocarlos
4. **Email:** Dejar placeholders para notificaciones, implementar después
5. **Testing:** Crítico tener buena cobertura en autenticación

## Dependencias de Python

```txt
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
```
