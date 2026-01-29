"""
ChatMode Backend Tests.

Tests for session management, memory, and TTS pipeline.
Run with: pytest tests/test_chatmode.py -v
"""

import json
import os
import sys
import tempfile
import pytest
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Settings
from memory import MemoryStore
from providers import OllamaChatProvider, OllamaEmbeddingProvider, OpenAIChatProvider
from tts import TTSClient, normalize_text_for_tts


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_settings():
    """Create mock settings for testing."""
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
        chroma_dir="/tmp/chroma_test",
        max_context_tokens=32000,
        max_output_tokens=512,
        memory_top_k=5,
        history_max_messages=20,
        temperature=0.9,
        sleep_seconds=0.1,
        admin_use_llm=False,
        verbose=False,
    )


@pytest.fixture
def mock_embedding_provider():
    """Create a mock embedding provider."""
    provider = Mock()
    # Return consistent 384-dimensional embeddings
    provider.embed.return_value = [[0.1] * 384]
    return provider


# ============================================================================
# TTS Tests
# ============================================================================

class TestTTSNormalization:
    """Test TTS text normalization."""
    
    def test_removes_markdown_bold(self):
        text = "This is **bold** text"
        assert normalize_text_for_tts(text) == "This is bold text"
    
    def test_removes_markdown_italic(self):
        text = "This is *italic* text"
        assert normalize_text_for_tts(text) == "This is italic text"
    
    def test_removes_markdown_links(self):
        text = "Check [this link](http://example.com) out"
        assert normalize_text_for_tts(text) == "Check this link out"
    
    def test_collapses_whitespace(self):
        text = "Multiple   spaces\n\nand newlines"
        assert normalize_text_for_tts(text) == "Multiple spaces and newlines"
    
    def test_handles_empty_string(self):
        assert normalize_text_for_tts("") == ""
    
    def test_handles_complex_markdown(self):
        text = "**Bold** and *italic* with [link](url)"
        result = normalize_text_for_tts(text)
        assert "**" not in result
        assert "*" not in result
        assert "[" not in result


# ============================================================================
# Memory Tests
# ============================================================================

class TestMemoryStore:
    """Test MemoryStore functionality."""
    
    def test_memory_initialization(self, mock_embedding_provider, tmp_path):
        """Test memory store can be initialized."""
        store = MemoryStore(
            collection_name="test_memory",
            persist_dir=str(tmp_path),
            embedding_provider=mock_embedding_provider,
        )
        assert store.collection_name == "test_memory"
        assert store.count() == 0
    
    def test_memory_add_with_metadata(self, mock_embedding_provider, tmp_path):
        """Test adding memory with enriched metadata."""
        store = MemoryStore(
            collection_name="test_add",
            persist_dir=str(tmp_path),
            embedding_provider=mock_embedding_provider,
        )
        
        store.add(
            text="Test message content",
            metadata={"sender": "Agent1"},
            session_id="session-123",
            agent_id="agent-1",
            topic="Test topic",
            tags=["important", "test"],
        )
        
        assert store.count() == 1
        mock_embedding_provider.embed.assert_called()
    
    def test_memory_ignores_empty_text(self, mock_embedding_provider, tmp_path):
        """Test that empty text is not stored."""
        store = MemoryStore(
            collection_name="test_empty",
            persist_dir=str(tmp_path),
            embedding_provider=mock_embedding_provider,
        )
        
        store.add(text="", metadata={"sender": "Agent1"})
        assert store.count() == 0
    
    def test_memory_query(self, mock_embedding_provider, tmp_path):
        """Test memory query returns results."""
        store = MemoryStore(
            collection_name="test_query",
            persist_dir=str(tmp_path),
            embedding_provider=mock_embedding_provider,
        )
        
        store.add(text="First message", metadata={"sender": "Agent1"})
        store.add(text="Second message", metadata={"sender": "Agent2"})
        
        results = store.query("test query", k=5)
        assert len(results) == 2
    
    def test_memory_clear(self, mock_embedding_provider, tmp_path):
        """Test memory can be cleared."""
        store = MemoryStore(
            collection_name="test_clear",
            persist_dir=str(tmp_path),
            embedding_provider=mock_embedding_provider,
        )
        
        store.add(text="Test message", metadata={"sender": "Agent1"})
        assert store.count() == 1
        
        store.clear()
        assert store.count() == 0


# ============================================================================
# Provider Tests
# ============================================================================

