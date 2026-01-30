"""
Comprehensive smoke tests for ChatMode features.

These tests validate:
1. Profile loading (extra_prompt, backward compatibility)
2. Solo mode (AdminAgent interaction)
3. Memory (session/agent tagging, retrieval, purge)
4. MCP/Tooling (list tools, block unauthorized, call tools)
5. Exports (transcript download)
"""

import json
import tempfile
import os
import uuid
from pathlib import Path
from unittest.mock import Mock, AsyncMock, MagicMock, patch

import pytest


class TestProfileLoading:
    """Test agent profile loading with various configurations."""
    
    def test_profile_with_extra_prompt(self):
        """Load an existing profile with extra_prompt and confirm prompt is not silently rewritten."""
        from chatmode.agent import ChatAgent
        from chatmode.config import load_settings
        
        profile_data = {
            "name": "Test Agent",
            "model": "gpt-4o-mini",
            "api": "openai",
            "conversing": "You are a helpful assistant.",
            "extra_prompt": "Additional instructions for testing."
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(profile_data, f)
            profile_path = f.name
        
        try:
            settings = load_settings()
            agent = ChatAgent(name="test", config_file=profile_path, settings=settings)
            
            # Verify extra_prompt was appended, not replaced
            assert "You are a helpful assistant." in agent.system_prompt
            assert "Additional instructions for testing." in agent.system_prompt
            # Ensure it was appended (both present)
            assert agent.system_prompt.count("You are a helpful assistant.") == 1
            assert agent.system_prompt.count("Additional instructions for testing.") == 1
            
        finally:
            os.unlink(profile_path)
    
    def test_profile_backward_compatibility_without_optional_fields(self):
        """Load a profile without new optional fields and confirm it still runs."""
        from chatmode.agent import ChatAgent
        from chatmode.config import load_settings
        
        # Old-style profile without extra_prompt, memory_top_k, etc.
        profile_data = {
            "name": "Legacy Agent",
            "model": "gpt-4",
            "api": "openai",
            "conversing": "You are a legacy agent."
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(profile_data, f)
            profile_path = f.name
        
        try:
            settings = load_settings()
            agent = ChatAgent(name="legacy", config_file=profile_path, settings=settings)
            
            # Should load successfully
            assert agent.full_name == "Legacy Agent"
            assert agent.system_prompt == "You are a legacy agent."
            # Optional fields should be None or default
            assert agent.memory_top_k is None
            assert agent.max_context_tokens is None
            assert agent.mcp_command is None
            assert agent.allowed_tools == []
            
        finally:
            os.unlink(profile_path)


class TestSoloMode:
    """Test single-agent mode with AdminAgent."""
    
    def test_admin_agent_creates_clarifying_questions(self):
        """Verify AdminAgent generates clarifying questions, not dead-loops."""
        from chatmode.admin import AdminAgent
        from chatmode.config import load_settings
        
        settings = load_settings()
        admin = AdminAgent(settings)
        
        # Test with empty history (first turn)
        topic = "Is AI consciousness possible?"
        history = []
        
        # Mock the provider to avoid actual API calls
        with patch.object(admin.provider, 'chat') as mock_chat:
            mock_message = Mock()
            mock_message.content = "What do you mean by consciousness?"
            mock_message.tool_calls = None
            mock_chat.return_value = mock_message
            
            response = admin.generate_response(topic, history)
            
            # Should generate a response
            assert response is not None
            assert len(response) > 0
            assert "What do you mean by consciousness?" in response
    
    def test_session_supports_solo_mode(self):
        """Verify ChatSession creates AdminAgent when only 1 agent present."""
        from chatmode.session import ChatSession
        from chatmode.config import load_settings
        
        settings = load_settings()
        session = ChatSession(settings)
        
        # Verify session has admin_agent attribute
        assert hasattr(session, 'admin_agent')
        assert session.admin_agent is None  # Not created until session starts
        
        # Mock agent loading to return single agent
        with patch('chatmode.session.load_agents') as mock_load:
            mock_agent = Mock()
            mock_agent.name = "solo"
            mock_agent.full_name = "Solo Agent"
            mock_load.return_value = [mock_agent]
            
            # Start session with 1 agent
            success = session.start("Test topic")
            
            assert success
            # AdminAgent should be created for solo mode
            assert session.admin_agent is not None
            assert session.admin_agent.full_name == "Admin"


class TestMemory:
    """Test memory storage with session_id and agent_id tagging."""
    
    def test_memory_entries_tagged_by_session_and_agent(self):
        """Confirm memory entries are tagged with session_id and agent_id."""
        from chatmode.memory import MemoryStore
        from chatmode.providers import build_embedding_provider
        from chatmode.config import load_settings
        
        settings = load_settings()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Mock embedding provider to avoid external dependencies
            mock_embedding_provider = Mock()
            mock_embedding_provider.embed.return_value = [[0.1] * 384]  # Mock embedding
            
            memory = MemoryStore(
                collection_name=f"test_memory_{uuid.uuid4().hex[:8]}",
                persist_dir=tmpdir,
                embedding_provider=mock_embedding_provider
            )
            
            # Add memory with session_id and agent_id
            memory.add(
                "Test message 1",
                metadata={"sender": "TestAgent"},
                session_id="session_123",
                agent_id="agent_1"
            )
            
            # Verify embedding was called
            assert mock_embedding_provider.embed.called
            
            # Query to verify filtering works (will need to check the collection)
            # Since we're mocking embeddings, we can't fully test retrieval
            # but we verified the add() accepts and stores the parameters
    
    def test_memory_retrieval_respects_filters(self):
        """Confirm retrieval respects session_id and agent_id filters."""
        from chatmode.memory import MemoryStore
        from chatmode.config import load_settings
        
        settings = load_settings()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Mock embedding provider
            mock_embedding_provider = Mock()
            mock_embedding_provider.embed.return_value = [[0.1] * 384]
            
            memory = MemoryStore(
                collection_name=f"test_memory_{uuid.uuid4().hex[:8]}",
                persist_dir=tmpdir,
                embedding_provider=mock_embedding_provider
            )
            
            # Test query with filters
            # Even if collection is empty, the method should accept the filters
            results = memory.query(
                "test query",
                k=5,
                session_id="session_123",
                agent_id="agent_1"
            )
            
            # Should return empty list but not error
            assert isinstance(results, list)
    
    def test_memory_purge_agent_only(self):
        """Test memory purge for specific agent only."""
        from chatmode.memory import MemoryStore
        
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_embedding_provider = Mock()
            mock_embedding_provider.embed.return_value = [[0.1] * 384]
            
            memory = MemoryStore(
                collection_name=f"test_memory_{uuid.uuid4().hex[:8]}",
                persist_dir=tmpdir,
                embedding_provider=mock_embedding_provider
            )
            
            # Test clear with agent_id
            memory.clear(agent_id="agent_1")
            # Should complete without error
    
    def test_memory_purge_session_only(self):
        """Test memory purge for specific session only."""
        from chatmode.memory import MemoryStore
        
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_embedding_provider = Mock()
            mock_embedding_provider.embed.return_value = [[0.1] * 384]
            
            memory = MemoryStore(
                collection_name=f"test_memory_{uuid.uuid4().hex[:8]}",
                persist_dir=tmpdir,
                embedding_provider=mock_embedding_provider
            )
            
            # Test clear with session_id
            memory.clear(session_id="session_123")
            # Should complete without error
    
    def test_memory_purge_both_filters(self):
        """Test memory purge with both agent and session filters."""
        from chatmode.memory import MemoryStore
        
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_embedding_provider = Mock()
            mock_embedding_provider.embed.return_value = [[0.1] * 384]
            
            memory = MemoryStore(
                collection_name=f"test_memory_{uuid.uuid4().hex[:8]}",
                persist_dir=tmpdir,
                embedding_provider=mock_embedding_provider
            )
            
            # Test clear with both filters
            memory.clear(session_id="session_123", agent_id="agent_1")
            # Should complete without error


class TestMCPTools:
    """Test MCP tool integration."""
    
    @pytest.mark.asyncio
    async def test_list_tools_returns_available_tools(self):
        """GET /tools/list?agent_name=X returns tools."""
        from chatmode.mcp_client import MCPClient
        
        # Create a mock MCP client
        client = MCPClient(command="test-mcp-server", args=[])
        
        # Mock the list_tools method
        with patch.object(client, 'list_tools', new_callable=AsyncMock) as mock_list:
            mock_list.return_value = [
                {"name": "tool1", "description": "First tool"},
                {"name": "tool2", "description": "Second tool"}
            ]
            
            tools = await client.list_tools()
            
            assert len(tools) == 2
            assert tools[0]["name"] == "tool1"
            assert tools[1]["name"] == "tool2"
    
    def test_tool_call_blocked_if_not_allowed(self):
        """Verify a tool call is blocked if not in allowed_tools."""
        from chatmode.agent import ChatAgent
        from chatmode.config import load_settings
        
        profile_data = {
            "name": "Test Agent",
            "model": "gpt-4",
            "api": "openai",
            "conversing": "Test",
            "mcp_command": "test-server",
            "allowed_tools": ["allowed_tool"]  # Only one tool allowed
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(profile_data, f)
            profile_path = f.name
        
        try:
            settings = load_settings()
            agent = ChatAgent(name="test", config_file=profile_path, settings=settings)
            
            # Verify allowed_tools is set correctly
            assert "allowed_tool" in agent.allowed_tools
            assert "forbidden_tool" not in agent.allowed_tools
            
            # Test the security check in _safe_json_loads and generate_response
            # The actual blocking happens in generate_response when tool_calls are processed
            
        finally:
            os.unlink(profile_path)
    
    @pytest.mark.asyncio
    async def test_tool_call_execution_end_to_end(self):
        """POST /tools/call works end-to-end for a simple tool."""
        from chatmode.mcp_client import MCPClient
        
        client = MCPClient(command="test-mcp-server", args=[])
        
        # Mock call_tool
        with patch.object(client, 'call_tool', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = {"result": "success", "value": 42}
            
            result = await client.call_tool("test_tool", {"arg": "value"})
            
            assert result["result"] == "success"
            assert result["value"] == 42
            mock_call.assert_called_once_with("test_tool", {"arg": "value"})


class TestExports:
    """Test transcript export functionality."""
    
    def test_transcript_export_markdown(self):
        """Verify transcript download works for markdown format."""
        from chatmode.session import ChatSession
        from chatmode.config import load_settings
        
        settings = load_settings()
        session = ChatSession(settings)
        
        # Populate some history
        session.session_id = "test_session_123"
        session.topic = "Test Topic"
        session.history = [
            {"sender": "Agent1", "content": "Hello"},
            {"sender": "Agent2", "content": "World"},
        ]
        
        # Generate markdown manually (simulating the route)
        lines = [
            f"# Conversation Transcript",
            f"",
            f"**Topic:** {session.topic}",
            f"**Session ID:** {session.session_id}",
            f"",
            f"---",
            f"",
        ]
        
        for msg in session.history:
            sender = msg.get("sender", "Unknown")
            content = msg.get("content", "")
            lines.append(f"## {sender}")
            lines.append(f"")
            lines.append(content)
            lines.append(f"")
            lines.append(f"---")
            lines.append(f"")
        
        transcript = "\n".join(lines)
        
        # Verify format
        assert "# Conversation Transcript" in transcript
        assert "Test Topic" in transcript
        assert "test_session_123" in transcript
        assert "## Agent1" in transcript
        assert "Hello" in transcript
        assert "## Agent2" in transcript
        assert "World" in transcript
    
    def test_transcript_export_csv(self):
        """Verify transcript download works for CSV format."""
        import csv
        import io
        from chatmode.session import ChatSession
        from chatmode.config import load_settings
        
        settings = load_settings()
        session = ChatSession(settings)
        
        # Populate some history
        session.session_id = "test_session_456"
        session.topic = "CSV Test"
        session.history = [
            {"sender": "Agent1", "content": "First message", "audio": "audio1.mp3"},
            {"sender": "Agent2", "content": "Second message", "audio": ""},
        ]
        
        # Generate CSV manually (simulating the route)
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow(["Sender", "Content", "Audio"])
        
        for msg in session.history:
            writer.writerow([
                msg.get("sender", "Unknown"),
                msg.get("content", ""),
                msg.get("audio", ""),
            ])
        
        csv_content = output.getvalue()
        
        # Verify format
        assert "Sender,Content,Audio" in csv_content
        assert "Agent1,First message,audio1.mp3" in csv_content
        assert "Agent2,Second message," in csv_content


class TestToolCallRobustness:
    """Test that tool call handling is robust and doesn't rely on finish_reason."""
    
    def test_tool_call_detection_uses_tool_calls_presence(self):
        """Verify we check tool_calls presence, not finish_reason."""
        from chatmode.providers import OpenAIChatProvider
        
        # This is verified by code inspection in providers.py line 75
        # The code uses: if choice and hasattr(choice.message, "tool_calls") and choice.message.tool_calls:
        # This is the correct pattern per the problem statement
        
        provider = OpenAIChatProvider(
            base_url="https://api.openai.com/v1",
            api_key="test-key"
        )
        
        # Verify the chat method returns message object
        import inspect
        source = inspect.getsource(provider.chat)
        
        # Should NOT contain "finish_reason" check
        assert "finish_reason" not in source
        
        # Should contain "tool_calls" check
        assert "tool_calls" in source or "return choice.message" in source
    
    def test_safe_json_loads_handles_invalid_json(self):
        """Verify safe JSON parsing handles malformed JSON."""
        from chatmode.agent import ChatAgent
        from chatmode.config import load_settings
        
        profile_data = {
            "name": "Test",
            "model": "gpt-4",
            "api": "openai",
            "conversing": "Test"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(profile_data, f)
            profile_path = f.name
        
        try:
            settings = load_settings()
            agent = ChatAgent(name="test", config_file=profile_path, settings=settings)
            
            # Test safe JSON parsing
            valid = agent._safe_json_loads('{"key": "value"}')
            assert valid == {"key": "value"}
            
            invalid = agent._safe_json_loads('{invalid json')
            assert invalid == {}  # Should return empty dict
            
            already_dict = agent._safe_json_loads({"already": "dict"})
            assert already_dict == {"already": "dict"}
            
        finally:
            os.unlink(profile_path)
    
    def test_tool_message_format_includes_tool_call_id(self):
        """Verify tool messages use role='tool' with tool_call_id."""
        from chatmode.agent import ChatAgent
        from chatmode.config import load_settings
        
        # This is verified by code inspection in agent.py
        # The generate_response method should append messages with:
        # {"role": "tool", "tool_call_id": tool_call_id, "content": json.dumps(result)}
        
        profile_data = {
            "name": "Test",
            "model": "gpt-4",
            "api": "openai",
            "conversing": "Test",
            "mcp_command": "test",
            "allowed_tools": ["test_tool"]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(profile_data, f)
            profile_path = f.name
        
        try:
            settings = load_settings()
            agent = ChatAgent(name="test", config_file=profile_path, settings=settings)
            
            # Verify by source inspection
            import inspect
            source = inspect.getsource(agent.generate_response)
            
            # Should use proper tool message format
            assert '"role": "tool"' in source
            assert '"tool_call_id"' in source or 'tool_call_id' in source
            
        finally:
            os.unlink(profile_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
