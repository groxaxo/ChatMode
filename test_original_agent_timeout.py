import sys

sys.path.insert(0, ".")
from chatmode.config import load_settings
from crewai_agent import load_agents_from_config
import os
import signal
import threading


class TimeoutException(Exception):
    pass


def timeout_handler(signum, frame):
    raise TimeoutException()


signal.signal(signal.SIGALRM, timeout_handler)

settings = load_settings()
config_path = os.path.join(os.path.dirname(__file__), "agent_config.json")
agents = load_agents_from_config(config_path, settings)
agent = agents[0]

from crewai import Task, Crew, Process

task = Task(description="Say hello world", agent=agent, expected_output="A greeting")

crew = Crew(
    agents=[agent], tasks=[task], process=Process.sequential, memory=False, verbose=True
)

print("Starting crew with 30 second timeout...")
signal.alarm(30)
try:
    result = crew.kickoff()
    signal.alarm(0)
    print(f"Success: {result}")
except TimeoutException:
    print("Timeout! Crew execution hung.")
except Exception as e:
    signal.alarm(0)
    print(f"Error: {e}")
    import traceback

    traceback.print_exc()
