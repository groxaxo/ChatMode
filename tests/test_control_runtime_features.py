import pytest
from unittest.mock import Mock

from chatmode.session import ChatSession
from chatmode.routes.control import _session_status_payload


@pytest.mark.asyncio
async def test_switch_topic_updates_session_without_reset():
    session = ChatSession(Mock())
    session.topic = "Original topic"
    session.history = [{"sender": "User", "content": "hello"}]

    switched = await session.switch_topic("New topic")

    assert switched is True
    assert session.topic == "New topic"
    assert session.history[-1]["sender"] == "System"
    assert "Context switched to: New topic" in session.history[-1]["content"]


def test_message_rate_clamps_and_affects_turn_delay():
    session = ChatSession(Mock())

    assert session.set_message_rate(8.0) == 5.0
    assert session._compute_turn_delay(2.0) == 0.4
    assert session.set_message_rate(0.01) == 0.1
    assert session._compute_turn_delay(0.001) == 0.05


@pytest.mark.asyncio
async def test_control_status_payload_includes_message_rate():
    session = ChatSession(Mock())
    session.topic = "Status topic"
    session.last_messages = [{"sender": "A", "content": "B"}]
    session.set_message_rate(1.7)

    payload = await _session_status_payload(session)

    assert payload["topic"] == "Status topic"
    assert payload["message_rate"] == 1.7
    assert payload["last_messages"][0]["sender"] == "A"
