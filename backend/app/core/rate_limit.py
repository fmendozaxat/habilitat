"""
Rate limiting module using slowapi.
Provides rate limiting for API endpoints.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.config import settings


def get_client_ip(request: Request) -> str:
    """
    Get client IP address from request.
    Handles X-Forwarded-For header for proxied requests.
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return get_remote_address(request)


# Create limiter instance
limiter = Limiter(
    key_func=get_client_ip,
    default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"],
    storage_uri="memory://",  # Use Redis in production: "redis://localhost:6379"
    strategy="fixed-window"
)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Custom handler for rate limit exceeded errors."""
    return JSONResponse(
        status_code=429,
        content={
            "success": False,
            "error": "Too Many Requests",
            "detail": f"Rate limit exceeded. Try again in {exc.detail}",
            "retry_after": str(exc.detail)
        },
        headers={"Retry-After": str(exc.detail)}
    )


# Rate limit decorators for common use cases
def login_rate_limit():
    """Rate limit for login endpoint - stricter limit."""
    return limiter.limit(f"{settings.RATE_LIMIT_LOGIN_PER_MINUTE}/minute")


def standard_rate_limit():
    """Standard rate limit for API endpoints."""
    return limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")


def strict_rate_limit():
    """Strict rate limit for sensitive operations."""
    return limiter.limit("10/minute")
