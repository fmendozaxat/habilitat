"""FastAPI dependencies for authentication."""

from fastapi import Depends
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
    """Get current user from JWT token."""
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

    user = db.query(User).filter(
        User.id == int(user_id),
        User.deleted_at.is_(None)
    ).first()

    if user is None:
        raise UnauthorizedException("Usuario no encontrado")

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Ensure user is active."""
    if not current_user.is_active:
        raise ForbiddenException("Usuario inactivo")

    return current_user


def require_role(required_role: UserRole):
    """Require specific role."""
    async def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role != required_role.value:
            raise ForbiddenException(f"Requiere rol: {required_role.value}")
        return current_user

    return role_checker


def require_any_role(*roles: UserRole):
    """Require any of the specified roles."""
    async def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        role_values = [r.value for r in roles]
        if current_user.role not in role_values:
            raise ForbiddenException(f"Requiere uno de los roles: {', '.join(role_values)}")
        return current_user

    return role_checker


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db)
) -> User | None:
    """Optional user dependency - returns None if no token."""
    if not credentials:
        return None

    try:
        return await get_current_user(credentials, db)
    except:
        return None
