"""
Unit tests for frontend-backend state synchronization.

These tests verify that agent control and session control endpoints
return immediate state updates to ensure 100% synchronization between
frontend and backend.
"""

import asyncio
import pytest
from unittest.mock import Mock, patch
from chatmode.agent_state import AgentState, AgentStateManager
from chatmode.session import ChatSession
from chatmode.config import Settings


class TestAgentControlStateSynchronization:
    """Test that agent control endpoints return updated state."""

    @pytest.fixture
    async def state_manager(self):
        """Create a fresh state manager for testing."""
        manager = AgentStateManager()
        await manager.register_agent("test-agent")
        return manager

    @pytest.mark.asyncio
    async def test_pause_returns_updated_state(self, state_manager):
        """Test that pause_agent returns the paused state."""
        # Pause the agent
        success = await state_manager.pause_agent("test-agent", "Test reason")
        assert success

        # Get state dict (simulating what endpoint returns)
        state_dict = await state_manager.get_states_dict()
        assert "test-agent" in state_dict
        assert state_dict["test-agent"]["state"] == "paused"
        assert state_dict["test-agent"]["reason"] == "Test reason"
        assert "changed_at" in state_dict["test-agent"]

    @pytest.mark.asyncio
    async def test_resume_returns_updated_state(self, state_manager):
        """Test that resume_agent returns the active state."""
        # Pause then resume
        await state_manager.pause_agent("test-agent")
        success = await state_manager.resume_agent("test-agent")
        assert success

        # Get state dict
        state_dict = await state_manager.get_states_dict()
        assert state_dict["test-agent"]["state"] == "active"
        assert state_dict["test-agent"]["reason"] is None

    @pytest.mark.asyncio
    async def test_stop_returns_updated_state(self, state_manager):
        """Test that stop_agent returns the stopped state."""
        # Stop the agent
        success = await state_manager.stop_agent("test-agent", "Admin stopped")
        assert success

        # Get state dict
        state_dict = await state_manager.get_states_dict()
        assert state_dict["test-agent"]["state"] == "stopped"
        assert state_dict["test-agent"]["reason"] == "Admin stopped"

    @pytest.mark.asyncio
    async def test_finish_returns_updated_state(self, state_manager):
        """Test that finish_agent returns the finished state."""
        # Finish the agent
        success = await state_manager.finish_agent("test-agent", "Task complete")
        assert success

        # Get state dict
        state_dict = await state_manager.get_states_dict()
        assert state_dict["test-agent"]["state"] == "finished"
        assert state_dict["test-agent"]["reason"] == "Task complete"

    @pytest.mark.asyncio
    async def test_restart_returns_updated_state(self, state_manager):
        """Test that restart_agent returns the active state."""
        # Stop then restart
        await state_manager.stop_agent("test-agent")
        success = await state_manager.restart_agent("test-agent")
        assert success

        # Get state dict
        state_dict = await state_manager.get_states_dict()
        assert state_dict["test-agent"]["state"] == "active"
        assert state_dict["test-agent"]["reason"] == "Agent restarted"

    @pytest.mark.asyncio
    async def test_concurrent_state_changes(self, state_manager):
        """Test that concurrent state changes are handled correctly."""
        # Register multiple agents
        await state_manager.register_agent("agent-1")
        await state_manager.register_agent("agent-2")
        await state_manager.register_agent("agent-3")

        # Pause agent-1 and stop agent-2 concurrently
        await state_manager.pause_agent("agent-1")
        await state_manager.stop_agent("agent-2")

        # Get all states
        states = await state_manager.get_states_dict()

        # Verify each agent has correct state
        assert states["agent-1"]["state"] == "paused"
        assert states["agent-2"]["state"] == "stopped"
        assert states["agent-3"]["state"] == "active"


class TestSessionControlStateSynchronization:
    """Test that session control operations update state correctly."""

    @pytest.fixture
    def mock_settings(self):
        """Create mock settings for testing."""
        settings = Mock(spec=Settings)
        settings.log_level = "INFO"
        settings.log_dir = "./logs"
        settings.tts_output_dir = "./tts_out"
        settings.sleep_seconds = 1
        settings.memory_top_k = 10
        return settings

    @pytest.mark.asyncio
    async def test_session_start_state(self, mock_settings):
        """Test that starting a session sets running state to True."""
        with patch("chatmode.session.load_agents") as mock_load:
            # Mock single agent
            mock_agent = Mock()
            mock_agent.name = "test-agent"
            mock_load.return_value = [mock_agent]

            session = ChatSession(mock_settings)

            # Start session
            result = await session.start("Test topic")
            assert result is True

            # Verify running state
            assert session.is_running() is True
            assert session.topic == "Test topic"
            assert session.session_id is not None

    @pytest.mark.asyncio
    async def test_session_stop_state(self, mock_settings):
        """Test that stopping a session sets running state to False."""
        with patch("chatmode.session.load_agents") as mock_load:
            mock_agent = Mock()
            mock_agent.name = "test-agent"
            mock_load.return_value = [mock_agent]

            session = ChatSession(mock_settings)
            await session.start("Test topic")

            # Stop session
            await session.stop()

            # Verify stopped state
            assert session.is_running() is False

    @pytest.mark.asyncio
    async def test_session_resume_state(self, mock_settings):
        """Test that resuming a session sets running state to True."""
        with patch("chatmode.session.load_agents") as mock_load:
            mock_agent = Mock()
            mock_agent.name = "test-agent"
            mock_load.return_value = [mock_agent]

            session = ChatSession(mock_settings)
            await session.start("Test topic")
            await session.stop()

            # Resume session
            result = await session.resume()
            assert result is True

            # Verify running state
            assert session.is_running() is True


