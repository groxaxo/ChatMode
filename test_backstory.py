import sys

sys.path.insert(0, ".")
from chatmode.config import load_settings
from crewai_agent import load_agents_from_config
import os
import json

settings = load_settings()
config_path = os.path.join(os.path.dirname(__file__), "agent_config.json")
agents = load_agents_from_config(config_path, settings)
agent = agents[0]

print("Backstory:")
print(repr(agent.backstory))
print("\n---")

# Load profile directly
with open("profiles/sunny.json", "r") as f:
    profile = json.load(f)
print("Original conversing:")
print(repr(profile.get("conversing", "")))
