import asyncio
import json

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import JSONResponse, StreamingResponse
from ..session import ChatSession
from .advanced import get_chat_session

router = APIRouter(prefix="/api/v1/control", tags=["control"])


async def _session_status_payload(session: ChatSession) -> dict:
    return {
        "running": session.is_running(),
        "topic": session.topic,
        "session_id": session.session_id,
        "last_messages": session.last_messages,
        "agent_states": await session.get_agent_states(),
        "message_rate": session.get_message_rate(),
    }


@router.post("/start")
async def start_session(
    topic: str = Form(""), session: ChatSession = Depends(get_chat_session)
):
    """Start a new chat session."""
    topic = topic.strip()
    if not topic:
        return JSONResponse(
            {"status": "failed", "reason": "Topic is required"}, status_code=400
        )
    if await session.start(topic):
        return JSONResponse(
            {
                "status": "started",
                "session_id": session.session_id,
                "topic": session.topic,
            }
        )
    return JSONResponse(
        {"status": "failed", "reason": "Session already running"}, status_code=400
    )


@router.post("/stop")
async def stop_session(session: ChatSession = Depends(get_chat_session)):
    """Stop the current chat session."""
    await session.stop()
    return JSONResponse({"status": "stopped"})


@router.post("/interrupt")
async def interrupt_session(session: ChatSession = Depends(get_chat_session)):
    """Interrupt the active generation immediately."""
    await session.stop()
    return JSONResponse({"status": "interrupted"})


@router.post("/memory/clear")
def clear_memory(session: ChatSession = Depends(get_chat_session)):
    """Clear session memory."""
    session.clear_memory()
    return JSONResponse({"status": "memory_cleared"})


@router.post("/resume")
async def resume_session(session: ChatSession = Depends(get_chat_session)):
    """Resume a paused session."""
    if await session.resume():
        return JSONResponse(
            {
                "status": "resumed",
                "session_id": session.session_id,
                "topic": session.topic,
            }
        )
    return JSONResponse(
        {"status": "failed", "reason": "Already running or no topic"}, status_code=400
    )


@router.post("/pause")
async def pause_session(session: ChatSession = Depends(get_chat_session)):
    """Pause the current session without clearing history or topic."""
    await session.stop()
    return JSONResponse({"status": "paused"})


@router.post("/messages")
def send_message(
    content: str = Form(...),
    sender: str = Form("Admin"),
    session: ChatSession = Depends(get_chat_session),
):
    """Inject a message into the conversation."""
    content = content.strip()
    sender = sender.strip()

    if not content:
        return JSONResponse(
            {"status": "failed", "reason": "Message content is required"},
            status_code=400,
        )

    if not sender:
        sender = "Admin"

    # Apply content filter if configured
    if session.content_filter:
        allowed, filtered_content, message = session.content_filter.filter_content(
            content
        )
        if not allowed:
            return JSONResponse(
                {
                    "status": "blocked",
                    "message": message
                    or "Message blocked due to inappropriate content",
                },
                status_code=400,
            )
        content = filtered_content

    session.inject_message(sender, content)
    return JSONResponse({"status": "sent", "sender": sender})


@router.post("/context/switch")
async def switch_context(
    topic: str = Form(""), session: ChatSession = Depends(get_chat_session)
):
    """Switch active conversation topic without reconnecting."""
    if await session.switch_topic(topic):
        return JSONResponse({"status": "switched", "topic": session.topic})
    return JSONResponse(
        {"status": "failed", "reason": "Topic is required"}, status_code=400
    )


@router.post("/rate")
async def set_message_rate(
    rate: float = Form(1.0), session: ChatSession = Depends(get_chat_session)
):
    """Adjust runtime message pacing multiplier."""
    applied_rate = session.set_message_rate(rate)
    return JSONResponse({"status": "updated", "message_rate": applied_rate})


@router.get("/status")
async def control_status(session: ChatSession = Depends(get_chat_session)):
    """Get control-plane session status snapshot."""
    return JSONResponse(await _session_status_payload(session))


@router.get("/events")
async def control_events(
    request: Request, session: ChatSession = Depends(get_chat_session)
):
    """Server-Sent Events stream for real-time control/status updates."""

    async def event_generator():
        while True:
            try:
                if await request.is_disconnected():
                    break
            except Exception:
                break
            payload = await _session_status_payload(session)
            yield f"data: {json.dumps(payload)}\n\n"
            await asyncio.sleep(0.25)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
