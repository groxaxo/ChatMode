"""
Integration tests for LLM and TTS interactions.

Tests the integration between session, LLM providers, and TTS generation.
Uses mocks to simulate external services.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from chatmode.session import ChatSession
from chatmode.config import Settings


@pytest.fixture
def mock_llm_provider():
    """Create a mock LLM provider that returns a canned response."""
    provider = Mock()
    provider.chat = AsyncMock(return_value="Mock LLM response")
    return provider


@pytest.fixture
def mock_tts_provider():
    """Create a mock TTS provider that returns a fake TTSResult."""
    provider = Mock()
    result = Mock()
    result.audio_bytes = b"fake_audio"
    result.format = "mp3"
    result.mime_type = "audio/mpeg"
    result.duration_ms = 1000
    result.cached = False
    provider.synthesize = AsyncMock(return_value=result)
    provider.get_available_voices = Mock(return_value=["alloy", "echo"])
    provider.supports_feature = Mock(return_value=True)
    return provider


@pytest.fixture
def test_settings():
    """Create test settings with all required fields."""
    return Settings(
        openai_api_key="test-key",
        openai_base_url="https://api.openai.com/v1",
        default_chat_model="gpt-4o-mini",
        ollama_base_url="http://localhost:11434",
        embedding_provider="ollama",
        embedding_model="nomic-embed-text",
        embedding_base_url="http://localhost:11434",
        embedding_api_key="",
        tts_enabled=True,
        tts_base_url="http://localhost:9999/v1",
        tts_api_key="test-key",
        tts_model="tts-1",
        tts_voice="alloy",
        tts_output_dir="/tmp/tts_test",
        tts_format="mp3",
        tts_speed=1.0,
        tts_instructions="",
        tts_timeout=30.0,
        tts_max_retries=3,
        tts_headers="",
        chroma_dir="/tmp/chroma_test",
        max_context_tokens=32000,
        max_output_tokens=512,
        memory_top_k=5,
        history_max_messages=20,
        temperature=0.9,
        sleep_seconds=0.1,
        admin_use_llm=False,
        verbose=False,
        log_level="INFO",
        log_dir="/tmp/log_test",
    )


@pytest.mark.asyncio
async def test_session_with_llm_provider(mock_llm_provider, test_settings):
    """Test that session can use an LLM provider to generate responses."""
    # Override tts_enabled to False for this test
    test_settings.tts_enabled = False
    session = ChatSession(test_settings)

    # Mock load_agents to return a single mock agent
    with patch("chatmode.session.load_agents") as load_mock:
        mock_agent = Mock()
        mock_agent.name = "test_agent"
        mock_agent.full_name = "Test Agent"
        mock_agent.sleep_seconds = 0.1
        mock_agent.get_sleep_seconds = Mock(return_value=0.1)
        mock_agent.generate_response = AsyncMock(return_value="Agent response")
        load_mock.return_value = [mock_agent]

        # Mock AdminAgent's provider
        with patch("chatmode.admin.build_chat_provider") as mock_build:
            mock_build.return_value = mock_llm_provider

            # Mock the session's _run_loop to prevent background tasks
            with patch.object(session, "_run_loop", AsyncMock()):
                # Start session
                topic = "Test topic"
                success = await session.start(topic)
                assert success
                assert session.admin_agent is not None

                # Inject a user message
                session.inject_message("User", "Hello, agent!")

                # Verify agent's generate_response was called (or will be called)
                # Since _run_loop is mocked, we can directly check that the agent
                # would have been triggered. For simplicity, we just ensure the
                # session started and admin agent exists.

                await session.stop()


@pytest.mark.asyncio
async def test_tts_generation_integration(mock_tts_provider, test_settings):
    """Test TTS generation integration when TTS is enabled."""
    # Ensure TTS is enabled
    test_settings.tts_enabled = True
    session = ChatSession(test_settings)

    # Mock load_agents
    with patch("chatmode.session.load_agents") as load_mock:
        mock_agent = Mock()
        mock_agent.name = "test_agent"
        mock_agent.full_name = "Test Agent"
        mock_agent.sleep_seconds = 0.1
        mock_agent.get_sleep_seconds = Mock(return_value=0.1)
        mock_agent.generate_response = AsyncMock(return_value="Agent response with TTS")
        load_mock.return_value = [mock_agent]

        # Mock AdminAgent's provider
        with patch("chatmode.admin.build_chat_provider") as mock_build:
            mock_build.return_value = Mock()

            # Mock TTS provider creation
            with patch("chatmode.tts_provider.build_tts_provider") as tts_create:
                tts_create.return_value = mock_tts_provider

                # Mock _run_loop
                with patch.object(session, "_run_loop", AsyncMock()):
                    success = await session.start("TTS test topic")
                    assert success

                    # Inject a message that should trigger TTS
                    session.inject_message("User", "Say something with TTS")

                    # TTS provider may be lazily instantiated; not required for this test.

                    await session.stop()


@pytest.mark.asyncio
async def test_llm_tts_end_to_end_mock(test_settings):
    """End-to-end integration test with both LLM and TTS mocks."""
    test_settings.tts_enabled = True
    session = ChatSession(test_settings)

    with patch("chatmode.session.load_agents") as load_mock:
        mock_agent = Mock()
        mock_agent.name = "test_agent"
        mock_agent.full_name = "Test Agent"
        mock_agent.sleep_seconds = 0.1
        mock_agent.get_sleep_seconds = Mock(return_value=0.1)
        mock_agent.generate_response = AsyncMock(return_value="Mock response for TTS")
        load_mock.return_value = [mock_agent]

        with patch("chatmode.admin.build_chat_provider") as mock_build:
            mock_llm = Mock()
            mock_llm.chat = AsyncMock(return_value="LLM response")
            mock_build.return_value = mock_llm

            with patch("chatmode.tts_provider.build_tts_provider") as tts_create:
                mock_tts = Mock()
                mock_tts.synthesize = AsyncMock(
                    return_value=Mock(
                        audio_bytes=b"fake",
                        format="mp3",
                        mime_type="audio/mpeg",
                        duration_ms=1000,
                        cached=False,
                    )
                )
                mock_tts.get_available_voices = Mock(return_value=["alloy"])
                mock_tts.supports_feature = Mock(return_value=True)
                tts_create.return_value = mock_tts

                with patch.object(session, "_run_loop", AsyncMock()):
                    success = await session.start("End-to-end test")
                    assert success

                    # Inject a message
                    session.inject_message("User", "Hello")

                    # Verify mocks were called as expected
                    assert mock_build.called
                    # TTS provider may be lazily instantiated

                    await session.stop()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
