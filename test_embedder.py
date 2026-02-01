#!/usr/bin/env python3
"""
Test embedder configuration for CrewAI memory.
"""

import sys
import os

sys.path.insert(0, ".")

from chatmode.config import load_settings
from chatmode.llm_config import create_embedder_config
from crewai import Agent, Crew, Task, Process
import traceback


def test_embedder_config():
    """Test that embedder config is created correctly and Crew accepts it."""
    settings = load_settings()
    print(f"Embedding provider: {settings.embedding_provider}")
    print(f"Embedding model: {settings.embedding_model}")
    print(f"Embedding base URL: {settings.embedding_base_url}")

    # Create embedder config
    embedder_config = create_embedder_config(settings)
    print(f"Generated embedder config: {embedder_config}")

    # Verify structure
    assert "provider" in embedder_config, "Missing provider key"
    assert "config" in embedder_config, "Missing config key"
    assert "model_name" in embedder_config["config"], "Missing model_name in config"

    if embedder_config["provider"] == "ollama":
        assert "url" in embedder_config["config"], "Missing url in ollama config"
        print(f"Ollama URL: {embedder_config['config']['url']}")
    else:
        assert "api_key" in embedder_config["config"], (
            "Missing api_key in openai config"
        )

    print("✓ Embedder config structure OK")

    # Now test with a Crew (minimal)
    # Create a simple agent with memory enabled
    # Use a dummy LLM to avoid actual API calls
    from crewai import LLM

    dummy_llm = LLM(
        model="gpt-3.5-turbo",
        temperature=0.0,
        max_tokens=10,
    )

    agent = Agent(
        role="Tester",
        goal="Test embedder functionality",
        backstory="A test agent",
        llm=dummy_llm,
        memory=True,  # Enable memory
        verbose=True,
    )

    task = Task(
        description="Say 'test'",
        agent=agent,
        expected_output="The word 'test'",
    )

    print("\nCreating Crew with embedder config...")
    try:
        crew = Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential,
            memory=True,
            embedder=embedder_config,
            verbose=True,
        )
        print("✓ Crew created successfully with embedder config")

        # Attempt kickoff (may fail due to dummy LLM, but we just want to see if embedder is accepted)
        print("Attempting kickoff (may fail due to dummy LLM)...")
        result = crew.kickoff()
        print(f"Result: {result}")
        return True
    except Exception as e:
        print(f"✗ Error creating or running crew with embedder: {e}")
        traceback.print_exc()
        return False


def test_memory_without_embedder():
    """Test that memory=False works (baseline)."""
    from crewai import LLM

    dummy_llm = LLM(
        model="gpt-3.5-turbo",
        temperature=0.0,
        max_tokens=10,
    )

    agent = Agent(
        role="Tester",
        goal="Test memory disabled",
        backstory="A test agent",
        llm=dummy_llm,
        memory=False,
        verbose=True,
    )

    task = Task(
        description="Say 'test'",
        agent=agent,
        expected_output="The word 'test'",
    )

    print("\nTesting Crew without memory...")
    try:
        crew = Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential,
            memory=False,
            verbose=True,
        )
        print("✓ Crew created successfully without memory")
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=== Testing Embedder Configuration ===\n")
    success = True
    success = test_embedder_config() and success
    success = test_memory_without_embedder() and success

    if success:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed")
        sys.exit(1)