class TestOllamaEmbeddingProvider:
    """Test Ollama embedding provider."""
    
    @patch('providers.requests.post')
    def test_embed_uses_new_api_first(self, mock_post):
        """Test that new /api/embed endpoint is tried first."""
        mock_response = Mock()
        mock_response.json.return_value = {"embeddings": [[0.1, 0.2, 0.3]]}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        provider = OllamaEmbeddingProvider(
            base_url="http://localhost:11434",
            model="nomic-embed-text"
        )
        
        result = provider.embed(["test text"])
        
        # Should call new endpoint
        call_url = mock_post.call_args[0][0]
        assert "/api/embed" in call_url
        assert result == [[0.1, 0.2, 0.3]]
    
    @patch('providers.requests.post')
    def test_embed_falls_back_to_legacy(self, mock_post):
        """Test fallback to legacy /api/embeddings endpoint."""
        from requests import RequestException
        
        call_count = [0]
        
        # First call (new API) fails, second succeeds
        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:  # First call to new endpoint
                raise RequestException("Not found")
            # Second call to legacy endpoint
            mock_resp = Mock()
            mock_resp.json.return_value = {"embedding": [0.4, 0.5, 0.6]}
            mock_resp.raise_for_status = Mock()
            return mock_resp
        
        mock_post.side_effect = side_effect
        
        provider = OllamaEmbeddingProvider(
            base_url="http://localhost:11434",
            model="nomic-embed-text"
        )
        
        result = provider.embed(["test text"])
        assert result == [[0.4, 0.5, 0.6]]
        assert call_count[0] == 2  # Verify both endpoints were tried


# ============================================================================
# Session Tests
# ============================================================================

class TestSessionManagement:
    """Test session management functionality."""
    
    def test_session_generates_unique_id(self, mock_settings):
        """Test that sessions get unique IDs."""
        from session_crewai import ChatSession
        
        session = ChatSession(mock_settings)
        
        # Session ID should be empty initially
        assert session.session_id == ""
        
        # After start (mocked), session_id should be set
        with patch.object(session, '_thread'):
            with patch('session_crewai.load_agents', return_value=[Mock(), Mock()]):
                session.start("Test topic")
        
        assert session.session_id != ""
        assert len(session.session_id) == 36  # UUID format
    
    def test_session_stores_topic(self, mock_settings):
        """Test that topic is stored in session."""
        from session_crewai import ChatSession
        
        session = ChatSession(mock_settings)
        
        with patch.object(session, '_thread'):
            with patch('session_crewai.load_agents', return_value=[Mock(), Mock()]):
                session.start("Is AI conscious?")
        
        assert session.topic == "Is AI conscious?"
    
    def test_session_inject_message(self, mock_settings):
        """Test admin can inject messages."""
        from session_crewai import ChatSession
        
        session = ChatSession(mock_settings)
        session.inject_message("Admin", "Please focus on the topic")
        
        assert len(session.history) == 1
        assert session.history[0]["sender"] == "Admin"
        assert session.history[0]["content"] == "Please focus on the topic"
    
    def test_session_clear_memory(self, mock_settings):
        """Test memory clearing."""
        from session_crewai import ChatSession
        
        session = ChatSession(mock_settings)
        session.inject_message("Admin", "Test message")
        assert len(session.history) == 1
        
        session.clear_memory()
        assert len(session.history) == 0
        assert len(session.last_messages) == 0


# ============================================================================
# API Tests
# ============================================================================

class TestWebAPI:
    """Test FastAPI endpoints."""
    
    @pytest.fixture
    def client(self, mock_settings):
        """Create test client."""
        from fastapi.testclient import TestClient
        
        with patch('web_admin_crewai.load_settings', return_value=mock_settings):
            with patch('web_admin_crewai.ChatSession') as MockSession:
                mock_session = Mock()
                mock_session.is_running.return_value = False
                mock_session.topic = ""
                mock_session.session_id = ""
                mock_session.created_at = None
                mock_session.last_messages = []
                MockSession.return_value = mock_session
                
                from web_admin_crewai import app
                yield TestClient(app)
    
    def test_status_endpoint(self, client):
        """Test /status returns correct structure."""
        response = client.get("/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "running" in data
        assert "topic" in data
        assert "session_id" in data
        assert "last_messages" in data
    
    def test_health_endpoint(self, client):
        """Test /health endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["framework"] == "crewai"


# ============================================================================
# Integration Test Skeleton
# ============================================================================

class TestEndToEnd:
    """End-to-end integration tests (require running services)."""
    
    @pytest.mark.skip(reason="Requires running Ollama and TTS services")
    def test_full_debate_flow(self, mock_settings):
        """
        Test complete flow:
        1. Admin sets topic
        2. Agents respond on-topic
        3. Memory stores/retrieves
        4. Audio plays
        """
        # This test should be run manually with services available
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
