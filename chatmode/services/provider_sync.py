"""
Provider Sync Service for automatic model discovery.

This module provides functionality to sync models from various LLM providers
including Ollama, OpenAI, DeepSeek, Fireworks AI, xAI, and any OpenAI-compatible API.
"""

import os
import json
import asyncio
from typing import List, Dict, Optional, Any
from datetime import datetime
import aiohttp
from sqlalchemy.orm import Session

from ..models import Provider, ProviderModel


# Provider type detection from URL patterns
PROVIDER_PATTERNS = {
    "openai": ["api.openai.com"],
    "fireworks": ["api.fireworks.ai"],
    "deepseek": ["api.deepseek.com"],
    "xai": ["api.x.ai"],
    "anthropic": ["api.anthropic.com"],
    "alibaba": ["dashscope"],
    "ollama": ["localhost:11434"],
    "lmstudio": ["localhost:1234"],
    "vllm": ["localhost:8000"],
}

# Default display names for providers
PROVIDER_DISPLAY_NAMES = {
    "openai": "OpenAI",
    "fireworks": "Fireworks AI",
    "deepseek": "DeepSeek",
    "xai": "xAI (Grok)",
    "anthropic": "Anthropic",
    "alibaba": "Alibaba DashScope",
    "ollama": "Ollama",
    "lmstudio": "LM Studio",
    "vllm": "vLLM",
    "local": "Local Provider",
}


def detect_provider_type(base_url: str) -> str:
    """
    Auto-detect provider type from URL patterns.

    Args:
        base_url: The provider's base API URL

    Returns:
        Provider type string
    """
    base_url_lower = base_url.lower()

    for provider_type, patterns in PROVIDER_PATTERNS.items():
        for pattern in patterns:
            if pattern in base_url_lower:
                return provider_type

    # Default to openai-compatible for unknown providers
    return "openai"


def get_provider_display_name(provider_type: str, base_url: str) -> str:
    """Get display name for a provider type."""
    if provider_type in PROVIDER_DISPLAY_NAMES:
        return PROVIDER_DISPLAY_NAMES[provider_type]

    # Generate from URL for unknown providers
    from urllib.parse import urlparse

    hostname = urlparse(base_url).hostname or "Unknown"
    return f"Provider ({hostname})"


async def fetch_models_from_provider(
    base_url: str,
    api_key: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None,
) -> List[Dict[str, Any]]:
    """
    Fetch available models from an OpenAI-compatible /models endpoint.

    Args:
        base_url: Provider's base URL
        api_key: Optional API key for authentication
        headers: Optional additional headers

    Returns:
        List of model dictionaries with id, name, and capabilities
    """
    # Ensure base_url ends with /v1 for the models endpoint
    base_url = base_url.rstrip("/")
    if not base_url.endswith("/v1"):
        if "/v1" not in base_url:
            base_url = f"{base_url}/v1"

    models_url = f"{base_url}/models"

    request_headers = headers or {}
    if api_key:
        request_headers["Authorization"] = f"Bearer {api_key}"

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(
                models_url, headers=request_headers, timeout=30
            ) as response:
                if response.status == 404:
                    # Try without /v1 for Ollama native API
                    if "ollama" in base_url.lower() or "11434" in base_url:
                        return await _fetch_ollama_models(
                            base_url.replace("/v1", ""), api_key, headers
                        )
                    raise ValueError(f"Models endpoint not found at {models_url}")

                response.raise_for_status()
                data = await response.json()

                # Parse OpenAI-compatible response format
                models = []
                for model_data in data.get("data", []):
                    model_id = model_data.get("id")
                    if model_id:
                        model_info = {
                            "id": model_id,
                            "name": model_data.get("name", model_id),
                            "supports_tools": _detect_tool_support(model_id),
                            "supports_vision": _detect_vision_support(model_id),
                            "context_window": model_data.get("context_window"),
                            "metadata": model_data,
                        }
                        models.append(model_info)

                return models

        except aiohttp.ClientError as e:
            raise ValueError(f"Failed to connect to provider: {str(e)}")
        except asyncio.TimeoutError:
            raise ValueError("Connection timeout - provider may be unreachable")


