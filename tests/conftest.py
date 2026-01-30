"""
Pytest configuration and fixtures for ChatMode tests.

This file provides shared fixtures and configuration for deterministic testing.
"""

import os
import tempfile
import uuid
import pytest
from unittest.mock import Mock


@pytest.fixture
def unique_collection_name():
    """Generate a unique collection name for each test to avoid conflicts."""
    return f"test_collection_{uuid.uuid4().hex[:8]}"


@pytest.fixture
def test_chroma_dir(tmp_path):
    """
    Provide a temporary directory for ChromaDB testing.
    
    This ensures tests are isolated and can run in parallel without conflicts.
    """
    chroma_dir = tmp_path / "chroma_test"
    chroma_dir.mkdir(exist_ok=True)
    return str(chroma_dir)


@pytest.fixture
def test_tts_dir(tmp_path):
    """
    Provide a temporary directory for TTS testing.
    """
    tts_dir = tmp_path / "tts_test"
    tts_dir.mkdir(exist_ok=True)
    return str(tts_dir)


@pytest.fixture
def mock_embedding_provider():
    """Create a mock embedding provider that returns consistent embeddings."""
    provider = Mock()
    # Return consistent 384-dimensional embeddings (common dimension for many models)
    provider.embed.return_value = [[0.1] * 384]
    return provider


@pytest.fixture(autouse=True)
def set_test_env_vars(test_chroma_dir, test_tts_dir):
    """
    Automatically set environment variables for tests.
    
    This fixture runs automatically for all tests (autouse=True).
    """
    original_env = os.environ.copy()
    
    # Set test environment variables
    os.environ['CHROMA_DIR'] = test_chroma_dir
    os.environ['TTS_OUTPUT_DIR'] = test_tts_dir
    os.environ['OPENAI_API_KEY'] = 'test-key-fixture'
    
    yield
    
    # Restore original environment after test
    os.environ.clear()
    os.environ.update(original_env)
