"""
Tests for tenant utility functions.
"""

import pytest
from app.tenants.utils import (
    is_valid_subdomain_format,
    is_subdomain_reserved,
    validate_subdomain_availability,
    sanitize_subdomain,
    generate_subdomain_from_name,
    get_tenant_domain,
    parse_domain_to_subdomain
)


class TestSubdomainValidation:
    """Tests for subdomain validation functions."""

    def test_is_valid_subdomain_format_valid(self):
        """Test valid subdomain formats."""
        valid_subdomains = [
            "acme",
            "my-company",
            "test123",
            "company-name-2024"
        ]

        for subdomain in valid_subdomains:
            assert is_valid_subdomain_format(subdomain) is True

    def test_is_valid_subdomain_format_invalid(self):
        """Test invalid subdomain formats."""
        invalid_subdomains = [
            "ab",  # Too short
            "-company",  # Starts with hyphen
            "company-",  # Ends with hyphen
            "My-Company",  # Has uppercase
            "company_name",  # Has underscore
            "",  # Empty
            "a",  # Too short
        ]

        for subdomain in invalid_subdomains:
            assert is_valid_subdomain_format(subdomain) is False

    def test_is_subdomain_reserved(self):
        """Test reserved subdomain checking."""
        reserved = ["www", "api", "admin", "app", "mail"]

        for subdomain in reserved:
            assert is_subdomain_reserved(subdomain) is True

        assert is_subdomain_reserved("my-company") is False

    def test_validate_subdomain_availability_valid(self):
        """Test subdomain availability validation for valid subdomains."""
        is_valid, message = validate_subdomain_availability("my-company")

        assert is_valid is True
        assert message == ""

    def test_validate_subdomain_availability_invalid_format(self):
        """Test subdomain availability validation for invalid format."""
        is_valid, message = validate_subdomain_availability("-invalid")

        assert is_valid is False
        assert "formato" in message.lower() or "inválido" in message.lower()

    def test_validate_subdomain_availability_reserved(self):
        """Test subdomain availability validation for reserved subdomain."""
        is_valid, message = validate_subdomain_availability("www")

        assert is_valid is False
        assert "reservado" in message.lower()


class TestSubdomainSanitization:
    """Tests for subdomain sanitization functions."""

    def test_sanitize_subdomain(self):
        """Test subdomain sanitization."""
        assert sanitize_subdomain("My-Company!") == "my-company"
        assert sanitize_subdomain("Test@Company#123") == "testcompany123"
        assert sanitize_subdomain("--company--") == "company"
        assert sanitize_subdomain("multiple---hyphens") == "multiple-hyphens"

    def test_generate_subdomain_from_name(self):
        """Test generating subdomain from company name."""
        assert generate_subdomain_from_name("ACME Corporation") == "acme-corporation"
        assert generate_subdomain_from_name("My Great Company") == "my-great-company"
        assert generate_subdomain_from_name("Test!@# Company 123") == "test-company-123"

    def test_generate_subdomain_from_short_name(self):
        """Test generating subdomain from very short name."""
        result = generate_subdomain_from_name("AB")

        # Should add suffix to meet minimum length
        assert len(result) >= 3
        assert "ab" in result


class TestDomainOperations:
    """Tests for domain operation functions."""

    def test_get_tenant_domain(self):
        """Test getting full tenant domain."""
        assert get_tenant_domain("acme") == "acme.habilitat.com"
        assert get_tenant_domain("my-company") == "my-company.habilitat.com"

    def test_get_tenant_domain_custom_base(self):
        """Test getting tenant domain with custom base."""
        assert get_tenant_domain("acme", "example.com") == "acme.example.com"

    def test_parse_domain_to_subdomain(self):
        """Test parsing subdomain from full domain."""
        assert parse_domain_to_subdomain("acme.habilitat.com") == "acme"
        assert parse_domain_to_subdomain("my-company.example.com") == "my-company"

    def test_parse_domain_to_subdomain_no_subdomain(self):
        """Test parsing domain without subdomain."""
        assert parse_domain_to_subdomain("localhost") is None
        assert parse_domain_to_subdomain("example.com") is None