async def _fetch_ollama_models(
    base_url: str,
    api_key: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None,
) -> List[Dict[str, Any]]:
    """
    Fetch models from Ollama's native API.

    Args:
        base_url: Ollama base URL (without /v1)
        api_key: Optional API key
        headers: Optional additional headers

    Returns:
        List of model dictionaries
    """
    base_url = base_url.rstrip("/")
    tags_url = f"{base_url}/api/tags"

    request_headers = headers or {}
    if api_key:
        request_headers["Authorization"] = f"Bearer {api_key}"

    async with aiohttp.ClientSession() as session:
        async with session.get(
            tags_url, headers=request_headers, timeout=30
        ) as response:
            response.raise_for_status()
            data = await response.json()

            models = []
            for model_data in data.get("models", []):
                model_id = model_data.get("name") or model_data.get("model")
                if model_id:
                    model_info = {
                        "id": model_id,
                        "name": model_id,
                        "supports_tools": _detect_tool_support(model_id),
                        "supports_vision": _detect_vision_support(model_id),
                        "context_window": None,
                        "metadata": model_data,
                    }
                    models.append(model_info)

            return models


def _detect_tool_support(model_id: str) -> bool:
    """
    Detect if a model supports tool calling based on its ID.

    Args:
        model_id: The model identifier

    Returns:
        True if model likely supports tools
    """
    model_id_lower = model_id.lower()

    # Models that typically don't support tools
    non_tool_patterns = [
        "embedding",
        "embed",
        "rerank",
        "reranker",
        "whisper",
        "tts",
        "stt",
        "dall-e",
    ]

    for pattern in non_tool_patterns:
        if pattern in model_id_lower:
            return False

    # Models that typically support tools
    tool_patterns = [
        "gpt-4",
        "gpt-3.5",
        "claude",
        "llama3",
        "llama-3",
        "qwen",
        "mixtral",
        "command",
        "deepseek",
    ]

    for pattern in tool_patterns:
        if pattern in model_id_lower:
            return True

    # Default to True for unknown models (most modern models support tools)
    return True


def _detect_vision_support(model_id: str) -> bool:
    """
    Detect if a model supports vision based on its ID.

    Args:
        model_id: The model identifier

    Returns:
        True if model likely supports vision
    """
    model_id_lower = model_id.lower()

    vision_patterns = [
        "vision",
        "vl",
        " multimodal",
        "gpt-4o",
        "claude-3",
        "llava",
        "bakllava",
        "moondream",
    ]

    for pattern in vision_patterns:
        if pattern in model_id_lower:
            return True

    return False


