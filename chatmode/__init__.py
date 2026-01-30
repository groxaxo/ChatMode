"""
ChatMode - AI Multi-Agent Conversation Platform

A FastAPI-based platform for managing and orchestrating AI agent conversations
with support for multiple LLM providers, semantic memory, and voice synthesis.
"""

__version__ = "2.0.0"

# Import commonly used components for easier access
from .config import Settings, load_settings
from .database import init_db, get_db
from .models import User, Agent, Conversation

__all__ = [
    "Settings",
    "load_settings",
    "init_db",
    "get_db",
    "User",
    "Agent",
    "Conversation",
]
