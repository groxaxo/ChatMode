import sys

sys.path.insert(0, ".")
from chatmode.config import load_settings
from session_crewai import ChatSession
import time
import threading

settings = load_settings()
session = ChatSession(settings)

print("Starting session...")
if session.start("Test topic"):
    print("Session started")
    time.sleep(2)
    print(f"Is running: {session.is_running()}")
    print(f"Topic: {session.topic}")
    print(f"Agents loaded: {len(session.agents)}")
    time.sleep(5)
    session.stop()
    print("Session stopped")
else:
    print("Failed to start session")
