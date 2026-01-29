"""
Session management for ChatMode with CrewAI integration.

Provides thread-safe session control for the web admin interface.
"""

import json
import logging
import os
import threading
import time
import uuid
from datetime import datetime
from typing import List, Dict, Optional

from crewai import Agent

from config import Settings
from crewai_agent import ChatModeAgent, load_agents_from_config
from debate_crew import DebateCrew, TopicGenerator
from tts import TTSClient

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(handler)


def load_agents(settings: Settings) -> List[Agent]:
    """
    Load all agents from configuration using CrewAI.
    
    Args:
        settings: Global application settings
        
    Returns:
        List of CrewAI Agent instances
    """
    config_path = os.path.join(os.path.dirname(__file__), "agent_config.json")
    return load_agents_from_config(config_path, settings)


class ChatSession:
    """
    Thread-safe chat session manager using CrewAI.
    
    Manages the lifecycle of multi-agent debate sessions,
    including start, stop, resume, and message injection.
    """
    
    def __init__(self, settings: Settings):
        """
        Initialize the chat session.
        
        Args:
            settings: Global application settings
        """
        self.settings = settings
        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._stop_requested = False
        
        self.session_id: str = ""
        self.topic: str = ""
        self.admin_id: str = "admin"
        self.history: List[Dict[str, str]] = []
        self.last_messages: List[Dict[str, str]] = []
        self.agents: List[Agent] = []
        self.debate_crew: Optional[DebateCrew] = None
        self.created_at: Optional[str] = None
        
        # TTS client (optional)
        self.tts_client: Optional[TTSClient] = None
        if settings.tts_enabled:
            self.tts_client = TTSClient(
                base_url=settings.tts_base_url,
                api_key=settings.tts_api_key or settings.openai_api_key,
                model=settings.tts_model,
                voice=settings.tts_voice,
                output_dir=settings.tts_output_dir,
            )
        
        # Agent-specific TTS voice overrides (loaded from profiles)
        self._agent_voices: Dict[str, Dict[str, str]] = {}

    def start(self, topic: str) -> bool:
        """
        Start a new debate session.
        
        Args:
            topic: The debate topic
            
        Returns:
            True if started successfully, False if already running
        """
        with self._lock:
            if self._running:
                return False
            
            # Generate unique session ID
            self.session_id = str(uuid.uuid4())
            self.created_at = datetime.utcnow().isoformat()
            self.topic = topic
            self.history = []
            self.last_messages = []
            self._stop_requested = False
            
            logger.info(f"Starting session {self.session_id} with topic: {topic}")
            
            # Load agents using CrewAI
            self.agents = load_agents(self.settings)
            
            if len(self.agents) < 2:
                raise RuntimeError("Need at least two agents to start")
            
            # Load TTS voice overrides from profiles
            self._load_agent_voices()
            
            # Create debate crew with response callback
            self.debate_crew = DebateCrew(
                agents=self.agents,
                settings=self.settings,
                on_response=self._on_agent_response
            )
            
            self._running = True
            self._thread = threading.Thread(target=self._run_loop, daemon=True)
            self._thread.start()
            return True

    def resume(self) -> bool:
        """
        Resume a paused session.
        
        Returns:
            True if resumed successfully, False otherwise
        """
        with self._lock:
            if self._running:
                return False
            if not self.topic:
                return False
            
            # Reload agents if needed
            if not self.agents:
                self.agents = load_agents(self.settings)
                self._load_agent_voices()
            
            # Recreate debate crew
            self.debate_crew = DebateCrew(
                agents=self.agents,
                settings=self.settings,
                on_response=self._on_agent_response
            )
            
            self._stop_requested = False
            self._running = True
            self._thread = threading.Thread(target=self._run_loop, daemon=True)
            self._thread.start()
            return True

    def stop(self) -> None:
        """Stop the current session."""
        with self._lock:
            self._stop_requested = True
            self._running = False

    def is_running(self) -> bool:
        """Check if the session is currently running."""
        with self._lock:
            return self._running

    def inject_message(self, sender: str, content: str) -> None:
        """
        Inject an admin message into the conversation.
        
        Args:
            sender: Message sender name
            content: Message content
        """
        with self._lock:
            entry = {"sender": sender, "content": content}
            self.history.append(entry)
            self.last_messages.append(entry)
            if len(self.last_messages) > 8:
                self.last_messages.pop(0)

    def clear_memory(self) -> None:
        """Clear conversation history."""
        with self._lock:
            self.history = []
            self.last_messages = []

    def _run_loop(self) -> None:
        """Main debate loop running in background thread."""
        round_num = 1
        
        while not self._stop_requested:
            # Run one round of debate
            with self._lock:
                current_history = self.history.copy()
            
            try:
                new_messages = self.debate_crew.run_round(
                    topic=self.topic,
                    conversation_history=current_history,
                    round_num=round_num
                )
                
                # Messages are added via callback, but ensure history sync
                with self._lock:
                    if not self._stop_requested:
                        # Trim history if needed
                        while len(self.history) > self.settings.history_max_messages:
                            self.history.pop(0)
                
            except Exception as e:
                print(f"Error in debate round {round_num}: {e}")
            
            # Delay between rounds
            for _ in range(int(self.settings.sleep_seconds * 10)):
                if self._stop_requested:
                    break
                time.sleep(0.1)
            
            round_num += 1
        
        with self._lock:
            self._running = False

    def _on_agent_response(self, agent_name: str, response: str) -> None:
        """
        Callback for each agent response.
        
        Handles message logging and TTS generation.
        
        Args:
            agent_name: Name of the responding agent
            response: The agent's response text
        """
        audio_path = None
        audio_error = None
        
        logger.info(f"[{self.session_id}] Agent '{agent_name}' responded: {response[:80]}...")
        
        # Generate TTS if enabled
        if self.tts_client and response:
            try:
                voice_config = self._agent_voices.get(agent_name, {})
                audio_path = self.tts_client.speak(
                    text=response,
                    model=voice_config.get("model"),
                    voice=voice_config.get("voice"),
                    filename_prefix=agent_name.lower().replace(" ", "_")
                )
                logger.info(f"[{self.session_id}] TTS generated for '{agent_name}': {audio_path}")
            except Exception as e:
                audio_error = str(e)
                logger.error(f"[{self.session_id}] TTS error for {agent_name}: {e}")
        
        # Add to session history
        with self._lock:
            entry = {
                "sender": agent_name,
                "content": response,
                "audio": audio_path,
                "audio_error": audio_error,
                "timestamp": datetime.utcnow().isoformat(),
                "session_id": self.session_id,
            }
            self.history.append(entry)
            self.last_messages.append(entry)
            
            if len(self.last_messages) > 8:
                self.last_messages.pop(0)

    def _load_agent_voices(self) -> None:
        """Load TTS voice configurations from agent profiles."""
        config_path = os.path.join(os.path.dirname(__file__), "agent_config.json")
        
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
            
            for agent_conf in config.get("agents", []):
                with open(agent_conf["file"], "r") as f:
                    profile = json.load(f)
                
                agent_name = profile.get("name", agent_conf.get("name", ""))
                speak_model = profile.get("speak_model", {})
                
                if speak_model:
                    self._agent_voices[agent_name] = {
                        "model": speak_model.get("model"),
                        "voice": speak_model.get("voice"),
                    }
        except Exception as e:
            print(f"Warning: Could not load agent voices: {e}")
