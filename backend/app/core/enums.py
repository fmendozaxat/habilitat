"""
Global enums for the Habilitat application.
Defines common enumeration types used across multiple modules.
"""

from enum import Enum


class UserRole(str, Enum):
    """
    User roles in the system.

    Attributes:
        SUPER_ADMIN: Platform administrator with full access
        TENANT_ADMIN: Tenant administrator with full access to their organization
        EMPLOYEE: Regular employee with limited access
    """

    SUPER_ADMIN = "super_admin"
    TENANT_ADMIN = "tenant_admin"
    EMPLOYEE = "employee"


class OnboardingStatus(str, Enum):
    """
    Status of an onboarding process.

    Attributes:
        NOT_STARTED: Onboarding has been assigned but not started
        IN_PROGRESS: Employee is currently working on onboarding
        COMPLETED: Onboarding has been completed
        EXPIRED: Onboarding has expired without completion
    """

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    EXPIRED = "expired"


class ContentType(str, Enum):
    """
    Types of content that can be used in onboarding modules.

    Attributes:
        TEXT: Plain text or rich text content
        IMAGE: Image files (JPEG, PNG, GIF, WebP)
        VIDEO: Video files (MP4, WebM)
        PDF: PDF documents
        LINK: External links/URLs
    """

    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    PDF = "pdf"
    LINK = "link"


class NotificationType(str, Enum):
    """
    Types of notifications that can be sent.

    Attributes:
        EMAIL: Email notification
        IN_APP: In-application notification
        PUSH: Push notification (mobile/web)
    """

    EMAIL = "email"
    IN_APP = "in_app"
    PUSH = "push"


class TenantStatus(str, Enum):
    """
    Status of a tenant/organization.

    Attributes:
        ACTIVE: Tenant is active and can use the platform
        INACTIVE: Tenant is temporarily inactive
        SUSPENDED: Tenant has been suspended (e.g., non-payment)
        TRIAL: Tenant is in trial period
    """

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    TRIAL = "trial"


class TaskStatus(str, Enum):
    """
    Status of an onboarding task.

    Attributes:
        PENDING: Task is pending completion
        IN_PROGRESS: Task is being worked on
        COMPLETED: Task has been completed
        SKIPPED: Task was skipped
    """

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"


class FileCategory(str, Enum):
    """
    Categories for uploaded files.

    Attributes:
        LOGO: Company/tenant logos
        AVATAR: User profile pictures
        CONTENT: Content files for onboarding modules
        DOCUMENT: General documents
        BACKGROUND: Background images for branding
    """

    LOGO = "logo"
    AVATAR = "avatar"
    CONTENT = "content"
    DOCUMENT = "document"
    BACKGROUND = "background"
