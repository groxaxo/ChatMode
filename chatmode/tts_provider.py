"""
TTS Provider abstraction for OpenAI-compatible text-to-speech APIs.

Supports multiple TTS providers with a unified interface.
"""

import hashlib
import logging
import os
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


def normalize_text_for_tts(text: str) -> str:
    """
    Normalize text for TTS input.

    - Remove markdown formatting
    - Collapse multiple spaces
    - Handle common abbreviations
    """
    # Remove markdown bold/italic
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    text = re.sub(r"__([^_]+)__", r"\1", text)
    text = re.sub(r"_([^_]+)_", r"\1", text)

    # Remove markdown links
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)

    # Collapse multiple spaces/newlines
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def get_mime_type_for_format(format: str) -> str:
    """Get MIME type for audio format."""
    mime_types = {
        "mp3": "audio/mpeg",
        "opus": "audio/opus",
        "aac": "audio/aac",
        "flac": "audio/flac",
        "wav": "audio/wav",
        "pcm": "audio/pcm",
    }
    return mime_types.get(format.lower(), "audio/mpeg")


@dataclass
class TTSResult:
    """Result of TTS synthesis."""

    audio_bytes: bytes
    format: str
    mime_type: str
    duration_ms: Optional[int] = None
    cached: bool = False


class TTSProvider(ABC):
    """Abstract base class for TTS providers."""

    @abstractmethod
    async def synthesize(
        self,
        text: str,
        voice: str,
        model: Optional[str] = None,
        response_format: str = "mp3",
        speed: Optional[float] = None,
        instructions: Optional[str] = None,
    ) -> TTSResult:
        """
        Synthesize text to speech.

        Args:
            text: Text to synthesize
            voice: Voice ID
            model: Model name (optional)
            response_format: Output format (mp3, opus, aac, flac, wav, pcm)
            speed: Speech speed multiplier (0.25-4.0)
            instructions: Additional instructions for the model

        Returns:
            TTSResult with audio bytes and metadata
        """
        pass

    @abstractmethod
    def get_available_voices(self) -> list:
        """Return list of available voices (if supported by provider)."""
        pass

    @abstractmethod
    def supports_feature(self, feature: str) -> bool:
        """Check if provider supports a specific feature."""
        pass


class OpenAICompatibleTTSProvider(TTSProvider):
    """
    OpenAI-compatible TTS provider.

    Works with OpenAI's official API and any compatible endpoint.
    """

    # Standard OpenAI voices
    STANDARD_VOICES = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]

    # Supported features and their availability
    FEATURES = {
        "voice_listing": False,  # Not all clones support this
        "speed_control": True,
        "instructions": True,  # gpt-4o-mini-tts supports this
        "streaming": False,  # We'll implement later if needed
    }

    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout: float = 30.0,
        max_retries: int = 3,
        headers: Optional[Dict[str, str]] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.headers = headers or {}

        # Initialize HTTP client
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                **self.headers,
            },
        )

        logger.info(f"OpenAICompatibleTTSProvider initialized: {base_url}")

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def synthesize(
        self,
        text: str,
        voice: str,
        model: Optional[str] = None,
        response_format: str = "mp3",
        speed: Optional[float] = None,
        instructions: Optional[str] = None,
    ) -> TTSResult:
        """
        Synthesize text using OpenAI-compatible API.

        POST /v1/audio/speech
        """
        if not text:
            logger.warning("TTS called with empty text")
            raise ValueError("Text cannot be empty")

        # Normalize text
        normalized_text = normalize_text_for_tts(text)
        if not normalized_text:
            raise ValueError("Text is empty after normalization")

        # Build request payload
        payload = {
            "model": model or "tts-1",
            "input": normalized_text,
            "voice": voice,
            "response_format": response_format,
        }

        # Add optional parameters
        if speed is not None:
            if not 0.25 <= speed <= 4.0:
                raise ValueError("Speed must be between 0.25 and 4.0")
            payload["speed"] = speed

        if instructions and model and "gpt-4o" in model:
            # Instructions only supported for gpt-4o-mini-tts
            payload["instructions"] = instructions

        try:
            logger.debug(
                f"TTS request: model={payload['model']}, voice={voice}, "
                f"format={response_format}, text_len={len(normalized_text)}"
            )

            response = await self.client.post(
                f"{self.base_url}/v1/audio/speech",
                json=payload,
            )
            response.raise_for_status()

            audio_bytes = response.content
            mime_type = get_mime_type_for_format(response_format)

            logger.info(
                f"TTS success: {len(audio_bytes)} bytes, format={response_format}"
            )

            return TTSResult(
                audio_bytes=audio_bytes,
                format=response_format,
                mime_type=mime_type,
                cached=False,
            )

        except httpx.HTTPStatusError as e:
            logger.error(
                f"TTS HTTP error: {e.response.status_code} - {e.response.text}"
            )
            raise TTSProviderError(
                f"TTS request failed: {e.response.status_code}",
                status_code=e.response.status_code,
                response_body=e.response.text,
            ) from e
        except httpx.TimeoutException as e:
            logger.error(f"TTS timeout after {self.timeout}s")
            raise TTSProviderError(
                f"TTS request timed out after {self.timeout}s",
                is_timeout=True,
            ) from e
        except Exception as e:
            logger.error(f"TTS error: {e}")
            raise TTSProviderError(f"TTS synthesis failed: {e}") from e

    def get_available_voices(self) -> list:
        """
        Return standard OpenAI voices.

        Note: Not all compatible providers support voice listing,
        so we return the standard set. Feature detection should be used
        to determine if the provider supports custom voice listing.
        """
        return self.STANDARD_VOICES.copy()

    def supports_feature(self, feature: str) -> bool:
        """Check if a feature is supported."""
        return self.FEATURES.get(feature, False)


