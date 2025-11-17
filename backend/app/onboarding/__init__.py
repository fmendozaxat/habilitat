"""
Onboarding module initialization.
Exports commonly used components for easy imports.
"""

from app.onboarding.models import (
    OnboardingFlow,
    OnboardingModule,
    OnboardingAssignment,
    ModuleProgress
)
from app.onboarding.service import OnboardingService
from app.onboarding.router import router

__all__ = [
    # Models
    "OnboardingFlow",
    "OnboardingModule",
    "OnboardingAssignment",
    "ModuleProgress",
    # Service
    "OnboardingService",
    # Router
    "router",
]