async def sync_provider_models(
    db: Session, provider: Provider, api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Sync models from a provider and update the database.

    Args:
        db: Database session
        provider: Provider instance to sync
        api_key: Optional API key (if not stored in provider)

    Returns:
        Dictionary with sync results
    """
    provider.sync_status = "syncing"
    provider.sync_error = None
    db.commit()

    try:
        # Fetch models from provider
        models = await fetch_models_from_provider(
            provider.base_url,
            api_key=api_key or provider.api_key_encrypted,
            headers=provider.headers,
        )

        # Get existing model IDs for this provider
        existing_models = {
            m.model_id: m
            for m in db.query(ProviderModel)
            .filter(ProviderModel.provider_id == provider.id)
            .all()
        }

        # Track changes
        added_count = 0
        updated_count = 0
        removed_count = 0

        # Update or create models
        current_model_ids = set()
        for model_data in models:
            model_id = model_data["id"]
            current_model_ids.add(model_id)

            if model_id in existing_models:
                # Update existing model
                existing_model = existing_models[model_id]
                existing_model.display_name = model_data.get("name", model_id)
                existing_model.supports_tools = model_data.get("supports_tools", True)
                existing_model.supports_vision = model_data.get(
                    "supports_vision", False
                )
                existing_model.context_window = model_data.get("context_window")
                existing_model.model_metadata = model_data.get("metadata", {})
                existing_model.updated_at = datetime.utcnow()
                updated_count += 1
            else:
                # Create new model
                new_model = ProviderModel(
                    provider_id=provider.id,
                    model_id=model_id,
                    display_name=model_data.get("name", model_id),
                    supports_tools=model_data.get("supports_tools", True),
                    supports_vision=model_data.get("supports_vision", False),
                    context_window=model_data.get("context_window"),
                    model_metadata=model_data.get("metadata", {}),
                )
                db.add(new_model)
                added_count += 1

        # Remove models that no longer exist
        for model_id, model in existing_models.items():
            if model_id not in current_model_ids:
                db.delete(model)
                removed_count += 1

        # Update provider sync status
        provider.last_sync_at = datetime.utcnow()
        provider.sync_status = "success"
        provider.sync_error = None
        db.commit()

        return {
            "success": True,
            "provider_id": provider.id,
            "provider_name": provider.name,
            "added": added_count,
            "updated": updated_count,
            "removed": removed_count,
            "total_models": len(models),
        }

    except Exception as e:
        provider.sync_status = "error"
        provider.sync_error = str(e)
        provider.last_sync_at = datetime.utcnow()
        db.commit()

        return {
            "success": False,
            "provider_id": provider.id,
            "provider_name": provider.name,
            "error": str(e),
        }


async def sync_all_providers(db: Session) -> List[Dict[str, Any]]:
    """
    Sync models from all enabled providers.

    Args:
        db: Database session

    Returns:
        List of sync results for each provider
    """
    providers = (
        db.query(Provider)
        .filter(Provider.enabled == True, Provider.auto_sync_enabled == True)
        .all()
    )

    results = []
    for provider in providers:
        result = await sync_provider_models(db, provider)
        results.append(result)

    return results


def create_provider_from_config(
    db: Session,
    name: str,
    base_url: str,
    api_key: Optional[str] = None,
    provider_type: Optional[str] = None,
    auto_sync: bool = True,
) -> Provider:
    """
    Create a new provider from configuration.

    Args:
        db: Database session
        name: Unique provider name
        base_url: Provider API base URL
        api_key: Optional API key
        provider_type: Optional explicit provider type (auto-detected if not provided)
        auto_sync: Whether to enable auto-sync

    Returns:
        Created Provider instance
    """
    # Auto-detect provider type if not specified
    if not provider_type:
        provider_type = detect_provider_type(base_url)

    display_name = get_provider_display_name(provider_type, base_url)

    provider = Provider(
        name=name,
        display_name=display_name,
        provider_type=provider_type,
        base_url=base_url,
        api_key_encrypted=api_key,
        auto_sync_enabled=auto_sync,
        sync_status="pending",
    )

    db.add(provider)
    db.commit()
    db.refresh(provider)

    return provider


def get_provider_models(db: Session, provider_id: str) -> List[ProviderModel]:
    """
    Get all enabled models for a provider.

    Args:
        db: Database session
        provider_id: Provider ID

    Returns:
        List of ProviderModel instances
    """
    return (
        db.query(ProviderModel)
        .filter(ProviderModel.provider_id == provider_id, ProviderModel.enabled == True)
        .all()
    )


def get_all_available_models(db: Session) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get all available models grouped by provider.

    Args:
        db: Database session

    Returns:
        Dictionary mapping provider names to their models
    """
    providers = db.query(Provider).filter(Provider.enabled == True).all()

    result = {}
    for provider in providers:
        models = (
            db.query(ProviderModel)
            .filter(
                ProviderModel.provider_id == provider.id, ProviderModel.enabled == True
            )
            .all()
        )

        result[provider.name] = [
            {
                "id": m.model_id,
                "name": m.display_name or m.model_id,
                "supports_tools": m.supports_tools,
                "supports_vision": m.supports_vision,
                "context_window": m.context_window,
            }
            for m in models
        ]

    return result
