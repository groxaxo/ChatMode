"""
Unit tests for TTS provider and agent state management.
"""

import asyncio
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

from chatmode.tts_provider import (
    normalize_text_for_tts,
    get_mime_type_for_format,
    TTSResult,
    OpenAICompatibleTTSProvider,
    AudioStorage,
    TTSProviderError,
)
from chatmode.agent_state import (
    AgentState,
    AgentStateInfo,
    AgentStateManager,
)


class TestTextNormalization:
    """Test text normalization for TTS."""

    def test_remove_bold_markdown(self):
        text = "This is **bold** text"
        result = normalize_text_for_tts(text)
        assert result == "This is bold text"

    def test_remove_italic_markdown(self):
        text = "This is *italic* text"
        result = normalize_text_for_tts(text)
        assert result == "This is italic text"

    def test_remove_links(self):
        text = "Check out [this link](http://example.com) here"
        result = normalize_text_for_tts(text)
        assert result == "Check out this link here"

    def test_collapse_whitespace(self):
        text = "Multiple   spaces    and\n\nnewlines"
        result = normalize_text_for_tts(text)
        assert result == "Multiple spaces and newlines"

    def test_empty_text(self):
        result = normalize_text_for_tts("")
        assert result == ""


class TestMimeTypes:
    """Test MIME type detection."""

    def test_mp3(self):
        assert get_mime_type_for_format("mp3") == "audio/mpeg"

    def test_opus(self):
        assert get_mime_type_for_format("opus") == "audio/opus"

    def test_wav(self):
        assert get_mime_type_for_format("wav") == "audio/wav"

    def test_unknown(self):
        assert get_mime_type_for_format("unknown") == "audio/mpeg"


class TestAudioStorage:
    """Test audio storage functionality."""

    @pytest.fixture
    def storage(self, tmp_path):
        return AudioStorage(base_dir=str(tmp_path))

    def test_compute_hash_consistency(self, storage):
        """Same inputs should produce same hash."""
        hash1 = storage._compute_hash("hello", "alloy", "tts-1", "mp3", 1.0)
        hash2 = storage._compute_hash("hello", "alloy", "tts-1", "mp3", 1.0)
        assert hash1 == hash2

    def test_compute_hash_different_inputs(self, storage):
        """Different inputs should produce different hashes."""
        hash1 = storage._compute_hash("hello", "alloy", "tts-1", "mp3", 1.0)
        hash2 = storage._compute_hash("world", "alloy", "tts-1", "mp3", 1.0)
        assert hash1 != hash2

    def test_save_and_retrieve(self, storage):
        """Test saving and retrieving audio."""
        audio_bytes = b"fake audio data"
        relative_path, was_cached = storage.save_audio(
            audio_bytes=audio_bytes,
            session_id="test-session",
            message_id="msg-1",
            text="Hello world",
            voice="alloy",
            model="tts-1",
            format="mp3",
        )

        assert not was_cached
        assert "test-session" in relative_path
        assert "msg-1" in relative_path

        # Verify file exists
        full_path = storage.get_audio_path(relative_path)
        assert full_path.exists()
        assert full_path.read_bytes() == audio_bytes

    def test_caching(self, storage):
        """Test that identical content is cached."""
        audio_bytes = b"fake audio data"

        # Save first time
        path1, cached1 = storage.save_audio(
            audio_bytes=audio_bytes,
            session_id="session-1",
            message_id="msg-1",
            text="Hello",
            voice="alloy",
            model="tts-1",
            format="mp3",
        )

        assert not cached1

        # Save same content again
        path2, cached2 = storage.save_audio(
            audio_bytes=audio_bytes,
            session_id="session-2",
            message_id="msg-2",
            text="Hello",
            voice="alloy",
            model="tts-1",
            format="mp3",
        )

        assert cached2

    def test_cleanup_session(self, storage):
        """Test session cleanup."""
        audio_bytes = b"fake audio"

        storage.save_audio(
            audio_bytes=audio_bytes,
            session_id="session-to-cleanup",
            message_id="msg-1",
            text="Hello",
            voice="alloy",
            model="tts-1",
            format="mp3",
        )

        session_dir = storage.base_dir / "session-to-cleanup"
        assert session_dir.exists()

        storage.cleanup_session("session-to-cleanup")

        assert not session_dir.exists()


