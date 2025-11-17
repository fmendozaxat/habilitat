"""
Custom middleware for the Habilitat application.
Includes tenant resolution, logging, and request processing.
"""

import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from app.core.config import settings


# Configure logger
logger = logging.getLogger(__name__)


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Middleware to resolve and inject tenant information into requests.

    Tenant resolution priority:
    1. Subdomain (e.g., acme.habilitat.com -> tenant identifier: "acme")
    2. X-Tenant-ID header
    3. Query parameter ?tenant=xxx (development only)

    The resolved tenant identifier is stored in request.state.tenant_identifier
    for use in dependencies and route handlers.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process request and resolve tenant.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain

        Returns:
            HTTP response
        """
        tenant_identifier = None

        # 1. Try to resolve from subdomain
        host = request.headers.get("host", "")
        if host:
            tenant_identifier = self._extract_subdomain(host)

        # 2. Try to resolve from X-Tenant-ID header
        if not tenant_identifier:
            tenant_identifier = request.headers.get("X-Tenant-ID")

        # 3. Try to resolve from query parameter (development only)
        if not tenant_identifier and settings.APP_ENV == "development":
            tenant_identifier = request.query_params.get("tenant")

        # Store tenant identifier in request state
        request.state.tenant_identifier = tenant_identifier

        # Continue processing request
        response = await call_next(request)

        return response

    def _extract_subdomain(self, host: str) -> str | None:
        """
        Extract subdomain from host header.

        Args:
            host: Host header value (e.g., "acme.habilitat.com:8000")

        Returns:
            Subdomain if found, None otherwise

        Examples:
            >>> _extract_subdomain("acme.habilitat.com")
            "acme"
            >>> _extract_subdomain("localhost:8000")
            None
        """
        # Remove port if present
        host = host.split(':')[0]

        # Split by dots
        parts = host.split('.')

        # Need at least 3 parts for subdomain (subdomain.domain.tld)
        # Example: acme.habilitat.com -> ['acme', 'habilitat', 'com']
        if len(parts) >= 3:
            # Return first part as subdomain
            return parts[0]

        # No subdomain found (e.g., localhost, habilitat.com)
        return None


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log HTTP requests and responses.
    Includes timing information and basic request details.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Log request and response with timing.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain

        Returns:
            HTTP response
        """
        # Start timer
        start_time = time.time()

        # Extract request info
        method = request.method
        path = request.url.path
        client_host = request.client.host if request.client else "unknown"

        # Get tenant if available
        tenant = getattr(request.state, 'tenant_identifier', None)
        tenant_info = f" [Tenant: {tenant}]" if tenant else ""

        # Log request
        logger.info(f"{method} {path} - Client: {client_host}{tenant_info}")

        # Process request
        try:
            response = await call_next(request)

            # Calculate processing time
            process_time = time.time() - start_time

            # Add processing time header
            response.headers["X-Process-Time"] = str(process_time)

            # Log response
            logger.info(
                f"{method} {path} - Status: {response.status_code} - "
                f"Time: {process_time:.3f}s{tenant_info}"
            )

            return response

        except Exception as e:
            # Calculate processing time even for errors
            process_time = time.time() - start_time

            # Log error
            logger.error(
                f"{method} {path} - Error: {str(e)} - "
                f"Time: {process_time:.3f}s{tenant_info}",
                exc_info=True
            )

            # Re-raise exception to be handled by FastAPI
            raise


class CORSCustomMiddleware(BaseHTTPMiddleware):
    """
    Custom CORS middleware with additional logging.
    Note: FastAPI's CORSMiddleware should be used in production.
    This is provided as an example of custom CORS handling.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Handle CORS for the request.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain

        Returns:
            HTTP response with CORS headers
        """
        # Handle preflight requests
        if request.method == "OPTIONS":
            response = Response()
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, PATCH, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Tenant-ID"
            response.headers["Access-Control-Max-Age"] = "3600"
            return response

        # Process normal request
        response = await call_next(request)

        # Add CORS headers to response
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Credentials"] = "true"

        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses.
    Helps protect against common web vulnerabilities.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Add security headers to response.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain

        Returns:
            HTTP response with security headers
        """
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # Content Security Policy (adjust as needed)
        if settings.APP_ENV == "production":
            response.headers["Content-Security-Policy"] = "default-src 'self'"

        return response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add a unique request ID to each request.
    Useful for tracking and debugging.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Add request ID to request and response.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain

        Returns:
            HTTP response with X-Request-ID header
        """
        import uuid

        # Generate unique request ID
        request_id = str(uuid.uuid4())

        # Store in request state
        request.state.request_id = request_id

        # Process request
        response = await call_next(request)

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        return response
