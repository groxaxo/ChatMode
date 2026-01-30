import json
from dataclasses import dataclass
from typing import List, Dict, Optional
from functools import lru_cache

import requests
from openai import OpenAI
from sqlalchemy.orm import Session


class ChatProvider:
    def chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        options: Optional[Dict[str, object]] = None,
    ) -> str:
        raise NotImplementedError


class EmbeddingProvider:
    def embed(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError


# Provider registry for dynamic provider management
_provider_registry: Dict[str, Dict] = {}


def register_provider(name: str, config: Dict):
    """Register a provider configuration in the registry."""
    _provider_registry[name] = config


def get_provider_config(name: str) -> Optional[Dict]:
    """Get a provider configuration from the registry."""
    return _provider_registry.get(name)


def get_all_provider_configs() -> Dict[str, Dict]:
    """Get all registered provider configurations."""
    return _provider_registry.copy()


def load_providers_from_db(db: Session):
    """
    Load all enabled providers from database into the registry.

    Args:
        db: SQLAlchemy database session
    """
    from .models import Provider, ProviderModel

    providers = db.query(Provider).filter(Provider.enabled == True).all()

    for provider in providers:
        # Get enabled models for this provider
        models = (
            db.query(ProviderModel)
            .filter(
                ProviderModel.provider_id == provider.id, ProviderModel.enabled == True
            )
            .all()
        )

        config = {
            "id": provider.id,
            "name": provider.name,
            "display_name": provider.display_name,
            "provider_type": provider.provider_type,
            "base_url": provider.base_url,
            "api_key": provider.api_key_encrypted,
            "headers": provider.headers or {},
            "supports_tools": provider.supports_tools,
            "models": {
                m.model_id: {"name": m.display_name or m.model_id} for m in models
            },
            "default_model": next((m.model_id for m in models if m.is_default), None),
        }

        register_provider(provider.name, config)


@dataclass
class OpenAIChatProvider(ChatProvider):
    base_url: str
    api_key: str

    def __post_init__(self):
        self.client = OpenAI(base_url=self.base_url, api_key=self.api_key)

    def chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        options=None,
        tools: Optional[List[Dict]] = None,
        tool_choice: Optional[str] = None,
    ):
        """
        Generate a chat completion.

        Args:
            model: Model name
            messages: Conversation messages
            temperature: Sampling temperature
            max_tokens: Max tokens to generate
            options: Additional options (ignored for OpenAI)
            tools: Optional list of tool schemas for function calling
            tool_choice: How to use tools ("auto", "none", or specific tool)

        Returns:
            Dict with either 'content' or 'tool_calls' key, or the full message object
        """
        kwargs = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if tools:
            kwargs["tools"] = tools
            if tool_choice:
                kwargs["tool_choice"] = tool_choice

        response = self.client.chat.completions.create(**kwargs)

        # Return the full message object for caller to handle
        choice = response.choices[0] if response.choices else None
        if choice:
            return choice.message
        return None


@dataclass
class OpenAIEmbeddingProvider(EmbeddingProvider):
    base_url: str
    api_key: str
    model: str

    def __post_init__(self):
        self.client = OpenAI(base_url=self.base_url, api_key=self.api_key)

    def embed(self, texts: List[str]) -> List[List[float]]:
        response = self.client.embeddings.create(model=self.model, input=texts)
        return [item.embedding for item in response.data]


@dataclass
class OllamaChatProvider(ChatProvider):
    base_url: str

    def chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        options=None,
        tools: Optional[List[Dict]] = None,
        tool_choice: Optional[str] = None,
    ):
        """
        Generate a chat completion.

        Note: Ollama doesn't currently support tool calling, so tools/tool_choice are ignored.

        Returns:
            A simple object with .content attribute for compatibility
        """
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        if options:
            payload["options"].update(options)

        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
        data = response.json()
        content = data.get("message", {}).get("content", "")

        # Return a simple object with .content for compatibility with OpenAI format
        class SimpleMessage:
            def __init__(self, content):
                self.content = content
                self.tool_calls = None

        return SimpleMessage(content)


