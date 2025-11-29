"""
Main application entry point for Habilitat backend.
Initializes FastAPI application with all middlewares and configurations.
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.middleware import (
    TenantMiddleware,
    LoggingMiddleware,
    SecurityHeadersMiddleware,
    RequestIDMiddleware
)
from app.core.rate_limit import limiter, rate_limit_exceeded_handler


# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info(f"Starting {settings.APP_NAME} API")
    logger.info(f"Environment: {settings.APP_ENV}")
    logger.info(f"Debug mode: {settings.DEBUG}")

    # TODO: Initialize database connection pool
    # TODO: Load initial data if needed
    # TODO: Start background tasks

    yield

    # Shutdown
    logger.info(f"Shutting down {settings.APP_NAME} API")

    # TODO: Close database connections
    # TODO: Stop background tasks
    # TODO: Cleanup resources


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="Plataforma de Onboarding Multitenant",
    version="1.0.0",
    docs_url=f"{settings.API_PREFIX}/docs",
    redoc_url=f"{settings.API_PREFIX}/redoc",
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
    lifespan=lifespan
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)


# ============================================================================
# Middleware Configuration
# ============================================================================

# CORS - Must be first to handle preflight requests properly
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Process-Time", "X-Request-ID"]
)

# Request ID - Add unique ID to each request
app.add_middleware(RequestIDMiddleware)

# Security Headers - Add security headers to responses
app.add_middleware(SecurityHeadersMiddleware)

# Tenant Resolution - Resolve tenant from subdomain/header
app.add_middleware(TenantMiddleware)

# Logging - Log all requests and responses
app.add_middleware(LoggingMiddleware)


# ============================================================================
# Exception Handlers
# ============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Global exception handler for unhandled exceptions.
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal Server Error",
            "detail": "An unexpected error occurred" if not settings.DEBUG else str(exc)
        }
    )


# ============================================================================
# Root Routes
# ============================================================================

@app.get("/")
async def root():
    """
    Root endpoint - API health check.
    """
    return {
        "name": settings.APP_NAME,
        "version": "1.0.0",
        "status": "healthy",
        "environment": settings.APP_ENV
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring and load balancers.
    Verifies database connectivity.
    """
    from app.core.database import get_db
    from sqlalchemy import text

    health_status = {
        "status": "healthy",
        "service": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "checks": {
            "database": "unknown"
        }
    }

    # Check database connectivity
    try:
        db = next(get_db())
        db.execute(text("SELECT 1"))
        health_status["checks"]["database"] = "healthy"
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = f"unhealthy: {str(e)}" if settings.DEBUG else "unhealthy"
        logger.error(f"Health check failed - Database: {e}")

    status_code = 200 if health_status["status"] == "healthy" else 503

    return JSONResponse(content=health_status, status_code=status_code)


@app.get(f"{settings.API_PREFIX}/")
async def api_root():
    """
    API root endpoint.
    """
    return {
        "message": f"Welcome to {settings.APP_NAME} API",
        "version": "1.0.0",
        "docs": f"{settings.API_PREFIX}/docs"
    }


# ============================================================================
# Router Registration
# ============================================================================

# Import routers
from app.tenants.router import router as tenants_router
from app.auth.router import router as auth_router
from app.users.router import router as users_router
from app.onboarding.router import router as onboarding_router
from app.content.router import router as content_router
from app.analytics.router import router as analytics_router
from app.notifications.router import router as notifications_router

# Register routers
app.include_router(tenants_router, prefix=settings.API_PREFIX)
app.include_router(auth_router, prefix=settings.API_PREFIX)
app.include_router(users_router, prefix=settings.API_PREFIX)
app.include_router(onboarding_router, prefix=settings.API_PREFIX)
app.include_router(content_router, prefix=settings.API_PREFIX)
app.include_router(analytics_router, prefix=settings.API_PREFIX)
app.include_router(notifications_router, prefix=settings.API_PREFIX)


# ============================================================================
# Development Mode
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    logger.info("Starting development server...")

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info"
    )
