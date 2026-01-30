"""
Conversation and message management routes.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from typing import Optional
import math

from ..database import get_db
from ..models import User, Conversation, Message
from ..schemas import (
    ConversationResponse, ConversationListResponse,
    MessageResponse, MessageListResponse,
    VoiceAssetResponse
)
from ..auth import get_current_user, require_role
from ..audit import log_action, get_client_ip, AuditAction
from .. import crud

router = APIRouter(prefix="/api/v1/conversations", tags=["conversations"])


def message_to_response(message: Message) -> MessageResponse:
    """Convert Message model to response schema."""
    voice_assets = []
    if message.voice_assets:
        for va in message.voice_assets:
            voice_assets.append(VoiceAssetResponse(
                id=va.id,
                message_id=va.message_id,
                filename=va.filename,
                original_filename=va.original_filename,
                mime_type=va.mime_type,
                file_size=va.file_size,
                duration_seconds=va.duration_seconds,
                source=va.source,
                transcript=va.transcript,
                created_at=va.created_at
            ))
    
    return MessageResponse(
        id=message.id,
        conversation_id=message.conversation_id,
        role=message.role,
        content=message.content,
        agent_id=message.agent_id,
        token_count=message.token_count,
        latency_ms=message.latency_ms,
        voice_assets=voice_assets,
        created_at=message.created_at
    )


def conversation_to_response(conv: Conversation, include_messages: bool = False) -> ConversationResponse:
    """Convert Conversation model to response schema."""
    messages = []
    if include_messages and conv.messages:
        messages = [message_to_response(m) for m in conv.messages]
    
    return ConversationResponse(
        id=conv.id,
        agent_id=conv.agent_id,
        title=conv.title,
        status=conv.status,
        message_count=conv.message_count,
        total_tokens=conv.total_tokens,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        messages=messages if include_messages else None
    )


@router.get("/", response_model=ConversationListResponse)
async def list_conversations(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    agent_id: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List conversations with pagination.
    
    - **agent_id**: Filter by agent
    - **status**: Filter by status (active, archived, deleted)
    """
    conversations, total = crud.get_conversations(
        db,
        page=page,
        per_page=per_page,
        agent_id=agent_id,
        status=status
    )
    
    return ConversationListResponse(
        items=[conversation_to_response(c) for c in conversations],
        total=total,
        page=page,
        per_page=per_page,
        pages=math.ceil(total / per_page) if total > 0 else 1
    )


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    include_messages: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a conversation by ID.
    
    - **include_messages**: Include all messages in response (default: true)
    """
    conv = crud.get_conversation(db, conversation_id)
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": "Conversation not found"}
        )
    
    return conversation_to_response(conv, include_messages=include_messages)


@router.get("/{conversation_id}/messages", response_model=MessageListResponse)
async def get_conversation_messages(
    conversation_id: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    role: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get messages for a conversation with pagination.
    
    - **role**: Filter by role (user, assistant, system)
    """
    conv = crud.get_conversation(db, conversation_id)
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": "Conversation not found"}
        )
    
    messages, total = crud.get_messages(
        db,
        conversation_id=conversation_id,
        page=page,
        per_page=per_page,
        role=role
    )
    
    return MessageListResponse(
        items=[message_to_response(m) for m in messages],
        total=total,
        page=page,
        per_page=per_page,
        pages=math.ceil(total / per_page) if total > 0 else 1
    )


