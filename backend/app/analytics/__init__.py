"""
Analytics module initialization.
Exports service, schemas, and router.
"""

from app.analytics.service import AnalyticsService
from app.analytics.router import router

__all__ = [
    "AnalyticsService",
    "router",
]