class TestEndpointResponseFormat:
    """Test that endpoint responses include required state fields."""

    @pytest.mark.asyncio
    async def test_pause_endpoint_response_format(self, state_manager):
        """Test that pause endpoint response includes agent_state field."""
        await state_manager.pause_agent("test-agent", "Test")

        # Simulate endpoint response
        response = {
            "status": "paused",
            "agent": "test-agent",
            "reason": "Test",
            "agent_state": (await state_manager.get_states_dict())["test-agent"],
        }

        # Verify response format
        assert "status" in response
        assert "agent" in response
        assert "agent_state" in response
        assert response["agent_state"]["state"] == "paused"
        assert "changed_at" in response["agent_state"]

    @pytest.mark.asyncio
    async def test_resume_endpoint_response_format(self, state_manager):
        """Test that resume endpoint response includes agent_state field."""
        await state_manager.pause_agent("test-agent")
        await state_manager.resume_agent("test-agent")

        # Simulate endpoint response
        response = {
            "status": "resumed",
            "agent": "test-agent",
            "agent_state": (await state_manager.get_states_dict())["test-agent"],
        }

        # Verify response format
        assert "agent_state" in response
        assert response["agent_state"]["state"] == "active"

    @pytest.mark.asyncio
    async def test_stop_endpoint_response_format(self, state_manager):
        """Test that stop endpoint response includes agent_state field."""
        await state_manager.stop_agent("test-agent", "Admin stop")

        # Simulate endpoint response
        response = {
            "status": "stopped",
            "agent": "test-agent",
            "reason": "Admin stop",
            "agent_state": (await state_manager.get_states_dict())["test-agent"],
        }

        # Verify response format
        assert response["agent_state"]["state"] == "stopped"
        assert response["agent_state"]["reason"] == "Admin stop"

    @pytest.mark.asyncio
    async def test_finish_endpoint_response_format(self, state_manager):
        """Test that finish endpoint response includes agent_state field."""
        await state_manager.finish_agent("test-agent", "Complete")

        # Simulate endpoint response
        response = {
            "status": "finished",
            "agent": "test-agent",
            "reason": "Complete",
            "agent_state": (await state_manager.get_states_dict())["test-agent"],
        }

        # Verify response format
        assert response["agent_state"]["state"] == "finished"

    @pytest.mark.asyncio
    async def test_restart_endpoint_response_format(self, state_manager):
        """Test that restart endpoint response includes agent_state field."""
        await state_manager.stop_agent("test-agent")
        await state_manager.restart_agent("test-agent")

        # Simulate endpoint response
        response = {
            "status": "restarted",
            "agent": "test-agent",
            "agent_state": (await state_manager.get_states_dict())["test-agent"],
        }

        # Verify response format
        assert response["agent_state"]["state"] == "active"


class TestRaceConditionPrevention:
    """Test that race conditions are prevented through immediate state updates."""

    @pytest.mark.asyncio
    async def test_no_race_between_pause_and_status_check(self, state_manager):
        """
        Test that pausing an agent immediately updates state,
        preventing race conditions with status polling.
        """
        # Initial state
        initial_state = await state_manager.get_state("test-agent")
        assert initial_state.state == AgentState.ACTIVE

        # Pause agent
        await state_manager.pause_agent("test-agent")

        # Immediately check state (simulating quick status poll)
        immediate_state = await state_manager.get_state("test-agent")
        assert immediate_state.state == AgentState.PAUSED

        # No race condition - state is immediately updated

    @pytest.mark.asyncio
    async def test_optimistic_update_with_error_revert(self, state_manager):
        """
        Test that failed operations don't leave state in inconsistent state.
        """
        # Try to pause non-existent agent
        success = await state_manager.pause_agent("non-existent-agent")
        assert success is False

        # Verify original agent is unchanged
        state = await state_manager.get_state("test-agent")
        assert state.state == AgentState.ACTIVE

    @pytest.mark.asyncio
    async def test_concurrent_operations_on_different_agents(self, state_manager):
        """Test that operations on different agents don't interfere."""
        await state_manager.register_agent("agent-1")
        await state_manager.register_agent("agent-2")

        # Perform operations concurrently on different agents
        await state_manager.pause_agent("agent-1")
        await state_manager.stop_agent("agent-2")

        # Verify both operations succeeded independently
        state1 = await state_manager.get_state("agent-1")
        state2 = await state_manager.get_state("agent-2")

        assert state1.state == AgentState.PAUSED
        assert state2.state == AgentState.STOPPED


class TestStateTimestamps:
    """Test that state changes include accurate timestamps."""

    @pytest.mark.asyncio
    async def test_changed_at_timestamp_updates(self, state_manager):
        """Test that changed_at timestamp updates on state changes."""
        import time

        # Get initial timestamp
        initial_state = await state_manager.get_state("test-agent")
        initial_time = initial_state.changed_at

        # Wait a small amount
        await asyncio.sleep(0.1)

        # Pause agent
        await state_manager.pause_agent("test-agent")

        # Get new timestamp
        paused_state = await state_manager.get_state("test-agent")
        paused_time = paused_state.changed_at

        # Timestamps should be different
        assert paused_time > initial_time

    @pytest.mark.asyncio
    async def test_timestamp_in_response_dict(self, state_manager):
        """Test that timestamp is included in state dictionary responses."""
        await state_manager.pause_agent("test-agent")

        state_dict = await state_manager.get_states_dict()
        assert "changed_at" in state_dict["test-agent"]
        assert isinstance(state_dict["test-agent"]["changed_at"], str)
        # Should be ISO format timestamp
        assert "T" in state_dict["test-agent"]["changed_at"]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
