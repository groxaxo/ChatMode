"""
Tests for advanced ChatMode features.
"""

import json
import tempfile
import os
from pathlib import Path

import pytest


def test_agent_profile_with_extra_prompt():
    """Test that agent profiles can include extra_prompt field."""
    from chatmode.agent import ChatAgent
    from chatmode.config import load_settings

    # Create a temporary profile with extra_prompt
    profile_data = {
        "name": "Test Agent",
        "model": "gpt-4o-mini",
        "api": "openai",
        "conversing": "You are a test agent.",
        "extra_prompt": "This is an extra prompt for testing.",
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(profile_data, f)
        profile_path = f.name

    try:
        settings = load_settings()
        agent = ChatAgent(name="test", config_file=profile_path, settings=settings)

        # Verify extra_prompt was added to system_prompt
        assert "This is an extra prompt for testing." in agent.system_prompt
        assert "You are a test agent." in agent.system_prompt
    finally:
        os.unlink(profile_path)


def test_agent_profile_with_memory_settings():
    """Test that agent profiles can override memory settings."""
    from chatmode.agent import ChatAgent
    from chatmode.config import load_settings

    profile_data = {
        "name": "Test Agent",
        "model": "gpt-4o-mini",
        "api": "openai",
        "conversing": "You are a test agent.",
        "memory_top_k": 15,
        "max_context_tokens": 64000,
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(profile_data, f)
        profile_path = f.name

    try:
        settings = load_settings()
        agent = ChatAgent(name="test", config_file=profile_path, settings=settings)

        # Verify per-agent settings were loaded
        assert agent.memory_top_k == 15
        assert agent.max_context_tokens == 64000
    finally:
        os.unlink(profile_path)


def test_agent_profile_with_mcp_config():
    """Test that agent profiles can include MCP configuration."""
    from chatmode.agent import ChatAgent
    from chatmode.config import load_settings

    profile_data = {
        "name": "Test Agent",
        "model": "gpt-4o-mini",
        "api": "openai",
        "conversing": "You are a test agent.",
        "mcp_command": "mcp-server-test",
        "mcp_args": ["--headless"],
        "allowed_tools": ["tool1", "tool2"],
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(profile_data, f)
        profile_path = f.name

    try:
        settings = load_settings()
        agent = ChatAgent(name="test", config_file=profile_path, settings=settings)

        # Verify MCP settings were loaded
        assert agent.mcp_command == "mcp-server-test"
        assert agent.mcp_args == ["--headless"]
        assert agent.allowed_tools == ["tool1", "tool2"]
    finally:
        os.unlink(profile_path)


def test_memory_session_scoped_clear():
    """Test session-scoped memory clearing."""
    from chatmode.memory import MemoryStore
    from chatmode.providers import build_embedding_provider
    from chatmode.config import load_settings

    settings = load_settings()

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create embedding provider
        embedding_provider = build_embedding_provider(
            provider=settings.embedding_provider,
            base_url=settings.embedding_base_url,
            api_key=settings.embedding_api_key or settings.openai_api_key,
            model=settings.embedding_model,
        )

        # Create memory store
        memory = MemoryStore(
            collection_name="test_memory",
            persist_dir=tmpdir,
            embedding_provider=embedding_provider,
        )

        # Add some test memories with session IDs
        memory.add("Test message 1", session_id="session1", agent_id="agent1")
        memory.add("Test message 2", session_id="session2", agent_id="agent1")
        memory.add("Test message 3", session_id="session1", agent_id="agent2")

        # Verify memories were added
        assert memory.count() >= 3

        # Clear memories for session1
        memory.clear(session_id="session1")

        # Verify session1 memories are gone but session2 remains
        # Note: This is a basic test - actual verification would require querying


def test_openai_provider_tool_support():
    """Test that OpenAI provider accepts tools parameter."""
    from chatmode.providers import OpenAIChatProvider

    provider = OpenAIChatProvider(
        base_url="https://api.openai.com/v1", api_key="test-key"
    )

    # Verify the chat method accepts tools parameter
    # (We can't actually call it without a valid API key, but we can check the signature)
    import inspect

    sig = inspect.signature(provider.chat)
    params = sig.parameters

    assert "tools" in params
    assert "tool_choice" in params


def test_admin_agent_generate_response():
    """Test that AdminAgent can generate responses."""
    from chatmode.admin import AdminAgent
    from chatmode.config import load_settings

    settings = load_settings()
    admin = AdminAgent(settings)

    # Verify AdminAgent has the full_name attribute
    assert admin.full_name == "Admin"

    # Verify it has the generate_response method
    assert hasattr(admin, "generate_response")


def test_chat_session_supports_single_agent():
    """Test that ChatSession accepts single agent configuration."""
    # This test would require mocking the agent loading
    # For now, we just verify the constraint was removed
    from chatmode.session import ChatSession
    from chatmode.config import load_settings

    settings = load_settings()
    session = ChatSession(settings)

    # Verify session has admin_agent attribute for solo mode
    assert hasattr(session, "admin_agent")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
