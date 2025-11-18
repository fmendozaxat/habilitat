"""
Notifications module initialization.
Exports commonly used components for easy imports.
"""

from app.notifications.models import EmailLog
from app.notifications.service import NotificationService
from app.notifications.email_service import email_service
from app.notifications.router import router

__all__ = [
    # Models
    "EmailLog",
    # Services
    "NotificationService",
    "email_service",
    # Router
    "router",
]
