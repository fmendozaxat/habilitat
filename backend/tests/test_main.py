"""
Tests for main application endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from main import app


client = TestClient(app)


class TestRootEndpoints:
    """Tests for root API endpoints."""

    def test_root_endpoint(self):
        """Test root endpoint returns success."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "status" in data
        assert data["status"] == "healthy"

    def test_health_check_endpoint(self):
        """Test health check endpoint."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data

    def test_api_root_endpoint(self):
        """Test API root endpoint."""
        response = client.get("/api/v1/")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "docs" in data


class TestMiddleware:
    """Tests for middleware functionality."""

    def test_request_id_header(self):
        """Test that X-Request-ID header is added."""
        response = client.get("/health")

        assert "X-Request-ID" in response.headers
        assert len(response.headers["X-Request-ID"]) > 0

    def test_process_time_header(self):
        """Test that X-Process-Time header is added."""
        response = client.get("/health")

        assert "X-Process-Time" in response.headers

    def test_security_headers(self):
        """Test that security headers are added."""
        response = client.get("/health")

        assert "X-Content-Type-Options" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"

        assert "X-Frame-Options" in response.headers
        assert response.headers["X-Frame-Options"] == "DENY"

    def test_cors_headers(self):
        """Test CORS headers are present."""
        response = client.get("/health")

        assert "Access-Control-Allow-Origin" in response.headers


class TestTenantMiddleware:
    """Tests for tenant resolution middleware."""

    def test_tenant_from_header(self):
        """Test tenant resolution from X-Tenant-ID header."""
        headers = {"X-Tenant-ID": "acme"}
        response = client.get("/health", headers=headers)

        assert response.status_code == 200

    def test_tenant_from_query_param(self):
        """Test tenant resolution from query parameter (dev mode)."""
        response = client.get("/health?tenant=acme")

        assert response.status_code == 200
