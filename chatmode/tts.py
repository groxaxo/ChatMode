import logging
import os
import re
from dataclasses import dataclass, field
from typing import Optional

from openai import OpenAI

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


@dataclass
class TTSClient:
    """
    TTS client for OpenAI-compatible voice synthesis APIs.

    Supports OpenAI's TTS API and compatible endpoints.
    """

    base_url: str
    api_key: str
    model: str
    voice: str
    output_dir: str
    _client: OpenAI = field(init=False, repr=False)

    def __post_init__(self):
        self._client = OpenAI(base_url=self.base_url, api_key=self.api_key)
        os.makedirs(self.output_dir, exist_ok=True)
        logger.info(
            f"TTSClient initialized: {self.base_url}, model={self.model}, voice={self.voice}"
        )

    def speak(
        self,
        text: str,
        model: Optional[str] = None,
        voice: Optional[str] = None,
        filename_prefix: str = "tts",
        format: str = "mp3",
    ) -> Optional[str]:
        """
        Generate speech from text.

        Args:
            text: Text to synthesize
            model: TTS model override
            voice: Voice override
            filename_prefix: Prefix for output filename
            format: Output format (mp3, wav, opus)

        Returns:
            Path to generated audio file, or None on error
        """
        if not text:
            logger.warning("TTS called with empty text")
            return None

        # Normalize text for better TTS output
        normalized_text = normalize_text_for_tts(text)
        if not normalized_text:
            return None

        model = model or self.model
        voice = voice or self.voice

        # Generate unique filename based on content hash
        filename = f"{filename_prefix}_{abs(hash(normalized_text))}.{format}"
        output_path = os.path.join(self.output_dir, filename)

        # Check if already generated (cache)
        if os.path.exists(output_path):
            logger.debug(f"TTS cache hit: {filename}")
            return output_path

        try:
            logger.info(
                f"TTS request: model={model}, voice={voice}, text_len={len(normalized_text)}"
            )
            response = self._client.audio.speech.create(
                model=model,
                voice=voice,
                input=normalized_text,
                response_format=format,
            )
            response.stream_to_file(output_path)
            logger.info(f"TTS generated: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"TTS generation failed: {e}")
            # Return None instead of raising - allows graceful degradation
            return None

    def get_available_voices(self) -> list:
        """
        Return list of standard OpenAI TTS voices.
        """
        return ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
