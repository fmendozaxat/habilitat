"""
Notifications module initialization.
Exports services, schemas, and router.
"""

from app.notifications.email_service import EmailService
from app.notifications.service import NotificationService
from app.notifications.router import router

__all__ = [
    "EmailService",
    "NotificationService",
    "router",
]
