"""
Tests for core utility functions.
"""

import pytest
from app.core.utils import (
    slugify,
    is_valid_email,
    is_valid_subdomain,
    generate_random_string,
    generate_random_hex,
    sanitize_filename,
    calculate_pagination,
    truncate_string,
    parse_bool,
    get_file_extension,
    generate_unique_filename,
    validate_password_strength
)


class TestSlugify:
    """Tests for slugify function."""

    def test_basic_slugify(self):
        """Test basic slug creation."""
        assert slugify("Hello World") == "hello-world"

    def test_slugify_with_special_chars(self):
        """Test slug with special characters."""
        assert slugify("Hello, World!") == "hello-world"

    def test_slugify_with_accents(self):
        """Test slug with accented characters."""
        result = slugify("Café París")
        assert "caf" in result.lower()
        assert "par" in result.lower()

    def test_slugify_max_length(self):
        """Test slug truncation."""
        long_text = "a" * 200
        slug = slugify(long_text, max_length=50)
        assert len(slug) <= 50

    def test_slugify_multiple_spaces(self):
        """Test slug with multiple spaces."""
        assert slugify("Hello    World") == "hello-world"

    def test_slugify_leading_trailing_hyphens(self):
        """Test removal of leading/trailing hyphens."""
        assert slugify("-Hello World-") == "hello-world"


class TestEmailValidation:
    """Tests for email validation."""

    def test_valid_emails(self):
        """Test valid email addresses."""
        valid_emails = [
            "user@example.com",
            "john.doe@company.co.uk",
            "admin+test@domain.com",
            "user123@test-domain.com"
        ]
        for email in valid_emails:
            assert is_valid_email(email) is True

    def test_invalid_emails(self):
        """Test invalid email addresses."""
        invalid_emails = [
            "invalid.email",
            "@example.com",
            "user@",
            "user @example.com",
            "user@example",
            ""
        ]
        for email in invalid_emails:
            assert is_valid_email(email) is False


class TestSubdomainValidation:
    """Tests for subdomain validation."""

    def test_valid_subdomains(self):
        """Test valid subdomains."""
        valid_subdomains = [
            "acme",
            "my-company",
            "test123",
            "company-name-2024"
        ]
        for subdomain in valid_subdomains:
            assert is_valid_subdomain(subdomain) is True

    def test_invalid_subdomains(self):
        """Test invalid subdomains."""
        invalid_subdomains = [
            "ab",  # Too short
            "-company",  # Starts with hyphen
            "company-",  # Ends with hyphen
            "My-Company",  # Has uppercase
            "company_name",  # Has underscore
            "www",  # Reserved
            "api"  # Reserved
        ]
        for subdomain in invalid_subdomains:
            assert is_valid_subdomain(subdomain) is False


class TestRandomGeneration:
    """Tests for random string generation."""

    def test_generate_random_string(self):
        """Test random string generation."""
        random_str = generate_random_string(32)
        assert len(random_str) > 0
        assert isinstance(random_str, str)

    def test_generate_random_string_different(self):
        """Test that random strings are different."""
        str1 = generate_random_string()
        str2 = generate_random_string()
        assert str1 != str2

    def test_generate_random_hex(self):
        """Test random hex generation."""
        hex_str = generate_random_hex(16)
        assert len(hex_str) == 32  # 16 bytes = 32 hex chars
        assert isinstance(hex_str, str)


class TestFilenameUtils:
    """Tests for filename utilities."""

    def test_sanitize_filename(self):
        """Test filename sanitization."""
        assert sanitize_filename("my document.pdf") == "my_document.pdf"
        assert sanitize_filename("../../../etc/passwd") == "etc_passwd"
        assert sanitize_filename("file (1).txt") == "file_1.txt"

    def test_get_file_extension(self):
        """Test file extension extraction."""
        assert get_file_extension("document.PDF") == "pdf"
        assert get_file_extension("image.jpg") == "jpg"
        assert get_file_extension("no_extension") == ""
        assert get_file_extension("file.tar.gz") == "gz"

    def test_generate_unique_filename(self):
        """Test unique filename generation."""
        filename1 = generate_unique_filename("test.jpg")
        filename2 = generate_unique_filename("test.jpg")

        assert filename1 != filename2
        assert filename1.endswith("test.jpg")
        assert filename2.endswith("test.jpg")


class TestPagination:
    """Tests for pagination utilities."""

    def test_calculate_pagination(self):
        """Test pagination calculation."""
        result = calculate_pagination(total=100, page=1, page_size=20)

        assert result["total"] == 100
        assert result["page"] == 1
        assert result["page_size"] == 20
        assert result["total_pages"] == 5
        assert result["has_next"] is True
        assert result["has_prev"] is False

    def test_calculate_pagination_last_page(self):
        """Test pagination on last page."""
        result = calculate_pagination(total=100, page=5, page_size=20)

        assert result["has_next"] is False
        assert result["has_prev"] is True

    def test_calculate_pagination_empty(self):
        """Test pagination with no items."""
        result = calculate_pagination(total=0, page=1, page_size=20)

        assert result["total_pages"] == 0
        assert result["has_next"] is False
        assert result["has_prev"] is False


class TestStringUtils:
    """Tests for string utilities."""

    def test_truncate_string(self):
        """Test string truncation."""
        text = "This is a long text that needs to be truncated"
        truncated = truncate_string(text, 20)

        assert len(truncated) == 20
        assert truncated.endswith("...")

    def test_truncate_string_no_truncation(self):
        """Test string that doesn't need truncation."""
        text = "Short"
        truncated = truncate_string(text, 20)

        assert truncated == text

    def test_parse_bool(self):
        """Test boolean parsing."""
        assert parse_bool("true") is True
        assert parse_bool("yes") is True
        assert parse_bool("1") is True
        assert parse_bool("false") is False
        assert parse_bool("no") is False
        assert parse_bool("0") is False
        assert parse_bool(1) is True
        assert parse_bool(0) is False
        assert parse_bool(True) is True
        assert parse_bool(False) is False


class TestPasswordValidation:
    """Tests for password validation."""

    def test_valid_passwords(self):
        """Test valid passwords."""
        valid_passwords = [
            "Password123",
            "SecurePass1",
            "MyP@ssw0rd",
            "Abcd1234"
        ]
        for password in valid_passwords:
            is_valid, message = validate_password_strength(password)
            assert is_valid is True
            assert message == ""

    def test_invalid_passwords(self):
        """Test invalid passwords."""
        # Too short
        is_valid, message = validate_password_strength("Pass1")
        assert is_valid is False
        assert "8 caracteres" in message

        # No uppercase
        is_valid, message = validate_password_strength("password123")
        assert is_valid is False
        assert "mayúscula" in message

        # No lowercase
        is_valid, message = validate_password_strength("PASSWORD123")
        assert is_valid is False
        assert "minúscula" in message

        # No digit
        is_valid, message = validate_password_strength("PasswordABC")
        assert is_valid is False
        assert "número" in message
