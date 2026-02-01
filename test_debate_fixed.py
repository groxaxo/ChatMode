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

from crewai import Agent, Crew, Task, Process

# Simple test with first agent
agent = agents[0]
print(f"Testing with agent: {agent.role}")

# Create a simple task
task = Task(description="Say hello world", agent=agent, expected_output="A greeting")

# Create crew WITHOUT embedder config
crew = Crew(
    agents=[agent],
    tasks=[task],
    process=Process.sequential,
    memory=False,  # Disable memory
    verbose=True,
)

print("Kicking off crew...")
try:
    result = crew.kickoff()
    print(f"Result: {result}")
    # Check type
    print(f"Result type: {type(result)}")
    print(f"Has attr 'raw': {hasattr(result, 'raw')}")
    if hasattr(result, "raw"):
        print(f"Result.raw: {result.raw}")
except Exception as e:
    print(f"Error: {e}")
    import traceback

    traceback.print_exc()
