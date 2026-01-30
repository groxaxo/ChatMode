"""
ChatMode API Routes Package.

This module exports all API routers for the Agent Manager system.
"""

from .agents import router as agents_router
from .auth_routes import router as auth_router
from .audio import router as audio_router
from .conversations import router as conversations_router
from .users import router as users_router
from .audit_routes import router as audit_router

# List of all routers for easy registration
all_routers = [
    auth_router,
    agents_router,
    audio_router,
    conversations_router,
    users_router,
    audit_router
]

__all__ = [
    "agents_router",
    "auth_router", 
    "audio_router",
    "conversations_router",
    "users_router",
    "audit_router",
    "all_routers"
]
