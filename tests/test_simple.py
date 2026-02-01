"""
Simple test script for TTS provider and agent state management.
Run this directly with: python3 tests/test_simple.py
"""

import asyncio
import tempfile
from pathlib import Path
import pytest

# Test text normalization
from chatmode.tts_provider import (
    normalize_text_for_tts,
    get_mime_type_for_format,
    AudioStorage,
)
from chatmode.agent_state import AgentState, AgentStateManager


def test_text_normalization():
    """Test text normalization for TTS."""
    print("Testing text normalization...")

    # Test bold markdown
    result = normalize_text_for_tts("This is **bold** text")
    assert (
        result == "This is bold text"
    ), f"Expected 'This is bold text', got '{result}'"

    # Test italic markdown
    result = normalize_text_for_tts("This is *italic* text")
    assert (
        result == "This is italic text"
    ), f"Expected 'This is italic text', got '{result}'"

    # Test links
    result = normalize_text_for_tts("Check out [this link](http://example.com) here")
    assert (
        result == "Check out this link here"
    ), f"Expected 'Check out this link here', got '{result}'"

    # Test whitespace
    result = normalize_text_for_tts("Multiple   spaces    and\n\nnewlines")
    assert (
        result == "Multiple spaces and newlines"
    ), f"Expected 'Multiple spaces and newlines', got '{result}'"

    print("✓ Text normalization tests passed")


def test_mime_types():
    """Test MIME type detection."""
    print("Testing MIME types...")

    assert get_mime_type_for_format("mp3") == "audio/mpeg"
    assert get_mime_type_for_format("opus") == "audio/opus"
    assert get_mime_type_for_format("wav") == "audio/wav"
    assert get_mime_type_for_format("unknown") == "audio/mpeg"  # Default

    print("✓ MIME type tests passed")


def test_audio_storage():
    """Test audio storage functionality."""
    print("Testing audio storage...")

    with tempfile.TemporaryDirectory() as tmp_dir:
        storage = AudioStorage(base_dir=tmp_dir)

        # Test hash consistency
        hash1 = storage._compute_hash("hello", "alloy", "tts-1", "mp3", 1.0)
        hash2 = storage._compute_hash("hello", "alloy", "tts-1", "mp3", 1.0)
        assert hash1 == hash2, "Hash should be consistent for same inputs"

        # Test different inputs produce different hashes
        hash3 = storage._compute_hash("world", "alloy", "tts-1", "mp3", 1.0)
        assert hash1 != hash3, "Different inputs should produce different hashes"

        # Test save and retrieve
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

        assert not was_cached, "First save should not be cached"
        assert "test-session" in relative_path
        assert "msg-1" in relative_path

        # Verify file exists
        full_path = storage.get_audio_path(relative_path)
        assert full_path.exists(), "File should exist after save"
        assert full_path.read_bytes() == audio_bytes, "File content should match"

        # Test caching - save same content again
        path2, was_cached2 = storage.save_audio(
            audio_bytes=audio_bytes,
            session_id="session-2",
            message_id="msg-2",
            text="Hello world",
            voice="alloy",
            model="tts-1",
            format="mp3",
        )

        assert was_cached2, "Second save of same content should be cached"

        print("✓ Audio storage tests passed")


@pytest.mark.asyncio
@pytest.mark.skip(reason="Standalone script")
async def test_agent_state_manager():
    """Test agent state management."""
    print("Testing agent state management...")

    manager = AgentStateManager()

    # Test register
    await manager.register_agent("agent-1")
    state = await manager.get_state("agent-1")
    assert state.state == AgentState.ACTIVE, "New agent should be ACTIVE"

    # Test pause and resume
    success = await manager.pause_agent("agent-1", "Test pause")
    assert success, "Pause should succeed"

    state = await manager.get_state("agent-1")
    assert state.state == AgentState.PAUSED, "Agent should be PAUSED"
    assert state.reason == "Test pause", "Reason should be set"

    success = await manager.resume_agent("agent-1")
    assert success, "Resume should succeed"

    state = await manager.get_state("agent-1")
    assert state.state == AgentState.ACTIVE, "Agent should be ACTIVE after resume"

    # Test stop
    success = await manager.stop_agent("agent-1", "Test stop")
    assert success, "Stop should succeed"

    is_active = await manager.is_active("agent-1")
    assert not is_active, "Stopped agent should not be active"

    # Test restart
    success = await manager.restart_agent("agent-1")
    assert success, "Restart should succeed"

    is_active = await manager.is_active("agent-1")
    assert is_active, "Restarted agent should be active"

    # Test finish
    success = await manager.finish_agent("agent-1", "Test finish")
    assert success, "Finish should succeed"

    is_active = await manager.is_active("agent-1")
    assert not is_active, "Finished agent should not be active"

    # Test get active agents
    await manager.register_agent("agent-2")
    await manager.register_agent("agent-3")
    await manager.pause_agent("agent-2")

    active = await manager.get_active_agents()
    assert "agent-1" not in active, "Finished agent should not be in active list"
    assert "agent-2" not in active, "Paused agent should not be in active list"
    assert "agent-3" in active, "Active agent should be in active list"

    # Test unknown agent operations
    assert not await manager.pause_agent(
        "unknown"
    ), "Pause on unknown agent should fail"
    assert not await manager.resume_agent(
        "unknown"
    ), "Resume on unknown agent should fail"
    assert not await manager.stop_agent("unknown"), "Stop on unknown agent should fail"

    print("✓ Agent state management tests passed")


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("Running TTS and Agent State Tests")
    print("=" * 60 + "\n")

    try:
        test_text_normalization()
        test_mime_types()
        test_audio_storage()
        await test_agent_state_manager()

        print("\n" + "=" * 60)
        print("All tests passed! ✓")
        print("=" * 60 + "\n")

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        raise
    except Exception as e:
        print(f"\n❌ Error during tests: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
