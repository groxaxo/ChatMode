import sys

sys.path.insert(0, ".")
from chatmode.config import load_settings
from crewai_agent import load_agents_from_config
import os

settings = load_settings()
config_path = os.path.join(os.path.dirname(__file__), "agent_config.json")
agents = load_agents_from_config(config_path, settings)
original_agent = agents[0]

print("Original agent parameters:")
print(f"  role: {original_agent.role}")
print(f"  goal: {original_agent.goal}")
print(f"  backstory length: {len(original_agent.backstory)}")
print(f"  max_iter: {original_agent.max_iter}")
print(f"  memory: {original_agent.memory}")
print(f"  allow_delegation: {original_agent.allow_delegation}")
print(f"  respect_context_window: {original_agent.respect_context_window}")

# Create a copy with minimal parameters
from crewai import Agent

simple_agent = Agent(
    role=original_agent.role,
    goal=original_agent.goal,
    backstory=original_agent.backstory,
    llm=original_agent.llm,
    verbose=True,
    # Omit extra parameters
)

print("\nSimple agent parameters:")
print(f"  max_iter: {simple_agent.max_iter}")
print(f"  memory: {simple_agent.memory}")

# Test both agents with simple task
from crewai import Task, Crew, Process

for agent, name in [(original_agent, "original"), (simple_agent, "simple")]:
    print(f"\n--- Testing {name} agent ---")
    task = Task(
        description="Say hello world", agent=agent, expected_output="A greeting"
    )

    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        memory=False,
        verbose=True,
    )

    try:
        result = crew.kickoff()
        print(f"Success: {result}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
