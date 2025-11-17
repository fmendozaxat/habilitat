"""
Global constants for the Habilitat application.
Defines constant values used across multiple modules.
"""

# ============================================================================
# User Roles
# ============================================================================

SUPER_ADMIN_ROLE = "super_admin"
TENANT_ADMIN_ROLE = "tenant_admin"
EMPLOYEE_ROLE = "employee"

# ============================================================================
# File Upload Limits
# ============================================================================

# Maximum file size in bytes (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024

# Maximum avatar size in bytes (2MB)
MAX_AVATAR_SIZE = 2 * 1024 * 1024

# Maximum logo size in bytes (5MB)
MAX_LOGO_SIZE = 5 * 1024 * 1024

# ============================================================================
# Allowed File Types
# ============================================================================

ALLOWED_IMAGE_TYPES = [
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/gif",
    "image/webp"
]

ALLOWED_VIDEO_TYPES = [
    "video/mp4",
    "video/webm",
    "video/quicktime"
]

ALLOWED_DOCUMENT_TYPES = [
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
]

ALLOWED_AVATAR_TYPES = [
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp"
]

# ============================================================================
# Tenant Branding Defaults
# ============================================================================

DEFAULT_TENANT_THEME = {
    "primary_color": "#3B82F6",      # Blue
    "secondary_color": "#10B981",    # Green
    "background_color": "#FFFFFF",   # White
    "text_color": "#1F2937",         # Dark gray
    "accent_color": "#8B5CF6",       # Purple
    "success_color": "#10B981",      # Green
    "warning_color": "#F59E0B",      # Orange
    "error_color": "#EF4444",        # Red
}

# ============================================================================
# Pagination Defaults
# ============================================================================

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
MIN_PAGE_SIZE = 1

# ============================================================================
# Password Requirements
# ============================================================================

MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128

# ============================================================================
# Token Expiration (in seconds)
# ============================================================================

EMAIL_VERIFICATION_TOKEN_EXPIRE = 24 * 60 * 60  # 24 hours
PASSWORD_RESET_TOKEN_EXPIRE = 1 * 60 * 60       # 1 hour
INVITATION_TOKEN_EXPIRE = 7 * 24 * 60 * 60      # 7 days

# ============================================================================
# Email Templates
# ============================================================================

EMAIL_TEMPLATE_WELCOME = "welcome"
EMAIL_TEMPLATE_VERIFICATION = "verification"
EMAIL_TEMPLATE_PASSWORD_RESET = "password_reset"
EMAIL_TEMPLATE_INVITATION = "invitation"
EMAIL_TEMPLATE_ONBOARDING_REMINDER = "onboarding_reminder"
EMAIL_TEMPLATE_ONBOARDING_COMPLETED = "onboarding_completed"

# ============================================================================
# Cache Keys Prefixes
# ============================================================================

CACHE_PREFIX_USER = "user:"
CACHE_PREFIX_TENANT = "tenant:"
CACHE_PREFIX_SESSION = "session:"

# ============================================================================
# Rate Limiting
# ============================================================================

RATE_LIMIT_LOGIN_ATTEMPTS = 5
RATE_LIMIT_LOGIN_WINDOW = 15 * 60  # 15 minutes in seconds

# ============================================================================
# Onboarding Defaults
# ============================================================================

DEFAULT_ONBOARDING_DURATION_DAYS = 30
MAX_ONBOARDING_STEPS = 50

# ============================================================================
# Storage Paths
# ============================================================================

STORAGE_PATH_AVATARS = "avatars"
STORAGE_PATH_LOGOS = "logos"
STORAGE_PATH_CONTENT = "content"
STORAGE_PATH_DOCUMENTS = "documents"
STORAGE_PATH_BACKGROUNDS = "backgrounds"

# ============================================================================
# Tenant Limits
# ============================================================================

# For free/trial plans
TENANT_LIMIT_USERS_FREE = 10
TENANT_LIMIT_ONBOARDING_FLOWS_FREE = 3
TENANT_LIMIT_STORAGE_MB_FREE = 100

# ============================================================================
# Validation Patterns
# ============================================================================

# Regex for subdomain validation (lowercase alphanumeric and hyphens, 3-63 chars)
SUBDOMAIN_PATTERN = r"^[a-z0-9][a-z0-9-]{1,61}[a-z0-9]$"

# Reserved subdomains that cannot be used by tenants
RESERVED_SUBDOMAINS = [
    "www",
    "api",
    "app",
    "admin",
    "dashboard",
    "mail",
    "ftp",
    "smtp",
    "pop",
    "imap",
    "test",
    "dev",
    "staging",
    "production",
    "demo",
    "support",
    "help",
    "docs",
    "blog",
    "status",
]
