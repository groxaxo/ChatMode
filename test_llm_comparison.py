import sys

sys.path.insert(0, ".")
from chatmode.config import load_settings
from crewai_agent import load_agents_from_config, ChatModeAgent
from chatmode.llm_config import create_llm_from_profile
import json

settings = load_settings()
config_path = "agent_config.json"
agents = load_agents_from_config(config_path, settings)
agent1 = agents[0]

print("Agent LLM:")
print(f"  model: {agent1.llm.model}")
print(f"  base_url: {agent1.llm.base_url}")
print(f"  temperature: {agent1.llm.temperature}")
print(f"  api_key: {agent1.llm.api_key}")

# Create LLM directly
with open("profiles/sunny.json", "r") as f:
    profile = json.load(f)
llm2 = create_llm_from_profile(profile, settings)
print("\nDirect LLM:")
print(f"  model: {llm2.model}")
print(f"  base_url: {llm2.base_url}")
print(f"  temperature: {llm2.temperature}")
print(f"  api_key: {llm2.api_key}")

# Compare
print("\nAre they same?")
print(f"  model same: {agent1.llm.model == llm2.model}")
print(f"  base_url same: {agent1.llm.base_url == llm2.base_url}")
print(f"  temperature same: {agent1.llm.temperature == llm2.temperature}")

# Check LLM's __dict__
print(
    "\nAgent LLM attributes:",
    [k for k in agent1.llm.__dict__.keys() if not k.startswith("_")],
)
print(
    "Direct LLM attributes:", [k for k in llm2.__dict__.keys() if not k.startswith("_")]
)
