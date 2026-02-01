import sys

sys.path.insert(0, ".")
from chatmode.config import load_settings
from crewai_agent import load_agents_from_config
import os

settings = load_settings()
config_path = os.path.join(os.path.dirname(__file__), "agent_config.json")
agents = load_agents_from_config(config_path, settings)
agent = agents[0]

print(f"Original backstory length: {len(agent.backstory)}")
print(f"First 200 chars: {agent.backstory[:200]}")

# Create a new agent with simplified backstory
from crewai import Agent, LLM

simple_agent = Agent(
    role=agent.role,
    goal=agent.goal,
    backstory="A simple test agent.",
    llm=agent.llm,
    verbose=True,
)

from crewai import Task, Crew, Process

task = Task(
    description="Say hello world", agent=simple_agent, expected_output="A greeting"
)

crew = Crew(
    agents=[simple_agent],
    tasks=[task],
    process=Process.sequential,
    memory=False,
    verbose=True,
)

print("Kicking off crew with simplified agent...")
try:
    result = crew.kickoff()
    print(f"Result: {result}")
except Exception as e:
    print(f"Error: {e}")
    import traceback

    traceback.print_exc()
