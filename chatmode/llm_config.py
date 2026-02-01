"""
LLM Configuration Module for CrewAI Integration.

Provides utilities for creating CrewAI LLM instances from ChatMode settings
and agent profiles.
"""

import os
from typing import Optional, Dict, Any
from crewai import LLM

from .config import Settings


def create_llm_from_profile(profile: Dict[str, Any], settings: Settings) -> LLM:
    """
    Create a CrewAI LLM instance from an agent profile.

    Args:
        profile: Agent profile dictionary loaded from JSON
        settings: Global application settings

    Returns:
        Configured CrewAI LLM instance
    """
    api_type = profile.get("api", "openai").lower()
    model = profile.get("model") or settings.default_chat_model
    api_url = profile.get("url")
    api_key = profile.get("api_key")
    params = profile.get("params", {})

    if api_type == "ollama":
        # Ollama configuration - use ollama/ prefix for CrewAI
        base_url = api_url or settings.ollama_base_url
        # Ensure the model has ollama/ prefix for CrewAI
        if not model.startswith("ollama/"):
            model_name = f"ollama/{model}"
        else:
            model_name = model

        return LLM(
            model=model_name,
            base_url=base_url,
            temperature=params.get("temperature", settings.temperature),
        )
    else:
        # OpenAI-compatible configuration (OpenAI, Azure, Anthropic, etc.)
        base_url = api_url or settings.openai_base_url
        api_key = api_key or settings.openai_api_key

        return LLM(
            model=model,
            base_url=base_url if base_url != "https://api.openai.com/v1" else None,
            api_key=api_key,
            temperature=params.get("temperature", settings.temperature),
            max_tokens=params.get("max_tokens", settings.max_output_tokens),
        )


def create_embedder_config(settings: Settings) -> Dict[str, Any]:
    """
    Create embedder configuration for CrewAI memory.

    Args:
        settings: Global application settings

    Returns:
        Embedder configuration dictionary
    """
    provider = settings.embedding_provider.lower()

    if provider == "ollama":
        # OllamaProviderSpec expects url and model_name
        url = settings.embedding_base_url
        if not url.endswith("/api/embeddings"):
            url = f"{url.rstrip('/')}/api/embeddings"
        return {
            "provider": "ollama",
            "config": {
                "model_name": settings.embedding_model,
                "url": url,
            },
        }
    else:
        # OpenAIProviderSpec expects model_name and api_key (and optionally api_base)
        config = {
            "model_name": settings.embedding_model,
            "api_key": settings.embedding_api_key or settings.openai_api_key,
        }
        # Add api_base if it's not default OpenAI URL
        if (
            settings.embedding_base_url
            and settings.embedding_base_url != "https://api.openai.com/v1"
        ):
            config["api_base"] = settings.embedding_base_url
        return {"provider": "openai", "config": config}


def get_default_llm(settings: Settings) -> LLM:
    """
    Create a default LLM instance from global settings.

    Args:
        settings: Global application settings

    Returns:
        Default CrewAI LLM instance
    """
    return LLM(
        model=settings.default_chat_model,
        base_url=settings.openai_base_url
        if settings.openai_base_url != "https://api.openai.com/v1"
        else None,
        api_key=settings.openai_api_key,
        temperature=settings.temperature,
        max_tokens=settings.max_output_tokens,
    )
