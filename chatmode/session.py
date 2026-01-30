import json
import os
import threading
import time
from typing import List, Dict, Optional

from .agent import ChatAgent
from .config import Settings


def load_agents(settings: Settings) -> List[ChatAgent]:
    config_path = os.path.join(os.path.dirname(__file__), "agent_config.json")
    with open(config_path, "r") as f:
        config = json.load(f)

    agents: List[ChatAgent] = []
    for agent_conf in config.get("agents", []):
        agent = ChatAgent(
            name=agent_conf.get("name", "agent"),
            config_file=agent_conf["file"],
            settings=settings,
        )
        agents.append(agent)
    return agents


class ChatSession:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self.topic: str = ""
        self.history: List[Dict[str, str]] = []
        self.last_messages: List[Dict[str, str]] = []
        self.agents: List[ChatAgent] = []

    def start(self, topic: str) -> bool:
        with self._lock:
            if self._running:
                return False
            self.topic = topic
            self.history = []
            self.last_messages = []
            self.agents = load_agents(self.settings)
            if len(self.agents) < 2:
                raise RuntimeError("Need at least two agents to start")
            self._running = True
            self._thread = threading.Thread(target=self._run_loop, daemon=True)
            self._thread.start()
            return True

    def resume(self) -> bool:
        with self._lock:
            if self._running:
                return False
            if not self.topic:
                return False  # Nothing to resume
            # Don't clear history/last_messages
            # Reload agents to ensure fresh state if needed? Alternatively keep existing agents if stored.
            # Here we reload agents but they might lose short-term memory if it wasn't externalized.
            # "memory.py" uses chroma, so long-term is safe. Context is in self.history.
            # We need to make sure agents are initialized.
            if not self.agents:
                self.agents = load_agents(self.settings)

            self._running = True
            self._thread = threading.Thread(target=self._run_loop, daemon=True)
            self._thread.start()
            return True

    def stop(self) -> None:
        with self._lock:
            self._running = False

    def is_running(self) -> bool:
        with self._lock:
            return self._running

    def inject_message(self, sender: str, content: str):
        # Admin injection
        # We append to history so agents see it in context.
        with self._lock:
            entry = {"sender": sender, "content": content}
            self.history.append(entry)
            self.last_messages.append(entry)
            if len(self.last_messages) > 8:
                self.last_messages.pop(0)

    def _run_loop(self) -> None:
        round_num = 1
        while self.is_running():
            for agent in list(self.agents):
                if not self.is_running():
                    break
                response, audio_path = agent.generate_response(self.topic, self.history)
                entry = {
                    "sender": agent.full_name,
                    "content": response,
                    "audio": audio_path,
                }
                self.history.append(entry)
                self.last_messages.append(entry)
                if len(self.last_messages) > 8:
                    self.last_messages.pop(0)

                for memory_agent in self.agents:
                    memory_agent.remember_message(agent.full_name, response)

                if len(self.history) > self.settings.history_max_messages:
                    self.history.pop(0)

                time.sleep(self.settings.sleep_seconds)
            round_num += 1

    def clear_memory(self):
        with self._lock:
            self.history = []
            self.last_messages = []
