"""
Analytics module initialization.
Exports commonly used components for easy imports.
"""

from app.analytics.service import AnalyticsService
from app.analytics.router import router

__all__ = [
    # Service
    "AnalyticsService",
    # Router
    "router",
]