class TestAgentStateManager:
    """Test agent state management."""

    @pytest.fixture
    async def manager(self):
        return AgentStateManager()

    @pytest.mark.asyncio
    async def test_register_agent(self, manager):
        await manager.register_agent("agent-1")
        state = await manager.get_state("agent-1")
        assert state.state == AgentState.ACTIVE

    @pytest.mark.asyncio
    async def test_pause_and_resume(self, manager):
        await manager.register_agent("agent-1")

        # Pause
        success = await manager.pause_agent("agent-1", "Test pause")
        assert success

        state = await manager.get_state("agent-1")
        assert state.state == AgentState.PAUSED
        assert state.reason == "Test pause"

        # Resume
        success = await manager.resume_agent("agent-1")
        assert success

        state = await manager.get_state("agent-1")
        assert state.state == AgentState.ACTIVE

    @pytest.mark.asyncio
    async def test_stop_agent(self, manager):
        await manager.register_agent("agent-1")

        success = await manager.stop_agent("agent-1", "Test stop")
        assert success

        state = await manager.get_state("agent-1")
        assert state.state == AgentState.STOPPED

        # Should not be active
        is_active = await manager.is_active("agent-1")
        assert not is_active

    @pytest.mark.asyncio
    async def test_finish_agent(self, manager):
        await manager.register_agent("agent-1")

        success = await manager.finish_agent("agent-1", "Test finish")
        assert success

        state = await manager.get_state("agent-1")
        assert state.state == AgentState.FINISHED

    @pytest.mark.asyncio
    async def test_restart_agent(self, manager):
        await manager.register_agent("agent-1")
        await manager.stop_agent("agent-1")

        success = await manager.restart_agent("agent-1")
        assert success

        state = await manager.get_state("agent-1")
        assert state.state == AgentState.ACTIVE

    @pytest.mark.asyncio
    async def test_get_active_agents(self, manager):
        await manager.register_agent("agent-1")
        await manager.register_agent("agent-2")
        await manager.register_agent("agent-3")

        await manager.pause_agent("agent-2")

        active = await manager.get_active_agents()
        assert "agent-1" in active
        assert "agent-2" not in active
        assert "agent-3" in active

    @pytest.mark.asyncio
    async def test_task_cancellation_on_pause(self, manager):
        await manager.register_agent("agent-1")

        # Create a mock task
        mock_task = AsyncMock()
        mock_task.done.return_value = False
        await manager.set_task("agent-1", mock_task)

        # Pause should cancel the task
        await manager.pause_agent("agent-1")

        mock_task.cancel.assert_called_once()

    @pytest.mark.asyncio
    async def test_unknown_agent_operations(self, manager):
        # Operations on unknown agents should return False
        assert not await manager.pause_agent("unknown")
        assert not await manager.resume_agent("unknown")
        assert not await manager.stop_agent("unknown")
        assert not await manager.finish_agent("unknown")
        assert not await manager.restart_agent("unknown")


class TestOpenAICompatibleTTSProvider:
    """Test OpenAI-compatible TTS provider."""

    @pytest.mark.asyncio
    async def test_initialization(self):
        provider = OpenAICompatibleTTSProvider(
            base_url="https://api.openai.com/v1",
            api_key="test-key",
            timeout=30.0,
        )

        assert provider.base_url == "https://api.openai.com/v1"
        assert provider.timeout == 30.0

        await provider.close()

    @pytest.mark.asyncio
    async def test_get_available_voices(self):
        provider = OpenAICompatibleTTSProvider(
            base_url="https://api.openai.com/v1",
            api_key="test-key",
        )

        voices = provider.get_available_voices()
        assert "alloy" in voices
        assert "echo" in voices
        assert "fable" in voices

        await provider.close()

    @pytest.mark.asyncio
    async def test_empty_text_error(self):
        provider = OpenAICompatibleTTSProvider(
            base_url="https://api.openai.com/v1",
            api_key="test-key",
        )

        with pytest.raises(ValueError, match="Text cannot be empty"):
            await provider.synthesize(
                text="",
                voice="alloy",
            )

        await provider.close()

    @pytest.mark.asyncio
    async def test_invalid_speed(self):
        provider = OpenAICompatibleTTSProvider(
            base_url="https://api.openai.com/v1",
            api_key="test-key",
        )

        with pytest.raises(ValueError, match="Speed must be between"):
            await provider.synthesize(
                text="Hello",
                voice="alloy",
                speed=5.0,  # Too high
            )

        await provider.close()


class TestTTSProviderError:
    """Test TTS provider error handling."""

    def test_error_with_status_code(self):
        error = TTSProviderError(
            message="Request failed",
            status_code=500,
            response_body="Internal server error",
        )

        assert error.status_code == 500
        assert error.response_body == "Internal server error"
        assert not error.is_timeout

    def test_timeout_error(self):
        error = TTSProviderError(
            message="Request timed out",
            is_timeout=True,
        )

        assert error.is_timeout
        assert error.status_code is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
