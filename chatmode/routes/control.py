from fastapi import APIRouter, Depends, Form
from fastapi.responses import JSONResponse
from ..session import ChatSession
from .advanced import get_chat_session

router = APIRouter(prefix="/api/v1/control", tags=["control"])


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
