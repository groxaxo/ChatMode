import sys

sys.path.insert(0, ".")
from crewai import Agent, Task, Crew, Process
from chatmode.config import load_settings
from chatmode.llm_config import create_llm_from_profile
import json

settings = load_settings()
with open("profiles/sunny.json", "r") as f:
    profile = json.load(f)

llm = create_llm_from_profile(profile, settings)
agent = Agent(role="Test", goal="Test", backstory="Test", llm=llm, verbose=True)
task = Task(description="Say hello", agent=agent, expected_output="Hi")
crew = Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=True)

result = crew.kickoff()
print(f"Result type: {type(result)}")
print(f"Result: {result}")
print(f"Dir: {[attr for attr in dir(result) if not attr.startswith('_')]}")
if hasattr(result, "raw"):
    print(f"Result.raw: {result.raw}")
    print(f"Raw type: {type(result.raw)}")
