"""
Agent state management for pause/stop/finish control.

Provides per-agent state tracking and control mechanisms.
"""

import asyncio
import logging
from enum import Enum, auto
from typing import Dict, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


class AgentState(Enum):
    """
    Agent lifecycle states.

    - ACTIVE: Normal operation, agent takes turns
    - PAUSED: Agent is temporarily skipped but stays in roster
    - STOPPED: Agent is removed from rotation (can be restarted)
    - FINISHED: Agent has completed its role (terminal state)
    """

    ACTIVE = "active"
    PAUSED = "paused"
    STOPPED = "stopped"
    FINISHED = "finished"


@dataclass
class AgentStateInfo:
    """Information about an agent's current state."""

    state: AgentState = AgentState.ACTIVE
    changed_at: datetime = field(default_factory=datetime.utcnow)
    reason: Optional[str] = None
    # Track the current task for cancellation support
    current_task: Optional[asyncio.Task] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "state": self.state.value,
            "changed_at": self.changed_at.isoformat(),
            "reason": self.reason,
            "has_active_task": self.current_task is not None
            and not self.current_task.done(),
        }


class AgentStateManager:
    """
    Manages per-agent states and provides control mechanisms.

    This class tracks the state of each agent in a session and provides
    methods to pause, resume, stop, and finish agents. It also supports
    interrupting agents mid-generation through task cancellation.
    """

    def __init__(self):
        self._states: Dict[str, AgentStateInfo] = {}
        self._lock = asyncio.Lock()
        logger.debug("AgentStateManager initialized")

    async def register_agent(self, agent_name: str) -> None:
        """Register a new agent with ACTIVE state."""
        async with self._lock:
            if agent_name not in self._states:
                self._states[agent_name] = AgentStateInfo(state=AgentState.ACTIVE)
                logger.debug(f"Agent '{agent_name}' registered as ACTIVE")

    async def unregister_agent(self, agent_name: str) -> None:
        """Unregister an agent and cancel any active task."""
        async with self._lock:
            if agent_name in self._states:
                state_info = self._states[agent_name]
                if state_info.current_task and not state_info.current_task.done():
                    logger.warning(
                        f"Cancelling active task for unregistered agent '{agent_name}'"
                    )
                    state_info.current_task.cancel()
                del self._states[agent_name]
                logger.debug(f"Agent '{agent_name}' unregistered")

    async def set_task(self, agent_name: str, task: Optional[asyncio.Task]) -> None:
        """Set the current task for an agent (for cancellation support)."""
        async with self._lock:
            if agent_name in self._states:
                self._states[agent_name].current_task = task
                logger.debug(f"Task set for agent '{agent_name}': {task is not None}")

    async def pause_agent(self, agent_name: str, reason: Optional[str] = None) -> bool:
        """
        Pause an agent. It will be skipped in turn rotation but stays informed.

        Args:
            agent_name: Name of the agent to pause
            reason: Optional reason for pausing

        Returns:
            True if state was changed, False otherwise
        """
        async with self._lock:
            if agent_name not in self._states:
                logger.warning(f"Cannot pause unknown agent '{agent_name}'")
                return False

            state_info = self._states[agent_name]
            if state_info.state == AgentState.PAUSED:
                logger.debug(f"Agent '{agent_name}' is already paused")
                return False

            # Cancel any active task
            if state_info.current_task and not state_info.current_task.done():
                logger.info(f"Cancelling active task for paused agent '{agent_name}'")
                state_info.current_task.cancel()

            state_info.state = AgentState.PAUSED
            state_info.changed_at = datetime.utcnow()
            state_info.reason = reason

            logger.info(f"Agent '{agent_name}' paused: {reason or 'No reason given'}")
            return True

    async def resume_agent(self, agent_name: str) -> bool:
        """
        Resume a paused agent.

        Args:
            agent_name: Name of the agent to resume

        Returns:
            True if state was changed, False otherwise
        """
        async with self._lock:
            if agent_name not in self._states:
                logger.warning(f"Cannot resume unknown agent '{agent_name}'")
                return False

            state_info = self._states[agent_name]
            if state_info.state != AgentState.PAUSED:
                logger.debug(
                    f"Agent '{agent_name}' is not paused (state: {state_info.state.value})"
                )
                return False

            state_info.state = AgentState.ACTIVE
            state_info.changed_at = datetime.utcnow()
            state_info.reason = None

            logger.info(f"Agent '{agent_name}' resumed")
            return True

    async def stop_agent(self, agent_name: str, reason: Optional[str] = None) -> bool:
        """
        Stop an agent. It will be removed from turn rotation.

        If the agent is currently generating, its task will be cancelled.

        Args:
            agent_name: Name of the agent to stop
            reason: Optional reason for stopping

        Returns:
            True if state was changed, False otherwise
        """
        async with self._lock:
            if agent_name not in self._states:
                logger.warning(f"Cannot stop unknown agent '{agent_name}'")
                return False

            state_info = self._states[agent_name]
            if state_info.state == AgentState.STOPPED:
                logger.debug(f"Agent '{agent_name}' is already stopped")
                return False

            # Cancel any active task immediately
            if state_info.current_task and not state_info.current_task.done():
                logger.info(f"Cancelling active task for stopped agent '{agent_name}'")
                state_info.current_task.cancel()
                try:
                    await asyncio.wait_for(state_info.current_task, timeout=5.0)
                except (asyncio.CancelledError, asyncio.TimeoutError):
                    pass

            state_info.state = AgentState.STOPPED
            state_info.changed_at = datetime.utcnow()
            state_info.reason = reason
            state_info.current_task = None

            logger.info(f"Agent '{agent_name}' stopped: {reason or 'No reason given'}")
            return True

    async def finish_agent(self, agent_name: str, reason: Optional[str] = None) -> bool:
        """
        Mark an agent as finished. This is a terminal state.

        Args:
            agent_name: Name of the agent to finish
            reason: Optional reason for finishing

        Returns:
            True if state was changed, False otherwise
        """
        async with self._lock:
            if agent_name not in self._states:
                logger.warning(f"Cannot finish unknown agent '{agent_name}'")
                return False

            state_info = self._states[agent_name]
            if state_info.state == AgentState.FINISHED:
                logger.debug(f"Agent '{agent_name}' is already finished")
                return False

            # Cancel any active task
            if state_info.current_task and not state_info.current_task.done():
                logger.info(f"Cancelling active task for finished agent '{agent_name}'")
                state_info.current_task.cancel()
                try:
                    await asyncio.wait_for(state_info.current_task, timeout=5.0)
                except (asyncio.CancelledError, asyncio.TimeoutError):
                    pass

            state_info.state = AgentState.FINISHED
            state_info.changed_at = datetime.utcnow()
            state_info.reason = reason
            state_info.current_task = None

            logger.info(f"Agent '{agent_name}' finished: {reason or 'No reason given'}")
            return True

    async def restart_agent(self, agent_name: str) -> bool:
        """
        Restart a stopped or finished agent.

        Args:
            agent_name: Name of the agent to restart

        Returns:
            True if state was changed, False otherwise
        """
        async with self._lock:
            if agent_name not in self._states:
                logger.warning(f"Cannot restart unknown agent '{agent_name}'")
                return False

            state_info = self._states[agent_name]
            if state_info.state not in (AgentState.STOPPED, AgentState.FINISHED):
                logger.debug(
                    f"Agent '{agent_name}' is not stopped/finished (state: {state_info.state.value})"
                )
                return False

            state_info.state = AgentState.ACTIVE
            state_info.changed_at = datetime.utcnow()
            state_info.reason = "Agent restarted"

            logger.info(f"Agent '{agent_name}' restarted")
            return True

    async def get_state(self, agent_name: str) -> Optional[AgentStateInfo]:
        """Get the state info for an agent."""
        async with self._lock:
            return self._states.get(agent_name)

    async def is_active(self, agent_name: str) -> bool:
        """Check if an agent is active (should take turns)."""
        async with self._lock:
            state_info = self._states.get(agent_name)
            if not state_info:
                return False
            return state_info.state == AgentState.ACTIVE

    async def get_active_agents(self) -> Set[str]:
        """Get the set of currently active agent names."""
        async with self._lock:
            return {
                name
                for name, info in self._states.items()
                if info.state == AgentState.ACTIVE
            }

    async def get_all_states(self) -> Dict[str, AgentStateInfo]:
        """Get all agent states (returns a copy)."""
        async with self._lock:
            return dict(self._states)

    async def get_states_dict(self) -> Dict[str, dict]:
        """Get all agent states as dictionaries for API responses."""
        async with self._lock:
            return {name: info.to_dict() for name, info in self._states.items()}

    async def reset_all(self) -> None:
        """Reset all agents to ACTIVE state (useful for new sessions)."""
        async with self._lock:
            for state_info in self._states.values():
                if state_info.current_task and not state_info.current_task.done():
                    state_info.current_task.cancel()
                state_info.state = AgentState.ACTIVE
                state_info.changed_at = datetime.utcnow()
                state_info.reason = None
                state_info.current_task = None
            logger.info("All agent states reset to ACTIVE")


# Global state manager instance (can be replaced with per-session managers)
_default_manager: Optional[AgentStateManager] = None


def get_agent_state_manager() -> AgentStateManager:
    """Get the default agent state manager (singleton)."""
    global _default_manager
    if _default_manager is None:
        _default_manager = AgentStateManager()
    return _default_manager


def create_session_state_manager() -> AgentStateManager:
    """Create a new state manager for a session."""
    return AgentStateManager()
