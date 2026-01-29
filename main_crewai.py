"""
ChatMode - Multi-Agent Debate System with CrewAI

A Python multi-agent chat interface using CrewAI for autonomous conversations,
featuring long-term memory via embeddings, optional TTS, and a FastAPI admin UI.
"""

import json
import os
import time

from config import load_settings
from crewai_agent import load_agents_from_config
from debate_crew import DebateCrew, TopicGenerator


def load_config(path: str) -> dict:
    """Load JSON configuration file."""
    with open(path, "r") as f:
        return json.load(f)


def main():
    """Main entry point for CLI-based debate."""
    settings = load_settings()
    print("Initializing ChatMode with CrewAI...")

    # 1. Get or generate topic
    topic = os.getenv("ADMIN_TOPIC", "").strip()
    if not topic:
        topic = input("Admin topic (leave blank to auto-generate): ").strip()

    if not topic and settings.admin_use_llm:
        print("Generating topic...")
        generator = TopicGenerator(settings)
        topic = generator.generate_topic()

    if not topic:
        topic = "Is artificial consciousness possible?"

    print("\n" + "=" * 60)
    print(f"TOPIC: {topic}")
    print("=" * 60 + "\n")

    # 2. Load agents using CrewAI
    config_path = os.path.join(os.path.dirname(__file__), "agent_config.json")
    agents = load_agents_from_config(config_path, settings)

    if len(agents) < 2:
        print("Need at least two agents to start. Exiting.")
        return

    print(f"\nLoaded {len(agents)} agents:")
    for agent in agents:
        print(f"  • {agent.role}")

    # 3. Create debate crew
    def on_response(agent_name: str, response: str) -> None:
        """Callback for each agent response."""
        print(f"\n[{agent_name}]:\n{response}\n")
        print(f"(Waiting {settings.sleep_seconds}s...)")

    debate_crew = DebateCrew(
        agents=agents,
        settings=settings,
        on_response=on_response
    )

    # 4. Run continuous debate
    print("\n--- Starting Debate ---\n")
    
    try:
        conversation_history = []
        round_num = 1
        
        while True:
            print(f"\n{'='*20} Round {round_num} {'='*20}")
            
            # Run one round
            new_messages = debate_crew.run_round(
                topic=topic,
                conversation_history=conversation_history,
                round_num=round_num
            )
            
            # Update history
            conversation_history.extend(new_messages)
            
            # Trim history if needed
            max_history = settings.history_max_messages
            if len(conversation_history) > max_history:
                conversation_history = conversation_history[-max_history:]
            
            # Delay between rounds
            time.sleep(settings.sleep_seconds)
            round_num += 1
            
    except KeyboardInterrupt:
        print("\n\n--- Debate ended by user ---")
        print(f"Total messages: {len(conversation_history)}")


if __name__ == "__main__":
    main()
