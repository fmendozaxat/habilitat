"""
Common utility functions used across the application.
Provides helpers for string manipulation, validation, formatting, and more.
"""

import re
import secrets
import unicodedata
from datetime import datetime
from typing import Any, Dict


def slugify(text: str, max_length: int = 100) -> str:
    """
    Convert text to URL-friendly slug.

    Args:
        text: Text to convert to slug
        max_length: Maximum length of the slug

    Returns:
        URL-friendly slug string

    Example:
        >>> slugify("Hello World!")
        "hello-world"
        >>> slugify("Привет Мир")
        "privet-mir"
    """
    # Normalize unicode characters
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ascii', 'ignore').decode('ascii')

    # Convert to lowercase
    text = text.lower()

    # Replace spaces and special characters with hyphens
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)

    # Remove leading/trailing hyphens
    text = re.sub(r'^-+|-+$', '', text)

    # Truncate to max length
    if len(text) > max_length:
        text = text[:max_length].rstrip('-')

    return text


def is_valid_email(email: str) -> bool:
    """
    Validate email format.

    Args:
        email: Email address to validate

    Returns:
        True if email is valid, False otherwise

    Example:
        >>> is_valid_email("user@example.com")
        True
        >>> is_valid_email("invalid.email")
        False
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def is_valid_subdomain(subdomain: str) -> bool:
    """
    Validate subdomain format.

    Rules:
    - Must be 3-63 characters long
    - Can only contain lowercase letters, numbers, and hyphens
    - Cannot start or end with a hyphen
    - Cannot be a reserved subdomain

    Args:
        subdomain: Subdomain to validate

    Returns:
        True if subdomain is valid, False otherwise

    Example:
        >>> is_valid_subdomain("my-company")
        True
        >>> is_valid_subdomain("www")
        False  # Reserved
    """
    from app.core.constants import SUBDOMAIN_PATTERN, RESERVED_SUBDOMAINS

    # Check if subdomain matches pattern
    if not re.match(SUBDOMAIN_PATTERN, subdomain):
        return False

    # Check if subdomain is not reserved
    if subdomain.lower() in RESERVED_SUBDOMAINS:
        return False

    return True


def generate_random_string(length: int = 32) -> str:
    """
    Generate a cryptographically secure random string.

    Args:
        length: Length of the random string (default: 32)

    Returns:
        URL-safe random string

    Example:
        >>> token = generate_random_string(64)
    """
    return secrets.token_urlsafe(length)


def generate_random_hex(length: int = 16) -> str:
    """
    Generate a random hexadecimal string.

    Args:
        length: Number of bytes (result will be 2x this length)

    Returns:
        Random hexadecimal string

    Example:
        >>> code = generate_random_hex(8)
    """
    return secrets.token_hex(length)


def format_datetime(
    dt: datetime,
    format_str: str = "%Y-%m-%d %H:%M:%S"
) -> str:
    """
    Format datetime to string.

    Args:
        dt: Datetime object to format
        format_str: Format string (default: "YYYY-MM-DD HH:MM:SS")

    Returns:
        Formatted datetime string

    Example:
        >>> format_datetime(datetime.now())
        "2024-01-15 14:30:00"
    """
    return dt.strftime(format_str)


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe storage.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename

    Example:
        >>> sanitize_filename("../../../etc/passwd")
        "etc_passwd"
        >>> sanitize_filename("my document (1).pdf")
        "my_document_1.pdf"
    """
    # Remove path separators
    filename = filename.replace('/', '_').replace('\\', '_')

    # Remove dangerous characters but keep dots for extensions
    filename = re.sub(r'[^\w\s.-]', '', filename)

    # Replace multiple spaces/underscores with single underscore
    filename = re.sub(r'[\s_]+', '_', filename)

    # Remove leading/trailing dots and underscores
    filename = filename.strip('._')

    return filename


def calculate_pagination(
    total: int,
    page: int,
    page_size: int
) -> Dict[str, Any]:
    """
    Calculate pagination metadata.

    Args:
        total: Total number of items
        page: Current page number (1-indexed)
        page_size: Items per page

    Returns:
        Dictionary with pagination metadata

    Example:
        >>> calculate_pagination(100, 1, 20)
        {
            'total': 100,
            'page': 1,
            'page_size': 20,
            'total_pages': 5,
            'has_next': True,
            'has_prev': False
        }
    """
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1
    }


def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate a string to a maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length (including suffix)
        suffix: Suffix to add when truncating (default: "...")

    Returns:
        Truncated string

    Example:
        >>> truncate_string("This is a long text", 10)
        "This is..."
    """
    if len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix


def parse_bool(value: Any) -> bool:
    """
    Parse a value to boolean.

    Args:
        value: Value to parse (str, int, bool, etc.)

    Returns:
        Boolean value

    Example:
        >>> parse_bool("true")
        True
        >>> parse_bool("0")
        False
        >>> parse_bool(1)
        True
    """
    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        return value.lower() in ('true', 'yes', '1', 't', 'y')

    if isinstance(value, int):
        return value != 0

    return bool(value)


def get_file_extension(filename: str) -> str:
    """
    Get file extension from filename.

    Args:
        filename: Filename with or without extension

    Returns:
        File extension (lowercase, without dot)

    Example:
        >>> get_file_extension("document.PDF")
        "pdf"
        >>> get_file_extension("image")
        ""
    """
    if '.' not in filename:
        return ""

    return filename.rsplit('.', 1)[1].lower()


def generate_unique_filename(original_filename: str) -> str:
    """
    Generate a unique filename while preserving extension.

    Args:
        original_filename: Original filename

    Returns:
        Unique filename with timestamp and random string

    Example:
        >>> generate_unique_filename("photo.jpg")
        "20240115_143000_AbCdEf123456_photo.jpg"
    """
    # Get extension
    extension = get_file_extension(original_filename)

    # Get base name without extension
    base_name = original_filename
    if extension:
        base_name = original_filename[:-len(extension)-1]

    # Sanitize base name
    base_name = sanitize_filename(base_name)

    # Generate timestamp
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    # Generate random string
    random_str = secrets.token_urlsafe(8)

    # Combine parts
    if extension:
        return f"{timestamp}_{random_str}_{base_name}.{extension}"
    else:
        return f"{timestamp}_{random_str}_{base_name}"


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password strength.

    Requirements:
    - At least 8 characters
    - Contains at least one uppercase letter
    - Contains at least one lowercase letter
    - Contains at least one digit

    Args:
        password: Password to validate

    Returns:
        Tuple of (is_valid, error_message)

    Example:
        >>> validate_password_strength("Pass123")
        (False, "La contraseña debe tener al menos 8 caracteres")
        >>> validate_password_strength("Password123")
        (True, "")
    """
    from app.core.constants import MIN_PASSWORD_LENGTH, MAX_PASSWORD_LENGTH

    if len(password) < MIN_PASSWORD_LENGTH:
        return False, f"La contraseña debe tener al menos {MIN_PASSWORD_LENGTH} caracteres"

    if len(password) > MAX_PASSWORD_LENGTH:
        return False, f"La contraseña no puede tener más de {MAX_PASSWORD_LENGTH} caracteres"

    if not re.search(r'[A-Z]', password):
        return False, "La contraseña debe contener al menos una letra mayúscula"

    if not re.search(r'[a-z]', password):
        return False, "La contraseña debe contener al menos una letra minúscula"

    if not re.search(r'\d', password):
        return False, "La contraseña debe contener al menos un número"

    return True, ""
