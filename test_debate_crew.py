import sys

sys.path.insert(0, ".")
from chatmode.config import load_settings
from crewai_agent import load_agents_from_config
import os

settings = load_settings()
config_path = os.path.join(os.path.dirname(__file__), "agent_config.json")
print(f"Loading agents from {config_path}")
agents = load_agents_from_config(config_path, settings)
print(f"Loaded {len(agents)} agents")

from debate_crew import DebateCrew


def on_response(agent_name, response):
    print(f"Callback: {agent_name}: {response[:50]}...")


crew = DebateCrew(agents=agents, settings=settings, on_response=on_response)

print("Running one round...")
try:
    new_messages = crew.run_round(
        topic="Test topic", conversation_history=[], round_num=1
    )
    print(f"Got {len(new_messages)} messages")
    for msg in new_messages:
        print(f"  {msg['sender']}: {msg['content'][:80]}...")
except Exception as e:
    print(f"Error: {e}")
    import traceback

    traceback.print_exc()
