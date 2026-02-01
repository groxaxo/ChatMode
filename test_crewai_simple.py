import sys

sys.path.insert(0, ".")
from crewai import Agent, Task, Crew
from chatmode.config import load_settings
from chatmode.llm_config import create_llm_from_profile
import json

settings = load_settings()
print("Settings loaded")

# Load sunny profile
with open("profiles/sunny.json", "r") as f:
    profile = json.load(f)

llm = create_llm_from_profile(profile, settings)
print(f"LLM: {llm.model}, base_url: {llm.base_url}")

# Create a simple agent
agent = Agent(
    role="Test Agent",
    goal="Test the CrewAI system",
    backstory="A test agent",
    llm=llm,
    verbose=True,
)

# Create a simple task
task = Task(description="Say hello world", agent=agent, expected_output="A greeting")

# Create crew
crew = Crew(agents=[agent], tasks=[task], verbose=True)

print("Kicking off crew...")
try:
    result = crew.kickoff()
    print(f"Result: {result}")
except Exception as e:
    print(f"Error: {e}")
    import traceback

    traceback.print_exc()
