"""
Chat session management with per-agent state control and TTS support.

This module provides the ChatSession class which manages multi-agent conversations
with support for:
- Per-agent pause/stop/finish control
- Async generation with cancellation support
- TTS audio generation and delivery
- Turn scheduling based on agent states
"""

import asyncio
import json
import os
import time
import uuid
from typing import List, Dict, Optional, Set, Tuple, Any

from .agent import ChatAgent
from .admin import AdminAgent
from .agent_state import AgentStateManager, AgentState, create_session_state_manager
from .config import Settings
from .content_filter import ContentFilter, create_filter_from_permissions
from .logger_config import get_logger, log_execution_time, log_operation
from .tts_provider import AudioStorage, TTSResult, build_tts_provider

logger = get_logger(__name__)


@log_execution_time(logger)
def load_agents(settings: Settings) -> List[ChatAgent]:
    """Load agents from configuration file."""
    # Look for agent_config.json in project root (parent of chatmode package)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(project_root, "agent_config.json")

    logger.debug(f"📂 Loading agent configuration from: {config_path}")

    with open(config_path, "r") as f:
        config = json.load(f)

    agents: List[ChatAgent] = []
    agent_configs = config.get("agents", [])
    logger.info(f"🔧 Loading {len(agent_configs)} agents from configuration")

    for agent_conf in agent_configs:
        agent_name = agent_conf.get("name", "agent")
        config_file = agent_conf["file"]
        logger.debug(f"🤖 Loading agent: {agent_name} from {config_file}")

        try:
            agent = ChatAgent(
                name=agent_name,
                config_file=config_file,
                settings=settings,
            )
            agents.append(agent)
            logger.debug(f"✅ Agent '{agent_name}' loaded successfully")
        except Exception as e:
            logger.error(f"❌ Failed to load agent '{agent_name}': {e}", exc_info=True)
            raise

    logger.info(f"✅ Successfully loaded {len(agents)} agents")
    return agents