class TTSProviderError(Exception):
    """Custom exception for TTS provider errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None,
        is_timeout: bool = False,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body
        self.is_timeout = is_timeout


def build_tts_provider(
    provider: str = "openai",
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    timeout: float = 30.0,
    max_retries: int = 3,
    headers: Optional[Dict[str, str]] = None,
) -> TTSProvider:
    """
    Factory function to build a TTS provider.

    Args:
        provider: Provider type (currently only "openai" supported)
        base_url: API base URL
        api_key: API key
        timeout: Request timeout in seconds
        max_retries: Maximum retry attempts
        headers: Additional HTTP headers

    Returns:
        Configured TTSProvider instance
    """
    if provider == "openai":
        return OpenAICompatibleTTSProvider(
            base_url=base_url or "https://api.openai.com/v1",
            api_key=api_key or "",
            timeout=timeout,
            max_retries=max_retries,
            headers=headers,
        )
    else:
        raise ValueError(f"Unsupported TTS provider: {provider}")


class AudioStorage:
    """
    Manages audio file storage and retrieval.

    Stores audio files with content-based hashing for caching.
    """

    def __init__(self, base_dir: str = "./data/audio"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"AudioStorage initialized: {base_dir}")

    def _compute_hash(
        self, text: str, voice: str, model: str, format: str, speed: Optional[float]
    ) -> str:
        """Compute content hash for caching."""
        content = f"{text}:{voice}:{model}:{format}:{speed}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def get_storage_path(
        self,
        session_id: str,
        message_id: str,
        text: str,
        voice: str,
        model: str,
        format: str,
        speed: Optional[float] = None,
    ) -> Tuple[Path, bool]:
        """
        Get storage path for audio file.

        Returns:
            Tuple of (path, is_cached)
        """
        # Check cache first
        content_hash = self._compute_hash(text, voice, model, format, speed)
        cache_dir = self.base_dir / "cache"
        cache_dir.mkdir(exist_ok=True)
        cache_path = cache_dir / f"{content_hash}.{format}"

        if cache_path.exists():
            logger.debug(f"Audio cache hit: {content_hash}")
            return cache_path, True

        # Create session-specific path
        session_dir = self.base_dir / session_id
        session_dir.mkdir(exist_ok=True)
        storage_path = session_dir / f"{message_id}.{format}"

        return storage_path, False

    def save_audio(
        self,
        audio_bytes: bytes,
        session_id: str,
        message_id: str,
        text: str,
        voice: str,
        model: str,
        format: str,
        speed: Optional[float] = None,
    ) -> Tuple[str, bool]:
        """
        Save audio bytes to storage.

        Returns:
            Tuple of (relative_path, was_cached)
        """
        path, was_cached = self.get_storage_path(
            session_id, message_id, text, voice, model, format, speed
        )

        if was_cached:
            # Just return the cached file path
            return str(path.relative_to(self.base_dir)), True

        # Also save to cache for future reuse
        content_hash = self._compute_hash(text, voice, model, format, speed)
        cache_path = self.base_dir / "cache" / f"{content_hash}.{format}"

        # Write to both locations
        path.write_bytes(audio_bytes)
        cache_path.write_bytes(audio_bytes)

        logger.debug(f"Audio saved: {path} ({len(audio_bytes)} bytes)")
        return str(path.relative_to(self.base_dir)), False

    def get_audio_path(self, relative_path: str) -> Path:
        """Get full path from relative path."""
        return self.base_dir / relative_path

    def cleanup_session(self, session_id: str):
        """Remove all audio files for a session."""
        session_dir = self.base_dir / session_id
        if session_dir.exists():
            import shutil

            shutil.rmtree(session_dir)
            logger.info(f"Cleaned up audio for session: {session_id}")


# Legacy TTSClient for backwards compatibility
class TTSClient:
    """
    Legacy synchronous TTS client.

    Maintains backwards compatibility with existing code.
    New code should use TTSProvider directly.
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        voice: str,
        output_dir: str,
    ):
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        self.voice = voice
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        # Create async provider for actual synthesis
        self._provider = OpenAICompatibleTTSProvider(
            base_url=base_url,
            api_key=api_key,
        )

        logger.info(f"TTSClient initialized (legacy): {base_url}")

    def speak(
        self,
        text: str,
        model: Optional[str] = None,
        voice: Optional[str] = None,
        filename_prefix: str = "tts",
        format: str = "mp3",
    ) -> Optional[str]:
        """
        Synchronously generate speech (legacy method).

        Returns path to generated audio file.
        """
        import asyncio

        if not text:
            logger.warning("TTS called with empty text")
            return None

        try:
            # Run async synthesis in sync context
            result = asyncio.run(
                self._provider.synthesize(
                    text=text,
                    voice=voice or self.voice,
                    model=model or self.model,
                    response_format=format,
                )
            )

            # Generate filename
            normalized = normalize_text_for_tts(text)
            filename = f"{filename_prefix}_{abs(hash(normalized))}.{format}"
            output_path = os.path.join(self.output_dir, filename)

            # Write file
            with open(output_path, "wb") as f:
                f.write(result.audio_bytes)

            logger.info(f"TTS generated (legacy): {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"TTS generation failed: {e}")
            return None

    def get_available_voices(self) -> list:
        """Return list of standard OpenAI TTS voices."""
        return self._provider.get_available_voices()
