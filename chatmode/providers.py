import json
from dataclasses import dataclass
from typing import List, Dict, Optional

import requests
from openai import OpenAI


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
    ) -> str:
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
            The response content or tool call information
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
        
        # Check if model returned a tool call
        choice = response.choices[0] if response.choices else None
        if choice and hasattr(choice.message, "tool_calls") and choice.message.tool_calls:
            # Return tool calls as a special marker
            tool_calls_data = []
            for tool_call in choice.message.tool_calls:
                tool_calls_data.append({
                    "id": tool_call.id,
                    "type": tool_call.type,
                    "function": {
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments,
                    }
                })
            # Return JSON-encoded tool calls with special prefix
            import json
            return f"__TOOL_CALLS__:{json.dumps(tool_calls_data)}"
        
        return choice.message.content if choice else ""


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
    ) -> str:
        """
        Generate a chat completion.
        
        Note: Ollama doesn't currently support tool calling, so tools/tool_choice are ignored.
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
        return data.get("message", {}).get("content", "")


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


def build_chat_provider(provider: str, base_url: str, api_key: str) -> ChatProvider:
    provider = (provider or "openai").lower()
    if provider == "ollama":
        return OllamaChatProvider(base_url=base_url)
    return OpenAIChatProvider(base_url=base_url, api_key=api_key)


def build_embedding_provider(provider: str, base_url: str, api_key: str, model: str) -> EmbeddingProvider:
    """
    Build an embedding provider.
    
    Supported providers:
    - openai: OpenAI embeddings API
    - ollama: Local Ollama embeddings
    - deepinfra: DeepInfra embeddings API (OpenAI-compatible)
    - huggingface: HuggingFace Inference API
    """
    provider = (provider or "openai").lower()
    
    if provider == "ollama":
        return OllamaEmbeddingProvider(base_url=base_url, model=model)
    elif provider in ["deepinfra", "huggingface"]:
        # Both use OpenAI-compatible API format
        return OpenAIEmbeddingProvider(base_url=base_url, api_key=api_key, model=model)
    else:
        # Default to OpenAI
        return OpenAIEmbeddingProvider(base_url=base_url, api_key=api_key, model=model)
