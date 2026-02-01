"""
ChatMode API Routes Package.

This module exports all API routers for the Agent Manager system.
"""

from .advanced import router as advanced_router
from .agents import router as agents_router
from .audio import router as audio_router
from .audit_routes import router as audit_router
from .auth_routes import router as auth_router
from .conversations import router as conversations_router
from .env_config import router as env_config_router
from .filter import router as filter_router
from .providers import router as providers_router
from .users import router as users_router

# List of all routers for easy registration
all_routers = [
    auth_router,
    agents_router,
    providers_router,
    env_config_router,
    audio_router,
    conversations_router,
    users_router,
    audit_router,
    advanced_router,
    filter_router,
]

__all__ = [
    "agents_router",
    "auth_router",
    "audio_router",
    "conversations_router",
    "users_router",
    "audit_router",
    "advanced_router",
    "providers_router",
    "env_config_router",
    "filter_router",
    "all_routers",
]