class ChatSession:
    """
    Manages a multi-agent chat session with state control and TTS.

    Features:
    - Per-agent pause/stop/finish control
    - Async generation with cancellation
    - TTS audio generation
    - Turn scheduling based on agent states
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self._lock = asyncio.Lock()
        self._task: Optional[asyncio.Task] = None
        self._running = False
        self._stop_event = asyncio.Event()
        self.topic: str = ""
        self.history: List[Dict[str, Any]] = []
        self.last_messages: List[Dict[str, Any]] = []
        self.agents: List[ChatAgent] = []
        self.session_id: Optional[str] = None
        self.admin_agent: Optional[AdminAgent] = None
        self.content_filter: Optional[ContentFilter] = None

        # Agent state management
        self.state_manager = create_session_state_manager()

        # Audio storage
        self.audio_storage = AudioStorage(base_dir="./data/audio")

        # TTS provider (initialized on demand)
        self._tts_provider = None

        logger.debug("ChatSession initialized")

    @property
    def tts_provider(self):
        """Lazy initialization of TTS provider."""
        if self._tts_provider is None and self.settings.tts_enabled:
            headers = {}
            if self.settings.tts_headers:
                try:
                    import json

                    headers = json.loads(self.settings.tts_headers)
                except json.JSONDecodeError:
                    logger.warning("Failed to parse TTS_HEADERS as JSON")

            self._tts_provider = build_tts_provider(
                provider="openai",
                base_url=self.settings.tts_base_url,
                api_key=self.settings.tts_api_key or self.settings.openai_api_key,
                timeout=self.settings.tts_timeout,
                max_retries=self.settings.tts_max_retries,
                headers=headers,
            )
        return self._tts_provider

    async def start(self, topic: str) -> bool:
        """Start a new chat session."""
        async with self._lock:
            if self._running:
                logger.warning("⚠️  Session already running, cannot start new session")
                return False

            self.session_id = str(uuid.uuid4())
            logger.info(f"🚀 Starting new chat session: {self.session_id}")
            logger.debug(f"📋 Topic: {topic[:100]}...")

            self.topic = topic
            self.history = []
            self.last_messages = []
            self.agents = load_agents(self.settings)

            if len(self.agents) < 1:
                logger.error("❌ No agents configured - cannot start session")
                raise RuntimeError("Need at least one agent to start")

            logger.info(f"🤖 Session has {len(self.agents)} agent(s)")

            # Register all agents with state manager
            for agent in self.agents:
                await self.state_manager.register_agent(agent.name)
                logger.debug(f"Registered agent '{agent.name}' with state manager")

            # If only one agent, create AdminAgent for interaction
            if len(self.agents) == 1:
                logger.debug("👤 Single agent mode - creating AdminAgent")
                self.admin_agent = AdminAgent(self.settings)
            else:
                self.admin_agent = None

            self._running = True
            self._stop_event.clear()
            self._task = asyncio.create_task(self._run_loop())
            logger.info(f"✅ Session {self.session_id} started successfully")
            return True

    async def resume(self) -> bool:
        """Resume a paused session."""
        async with self._lock:
            if self._running:
                logger.warning("⚠️  Session already running, cannot resume")
                return False
            if not self.topic:
                logger.warning("⚠️  No topic to resume")
                return False

            logger.info(f"▶️  Resuming session: {self.session_id}")

            if not self.agents:
                logger.debug("🔄 Reloading agents for resumed session")
                self.agents = load_agents(self.settings)
                # Re-register agents
                for agent in self.agents:
                    await self.state_manager.register_agent(agent.name)

            self._running = True
            self._stop_event.clear()
            self._task = asyncio.create_task(self._run_loop())
            logger.info(f"✅ Session {self.session_id} resumed successfully")
            return True

    async def stop(self) -> None:
        """Stop the session gracefully."""
        async with self._lock:
            if not self._running:
                logger.debug("⚠️  Session not running, nothing to stop")
                return

            logger.info(f"🛑 Stopping session: {self.session_id}")
            self._running = False
            self._stop_event.set()

            # Cancel any active agent tasks
            for agent in self.agents:
                await self.state_manager.stop_agent(agent.name, "Session stopped")

            # Cancel the main task
            if self._task and not self._task.done():
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass

            logger.debug(f"✅ Session {self.session_id} stopped")

    def is_running(self) -> bool:
        """Check if session is running."""
        return self._running

    async def pause_agent(self, agent_name: str, reason: Optional[str] = None) -> bool:
        """Pause a specific agent."""
        return await self.state_manager.pause_agent(agent_name, reason)

    async def resume_agent(self, agent_name: str) -> bool:
        """Resume a paused agent."""
        return await self.state_manager.resume_agent(agent_name)

    async def stop_agent(self, agent_name: str, reason: Optional[str] = None) -> bool:
        """Stop a specific agent."""
        return await self.state_manager.stop_agent(agent_name, reason)

    async def finish_agent(self, agent_name: str, reason: Optional[str] = None) -> bool:
        """Mark an agent as finished."""
        return await self.state_manager.finish_agent(agent_name, reason)

    async def restart_agent(self, agent_name: str) -> bool:
        """Restart a stopped or finished agent."""
        return await self.state_manager.restart_agent(agent_name)

    async def get_agent_states(self) -> Dict[str, dict]:
        """Get states of all agents."""
        return await self.state_manager.get_states_dict()

    async def get_active_agents(self) -> Set[str]:
        """Get set of currently active agent names."""
        return await self.state_manager.get_active_agents()

    def inject_message(
        self, sender: str, content: str, permissions: Optional[Dict] = None
    ):
        """Inject a message into the conversation (admin/user message)."""
        # Apply content filtering if permissions provided
        if permissions:
            filter_instance = create_filter_from_permissions(permissions)
            allowed, filtered_content, message = filter_instance.filter_content(content)
            if not allowed:
                entry = {
                    "sender": "System",
                    "content": message
                    or "This message has been blocked due to inappropriate content.",
                }
                self.history.append(entry)
                self.last_messages.append(entry)
                if len(self.last_messages) > 8:
                    self.last_messages.pop(0)
                return
            content = filtered_content

        entry = {"sender": sender, "content": content}
        self.history.append(entry)
        self.last_messages.append(entry)
        if len(self.last_messages) > 8:
            self.last_messages.pop(0)

    async def _generate_tts(
        self,
        text: str,
        agent: ChatAgent,
        message_id: str,
    ) -> Optional[Dict[str, str]]:
        """
        Generate TTS audio for a message.

        Returns:
            Dict with audio_url, audio_format, audio_mime or None if TTS disabled/failed
        """
        if not self.settings.tts_enabled or not self.tts_provider:
            return None

        try:
            # Get per-agent TTS settings
            voice = agent.tts_voice_override or self.settings.tts_voice
            model = agent.tts_model_override or self.settings.tts_model
            format = self.settings.tts_format
            speed = self.settings.tts_speed
            instructions = self.settings.tts_instructions or None

            # Generate audio
            result = await self.tts_provider.synthesize(
                text=text,
                voice=voice,
                model=model,
                response_format=format,
                speed=speed if speed != 1.0 else None,
                instructions=instructions,
            )

            # Store audio
            relative_path, was_cached = self.audio_storage.save_audio(
                audio_bytes=result.audio_bytes,
                session_id=self.session_id,
                message_id=message_id,
                text=text,
                voice=voice,
                model=model,
                format=format,
                speed=speed,
            )

            return {
                "audio_url": f"/audio/{relative_path}",
                "audio_format": result.format,
                "audio_mime": result.mime_type,
                "audio_cached": was_cached,
            }

        except Exception as e:
            logger.error(f"TTS generation failed for message {message_id}: {e}")
            return None

    async def _generate_agent_response(
        self,
        agent: ChatAgent,
    ) -> Tuple[str, Optional[Dict[str, str]]]:
        """
        Generate agent response with TTS.

        This runs in a separate task for cancellation support.
        """
        message_id = str(uuid.uuid4())

        # Generate text response
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            agent.generate_response,
            self.topic,
            self.history,
        )

        # Handle tuple return from generate_response
        if isinstance(response, tuple):
            response_text, legacy_audio_path = response
        else:
            response_text = response
            legacy_audio_path = None

        # Generate TTS if enabled
        audio_info = None
        if self.settings.tts_enabled and response_text:
            audio_info = await self._generate_tts(response_text, agent, message_id)

        # If legacy audio path exists but no new TTS, use legacy
        if not audio_info and legacy_audio_path:
            audio_info = {
                "audio_url": f"/audio/{os.path.basename(legacy_audio_path)}",
                "audio_format": "mp3",
                "audio_mime": "audio/mpeg",
                "audio_cached": True,
            }

        return response_text, audio_info

    async def _run_agent_turn(self, agent: ChatAgent) -> bool:
        """
        Run a single agent's turn.

        Returns:
            True if turn completed successfully, False if interrupted/cancelled
        """
        agent_name = agent.name

        # Check if agent is still active
        if not await self.state_manager.is_active(agent_name):
            logger.debug(f"Skipping inactive agent '{agent_name}'")
            return False

        # Set current task for cancellation support
        task = asyncio.create_task(self._generate_agent_response(agent))
        await self.state_manager.set_task(agent_name, task)

        try:
            response, audio_info = await task
        except asyncio.CancelledError:
            logger.info(f"Agent '{agent_name}' turn was cancelled")
            await self.state_manager.set_task(agent_name, None)
            return False
        except Exception as e:
            logger.error(f"Error in agent '{agent_name}' turn: {e}")
            await self.state_manager.set_task(agent_name, None)
            return False
        finally:
            await self.state_manager.set_task(agent_name, None)

        # Check if still running after generation
        if not self._running:
            return False

        # Apply content filter
        allowed, filtered_response, filter_msg = self._filter_response(response)

        if not allowed:
            entry = {
                "sender": "System",
                "content": filter_msg
                or f"[{agent.full_name}'s message blocked due to inappropriate content]",
            }
        else:
            entry = {
                "sender": agent.full_name,
                "content": filtered_response,
            }
            if audio_info:
                entry.update(audio_info)

        # Add to history
        self.history.append(entry)
        self.last_messages.append(entry)
        if len(self.last_messages) > 8:
            self.last_messages.pop(0)

        # Store in memory
        for memory_agent in self.agents:
            try:
                memory_agent.remember_message(
                    agent.full_name,
                    response,
                    session_id=self.session_id,
                    topic=self.topic,
                )
            except Exception as e:
                logger.error(
                    f"Failed to store memory for agent '{memory_agent.name}': {e}"
                )

        return True

    async def _run_loop(self) -> None:
        """Main conversation loop with agent state management."""
        round_num = 1

        try:
            while self._running:
                # Get active agents
                active_agents = await self.get_active_agents()

                if not active_agents:
                    logger.info("No active agents remaining, ending session")
                    break

                # Handle solo agent mode with AdminAgent
                if self.admin_agent:
                    await self._run_solo_mode(active_agents)
                else:
                    await self._run_multi_agent_mode(active_agents)

                round_num += 1

                # Sleep between rounds
                await asyncio.sleep(self.settings.sleep_seconds)

        except asyncio.CancelledError:
            logger.info("Session loop cancelled")
            raise
        except Exception as e:
            logger.error(f"Error in session loop: {e}", exc_info=True)
            raise
        finally:
            self._running = False
            logger.info(f"Session {self.session_id} loop ended")

    async def _run_solo_mode(self, active_agents: Set[str]) -> None:
        """Run solo agent mode (agent + admin)."""
        agent = self.agents[0]

        # Check if agent is active
        if agent.name not in active_agents:
            logger.debug("Solo agent not active, skipping turn")
            return

        # Agent speaks
        if not self._running:
            return

        success = await self._run_agent_turn(agent)

        if not success or not self._running:
            return

        # Admin responds
        try:
            admin_response = self.admin_agent.generate_response(
                self.topic, self.history
            )
            admin_entry = {
                "sender": self.admin_agent.full_name,
                "content": admin_response,
            }
            self.history.append(admin_entry)
            self.last_messages.append(admin_entry)
            if len(self.last_messages) > 8:
                self.last_messages.pop(0)
        except Exception as e:
            logger.error(f"Admin agent error: {e}")

        # Summarize if needed
        await self._maybe_summarize()

    async def _run_multi_agent_mode(self, active_agents: Set[str]) -> None:
        """Run multi-agent mode (all agents take turns)."""
        for agent in list(self.agents):
            # Check if still running
            if not self._running:
                break

            # Check if agent is active
            if agent.name not in active_agents:
                logger.debug(
                    f"Skipping inactive agent '{agent.name}' in multi-agent mode"
                )
                continue

            # Run agent turn
            success = await self._run_agent_turn(agent)

            if not success:
                logger.debug(f"Agent '{agent.name}' turn did not complete successfully")

            # Summarize if needed
            await self._maybe_summarize()

    async def _maybe_summarize(self) -> None:
        """Summarize old messages if history exceeds limit."""
        if len(self.history) <= self.settings.history_max_messages:
            return

        num_to_summarize = self.settings.history_max_messages // 2
        old_messages = self.history[:num_to_summarize]
        summary = await self._summarize_old_messages_async(old_messages)

        self.history = self.history[num_to_summarize:]
        if summary:
            self.history.insert(
                0,
                {
                    "sender": "System",
                    "content": f"Previous conversation summary: {summary}",
                },
            )

    async def _summarize_old_messages_async(
        self, messages: List[Dict[str, Any]]
    ) -> str:
        """Summarize older messages using LLM (async version)."""
        if not messages:
            return ""

        conversation_text = "\n".join(
            f"{msg['sender']}: {msg['content']}" for msg in messages
        )

        if not self.agents:
            return f"[{len(messages)} previous messages]"

        try:
            first_agent = self.agents[0]

            summary_prompt = [
                {
                    "role": "system",
                    "content": "You are a conversation summarizer. Provide a concise summary of the following conversation, capturing key points and arguments.",
                },
                {
                    "role": "user",
                    "content": f"Summarize this conversation:\n\n{conversation_text}",
                },
            ]

            # Run in executor since chat_provider.chat is synchronous
            summary = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: first_agent.chat_provider.chat(
                    model=first_agent.model or self.settings.default_chat_model,
                    messages=summary_prompt,
                    temperature=0.5,
                    max_tokens=200,
                ),
            )

            return summary.strip() if isinstance(summary, str) else str(summary)

        except Exception as e:
            logger.error(f"Error summarizing messages: {e}")
            return f"[{len(messages)} previous messages]"

    def clear_memory(self):
        """Clear session history."""
        self.history = []
        self.last_messages = []

    def set_content_filter(self, filter_instance: Optional[ContentFilter]):
        """Set a content filter for all messages in this session."""
        self.content_filter = filter_instance

    def _filter_response(self, response: str) -> tuple:
        """
        Filter agent response through content filter.

        Returns:
            Tuple of (allowed, filtered_content, message)
        """
        if not self.content_filter:
            return True, response, None

        return self.content_filter.filter_content(response)
