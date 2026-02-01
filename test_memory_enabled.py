#!/usr/bin/env python3
"""
Test memory-enabled agents with embedder configuration.
"""

import sys
import os
import json

sys.path.insert(0, ".")

from chatmode.config import load_settings
from crewai_agent import load_agents_from_config
from debate_crew import DebateCrew


def test_memory_enabled():
    """Load agents with memory enabled and run one debate round."""
    settings = load_settings()
    print(f"Embedding provider: {settings.embedding_provider}")
    print(f"Embedding model: {settings.embedding_model}")

    # Load agents (use test config with 3 agents)
    config_path = "agent_config.json"
    if not os.path.exists(config_path):
        print(f"Config file not found: {config_path}")
        return False

    # Temporarily modify agent config to enable memory in profiles
    with open(config_path, "r") as f:
        config = json.load(f)

    # Enable memory for each agent via crewai config
    for agent_conf in config.get("agents", []):
        profile_path = agent_conf["file"]
        with open(profile_path, "r") as pf:
            profile = json.load(pf)
        if "crewai" not in profile:
            profile["crewai"] = {}
        profile["crewai"]["memory"] = True
        # Write back temporary
        with open(profile_path + ".tmp", "w") as pf:
            json.dump(profile, pf, indent=2)
        agent_conf["file"] = profile_path + ".tmp"

    # Write temporary config
    temp_config = "agent_config_memory_test.json"
    with open(temp_config, "w") as f:
        json.dump(config, f, indent=2)

    try:
        print("Loading agents with memory enabled...")
        agents = load_agents_from_config(temp_config, settings)
        print(f"Loaded {len(agents)} agents")

        # Check agent memory settings
        for agent in agents:
            print(f"  {agent.role}: memory={agent.memory}")

        # Create debate crew
        debate = DebateCrew(
            agents=agents,
            settings=settings,
            on_response=lambda sender, msg: print(f"[{sender}] {msg[:80]}..."),
        )

        topic = "Test topic: The future of AI"
        print(f"\nRunning one debate round on: {topic}")

        # Run one round
        new_messages = debate.run_round(
            topic=topic, conversation_history=[], round_num=1
        )

        print(f"\nGenerated {len(new_messages)} messages")
        for msg in new_messages:
            print(f"  {msg['sender']}: {msg['content'][:100]}...")

        # Clean up temporary files
        for agent_conf in config.get("agents", []):
            if os.path.exists(agent_conf["file"]):
                os.remove(agent_conf["file"])
        os.remove(temp_config)

        return True
    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()

        # Clean up on error
        for agent_conf in config.get("agents", []):
            if os.path.exists(agent_conf["file"]):
                os.remove(agent_conf["file"])
        if os.path.exists(temp_config):
            os.remove(temp_config)
        return False


if __name__ == "__main__":
    print("=== Testing Memory-Enabled Agents ===\n")
    print("Note: Ensure embedding model is pulled in Ollama:")
    print("  ollama pull nomic-embed-text")
    print()

    success = test_memory_enabled()

    if success:
        print("\n✅ Memory-enabled test passed!")
        sys.exit(0)
    else:
        print("\n❌ Memory-enabled test failed")
        sys.exit(1)