@dataclass
class OllamaEmbeddingProvider(EmbeddingProvider):
    base_url: str
    model: str

    def embed(self, texts: List[str]) -> List[List[float]]:
        # Try /api/embed first (Ollama v0.1.29+), fallback to /api/embeddings
        vectors: List[List[float]] = []
        for text in texts:
            embedding = self._embed_single(text)
            vectors.append(embedding)
        return vectors

    def _embed_single(self, text: str) -> List[float]:
        # Try new endpoint first
        try:
            url = f"{self.base_url}/api/embed"
            response = requests.post(
                url,
                json={"model": self.model, "input": text},
                timeout=120,
            )
            response.raise_for_status()
            data = response.json()
            # New API returns embeddings as array
            embeddings = data.get("embeddings", [[]])
            return embeddings[0] if embeddings else []
        except requests.RequestException:
            # Fallback to legacy endpoint
            url = f"{self.base_url}/api/embeddings"
            response = requests.post(
                url,
                json={"model": self.model, "prompt": text},
                timeout=120,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("embedding", [])


def build_chat_provider(
    provider: str, base_url: str, api_key: str, headers: Optional[Dict[str, str]] = None
) -> ChatProvider:
    """
    Build a chat provider instance.

    Args:
        provider: Provider type or name (e.g., 'ollama', 'openai', 'fireworks')
        base_url: Provider API base URL
        api_key: API key for authentication
        headers: Optional additional headers

    Returns:
        ChatProvider instance
    """
    provider = (provider or "openai").lower()

    # Check if this is a registered dynamic provider
    dynamic_config = get_provider_config(provider)
    if dynamic_config:
        provider_type = dynamic_config.get("provider_type", "openai")
        base_url = dynamic_config.get("base_url", base_url)
        api_key = dynamic_config.get("api_key") or api_key
        headers = {**(dynamic_config.get("headers") or {}), **(headers or {})}
    else:
        provider_type = provider

    if provider_type == "ollama":
        return OllamaChatProvider(base_url=base_url)

    # For OpenAI-compatible providers, use OpenAI client with custom base_url
    client_kwargs = {"base_url": base_url, "api_key": api_key}
    if headers:
        # Create custom client with additional headers
        from openai import OpenAI

        http_client = requests.Session()
        http_client.headers.update(headers)
        client_kwargs["http_client"] = http_client

    return OpenAIChatProvider(base_url=base_url, api_key=api_key)


def build_chat_provider_from_registry(provider_name: str) -> Optional[ChatProvider]:
    """
    Build a chat provider from the dynamic registry.

    Args:
        provider_name: Registered provider name

    Returns:
        ChatProvider instance or None if not found
    """
    config = get_provider_config(provider_name)
    if not config:
        return None

    provider_type = config.get("provider_type", "openai")
    base_url = config.get("base_url", "")
    api_key = config.get("api_key", "")
    headers = config.get("headers")

    return build_chat_provider(provider_type, base_url, api_key, headers)


def build_embedding_provider(
    provider: str,
    base_url: str,
    api_key: str,
    model: str,
    headers: Optional[Dict[str, str]] = None,
) -> EmbeddingProvider:
    """
    Build an embedding provider.

    Supported providers:
    - openai: OpenAI embeddings API
    - ollama: Local Ollama embeddings
    - deepinfra: DeepInfra embeddings API (OpenAI-compatible)
    - huggingface: HuggingFace Inference API
    - Any dynamic provider from the registry
    """
    provider = (provider or "openai").lower()

    # Check if this is a registered dynamic provider
    dynamic_config = get_provider_config(provider)
    if dynamic_config:
        provider_type = dynamic_config.get("provider_type", "openai")
        base_url = dynamic_config.get("base_url", base_url)
        api_key = dynamic_config.get("api_key") or api_key
    else:
        provider_type = provider

    if provider_type == "ollama":
        return OllamaEmbeddingProvider(base_url=base_url, model=model)
    elif provider_type in ["deepinfra", "huggingface"]:
        # Both use OpenAI-compatible API format
        return OpenAIEmbeddingProvider(base_url=base_url, api_key=api_key, model=model)
    else:
        # Default to OpenAI
        return OpenAIEmbeddingProvider(base_url=base_url, api_key=api_key, model=model)


def build_embedding_provider_from_registry(
    provider_name: str, model: Optional[str] = None
) -> Optional[EmbeddingProvider]:
    """
    Build an embedding provider from the dynamic registry.

    Args:
        provider_name: Registered provider name
        model: Optional model override (uses provider default if not specified)

    Returns:
        EmbeddingProvider instance or None if not found
    """
    config = get_provider_config(provider_name)
    if not config:
        return None

    provider_type = config.get("provider_type", "openai")
    base_url = config.get("base_url", "")
    api_key = config.get("api_key", "")
    headers = config.get("headers")

    # Use specified model or find an embedding model from provider
    if model:
        model_id = model
    else:
        # Try to find an embedding model
        for m_id, m_info in config.get("models", {}).items():
            if "embed" in m_id.lower():
                model_id = m_id
                break
        else:
            # Fallback to first available model
            model_id = config.get("default_model", "text-embedding-3-small")

    return build_embedding_provider(provider_type, base_url, api_key, model_id, headers)
