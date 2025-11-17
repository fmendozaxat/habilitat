"""
Utility functions for tenant module.
Includes subdomain validation and tenant-specific helpers.
"""

import re
from app.core.constants import RESERVED_SUBDOMAINS


def is_valid_subdomain_format(subdomain: str) -> bool:
    """
    Validate subdomain format.

    Rules:
    - Only lowercase letters, numbers, and hyphens
    - Minimum 3 characters
    - Cannot start or end with a hyphen

    Args:
        subdomain: Subdomain string to validate

    Returns:
        True if valid, False otherwise

    Example:
        >>> is_valid_subdomain_format("my-company")
        True
        >>> is_valid_subdomain_format("-invalid")
        False
    """
    if not subdomain or len(subdomain) < 3:
        return False

    # Pattern: must start and end with alphanumeric, can have hyphens in middle
    pattern = r'^[a-z0-9]([a-z0-9-]*[a-z0-9])?$'

    return bool(re.match(pattern, subdomain))


def get_reserved_subdomains() -> list[str]:
    """
    Get list of reserved subdomains that cannot be used by tenants.

    Returns:
        List of reserved subdomain strings

    Example:
        >>> "www" in get_reserved_subdomains()
        True
    """
    return RESERVED_SUBDOMAINS


def is_subdomain_reserved(subdomain: str) -> bool:
    """
    Check if a subdomain is reserved.

    Args:
        subdomain: Subdomain to check

    Returns:
        True if reserved, False otherwise

    Example:
        >>> is_subdomain_reserved("www")
        True
        >>> is_subdomain_reserved("my-company")
        False
    """
    return subdomain.lower() in [s.lower() for s in get_reserved_subdomains()]


def validate_subdomain_availability(subdomain: str) -> tuple[bool, str]:
    """
    Validate that a subdomain is available for use.

    Checks:
    1. Format is valid
    2. Not in reserved list

    Args:
        subdomain: Subdomain to validate

    Returns:
        Tuple of (is_valid, error_message)
        - (True, "") if valid and available
        - (False, "error message") if invalid or unavailable

    Example:
        >>> validate_subdomain_availability("my-company")
        (True, "")
        >>> validate_subdomain_availability("www")
        (False, "Este subdomain está reservado")
    """
    if not is_valid_subdomain_format(subdomain):
        return (
            False,
            "Formato de subdomain inválido. Solo letras minúsculas, números y guiones, mínimo 3 caracteres."
        )

    if is_subdomain_reserved(subdomain):
        return False, "Este subdomain está reservado"

    return True, ""


def sanitize_subdomain(subdomain: str) -> str:
    """
    Sanitize subdomain by removing invalid characters and converting to lowercase.

    Args:
        subdomain: Subdomain to sanitize

    Returns:
        Sanitized subdomain string

    Example:
        >>> sanitize_subdomain("My-Company!")
        "my-company"
    """
    # Convert to lowercase
    subdomain = subdomain.lower()

    # Remove all characters except letters, numbers, and hyphens
    subdomain = re.sub(r'[^a-z0-9-]', '', subdomain)

    # Remove leading/trailing hyphens
    subdomain = subdomain.strip('-')

    # Replace multiple consecutive hyphens with single hyphen
    subdomain = re.sub(r'-+', '-', subdomain)

    return subdomain


def generate_subdomain_from_name(name: str) -> str:
    """
    Generate a subdomain from organization name.

    Args:
        name: Organization name

    Returns:
        Generated subdomain

    Example:
        >>> generate_subdomain_from_name("My Great Company")
        "my-great-company"
    """
    # Convert to lowercase and replace spaces with hyphens
    subdomain = name.lower().replace(' ', '-')

    # Sanitize
    subdomain = sanitize_subdomain(subdomain)

    # Ensure minimum length
    if len(subdomain) < 3:
        subdomain += "-org"

    return subdomain


def get_tenant_domain(subdomain: str, base_domain: str = "habilitat.com") -> str:
    """
    Get full tenant domain from subdomain.

    Args:
        subdomain: Tenant subdomain
        base_domain: Base domain (default: habilitat.com)

    Returns:
        Full domain string

    Example:
        >>> get_tenant_domain("acme")
        "acme.habilitat.com"
    """
    return f"{subdomain}.{base_domain}"


def parse_domain_to_subdomain(domain: str) -> str | None:
    """
    Extract subdomain from full domain.

    Args:
        domain: Full domain string (e.g., "acme.habilitat.com")

    Returns:
        Subdomain or None if not found

    Example:
        >>> parse_domain_to_subdomain("acme.habilitat.com")
        "acme"
        >>> parse_domain_to_subdomain("localhost")
        None
    """
    parts = domain.split('.')

    # Need at least 3 parts for subdomain (subdomain.domain.tld)
    if len(parts) >= 3:
        return parts[0]

    return None