@router.get("/{conversation_id}/messages/{message_id}", response_model=MessageResponse)
async def get_message(
    conversation_id: str,
    message_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a single message by ID."""
    message = crud.get_message(db, message_id)
    if not message or message.conversation_id != conversation_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": "Message not found"}
        )
    
    return message_to_response(message)


@router.put("/{conversation_id}/archive")
async def archive_conversation(
    request: Request,
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "moderator"]))
):
    """Archive a conversation."""
    conv = crud.get_conversation(db, conversation_id)
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": "Conversation not found"}
        )
    
    conv.status = "archived"
    db.commit()
    
    # Audit log
    log_action(
        db=db,
        user=current_user,
        action=AuditAction.CONVERSATION_ARCHIVE,
        resource_type="conversation",
        resource_id=conversation_id,
        ip_address=get_client_ip(request)
    )
    
    return {"status": "archived", "id": conversation_id}


@router.delete("/{conversation_id}")
async def delete_conversation(
    request: Request,
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    """Delete a conversation (soft delete)."""
    conv = crud.get_conversation(db, conversation_id)
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": "Conversation not found"}
        )
    
    conv.status = "deleted"
    db.commit()
    
    # Audit log
    log_action(
        db=db,
        user=current_user,
        action=AuditAction.CONVERSATION_DELETE,
        resource_type="conversation",
        resource_id=conversation_id,
        ip_address=get_client_ip(request)
    )
    
    return {"status": "deleted", "id": conversation_id}


@router.get("/{conversation_id}/export")
async def export_conversation(
    conversation_id: str,
    format: str = Query("json", regex="^(json|markdown|txt)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Export a conversation.
    
    - **format**: Export format (json, markdown, txt)
    """
    conv = crud.get_conversation(db, conversation_id)
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": "Conversation not found"}
        )
    
    messages, _ = crud.get_messages(db, conversation_id=conversation_id, page=1, per_page=10000)
    
    if format == "json":
        return {
            "conversation": conversation_to_response(conv).dict(),
            "messages": [message_to_response(m).dict() for m in messages]
        }
    
    elif format == "markdown":
        lines = [f"# {conv.title or 'Conversation'}", ""]
        lines.append(f"**ID:** {conv.id}")
        lines.append(f"**Agent:** {conv.agent_id}")
        lines.append(f"**Created:** {conv.created_at}")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        for msg in messages:
            role_label = {"user": "🧑 User", "assistant": "🤖 Assistant", "system": "⚙️ System"}.get(msg.role, msg.role)
            lines.append(f"### {role_label}")
            lines.append("")
            lines.append(msg.content)
            lines.append("")
            
            if msg.voice_assets:
                for va in msg.voice_assets:
                    lines.append(f"🔊 *Voice attachment: {va.original_filename}*")
                    if va.transcript:
                        lines.append(f"> {va.transcript}")
                    lines.append("")
        
        return {"content": "\n".join(lines), "format": "markdown"}
    
    else:  # txt
        lines = [f"Conversation: {conv.title or conv.id}", "=" * 50, ""]
        
        for msg in messages:
            lines.append(f"[{msg.role.upper()}]")
            lines.append(msg.content)
            lines.append("")
        
        return {"content": "\n".join(lines), "format": "txt"}


@router.get("/{conversation_id}/stats")
async def get_conversation_stats(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get statistics for a conversation."""
    conv = crud.get_conversation(db, conversation_id)
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": "Conversation not found"}
        )
    
    messages, _ = crud.get_messages(db, conversation_id=conversation_id, page=1, per_page=10000)
    
    user_messages = [m for m in messages if m.role == "user"]
    assistant_messages = [m for m in messages if m.role == "assistant"]
    
    avg_latency = 0
    if assistant_messages:
        latencies = [m.latency_ms for m in assistant_messages if m.latency_ms]
        avg_latency = sum(latencies) / len(latencies) if latencies else 0
    
    voice_count = sum(len(m.voice_assets or []) for m in messages)
    
    return {
        "conversation_id": conversation_id,
        "total_messages": len(messages),
        "user_messages": len(user_messages),
        "assistant_messages": len(assistant_messages),
        "total_tokens": conv.total_tokens or 0,
        "average_latency_ms": round(avg_latency, 2),
        "voice_attachments": voice_count,
        "duration_seconds": (conv.updated_at - conv.created_at).total_seconds() if conv.updated_at else 0
    }
