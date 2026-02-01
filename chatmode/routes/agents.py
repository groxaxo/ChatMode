"""
Agent management routes.
"""

import math
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from .. import crud
from ..audit import AuditAction, compute_changes, get_client_ip, log_action
from ..auth import get_current_user, require_role
from ..database import get_db
from ..models import User
from ..schemas import (
    AgentCreate,
    AgentListResponse,
    AgentResponse,
    AgentUpdate,
    ErrorResponse,
    MemorySettingsBase,
    MemorySettingsUpdate,
    PermissionsBase,
    PermissionsUpdate,
    VoiceSettingsBase,
    VoiceSettingsUpdate,
)

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])


def agent_to_response(agent) -> AgentResponse:
    """Convert agent model to response schema."""
    voice_settings = None
    if agent.voice_settings:
        voice_settings = VoiceSettingsBase(
            tts_enabled=agent.voice_settings.tts_enabled,
            tts_provider=agent.voice_settings.tts_provider,
            tts_model=agent.voice_settings.tts_model,
            tts_voice=agent.voice_settings.tts_voice,
            speaking_rate=agent.voice_settings.speaking_rate,
            pitch=agent.voice_settings.pitch,
            stt_enabled=agent.voice_settings.stt_enabled,
            stt_provider=agent.voice_settings.stt_provider,
            stt_model=agent.voice_settings.stt_model,
        )

    memory_settings = None
    if agent.memory_settings:
        memory_settings = MemorySettingsBase(
            memory_enabled=agent.memory_settings.memory_enabled,
            embedding_provider=agent.memory_settings.embedding_provider,
            embedding_model=agent.memory_settings.embedding_model,
            embedding_base_url=agent.memory_settings.embedding_base_url,
            retention_days=agent.memory_settings.retention_days,
            top_k=agent.memory_settings.top_k,
        )

    permissions = None
    if agent.permissions:
        permissions = PermissionsBase(
            tool_permissions=agent.permissions.tool_permissions or [],
            allowed_topics=agent.permissions.allowed_topics or [],
            blocked_topics=agent.permissions.blocked_topics or [],
            filter_enabled=(
                agent.permissions.filter_enabled
                if agent.permissions.filter_enabled is not None
                else True
            ),
            blocked_words=agent.permissions.blocked_words or [],
            filter_action=agent.permissions.filter_action or "block",
            filter_message=agent.permissions.filter_message
            or "This message contains inappropriate content and has been blocked.",
            rate_limit_rpm=agent.permissions.rate_limit_rpm,
            rate_limit_tpm=agent.permissions.rate_limit_tpm,
        )

    return AgentResponse(
        id=agent.id,
        name=agent.name,
        display_name=agent.display_name,
        system_prompt=agent.system_prompt,
        developer_prompt=agent.developer_prompt,
        model=agent.model,
        provider=agent.provider,
        api_url=agent.api_url,
        temperature=agent.temperature,
        max_tokens=agent.max_tokens,
        top_p=agent.top_p,
        stop_sequences=agent.stop_sequences or [],
        sleep_seconds=agent.sleep_seconds,
        enabled=agent.enabled,
        created_at=agent.created_at,
        updated_at=agent.updated_at,
        voice_settings=voice_settings,
        memory_settings=memory_settings,
        permissions=permissions,
    )


@router.get("/", response_model=AgentListResponse)
async def list_agents(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    enabled: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all agents with pagination."""
    agents, total = crud.get_agents(db, page=page, per_page=per_page, enabled=enabled)

    return AgentListResponse(
        items=[agent_to_response(a) for a in agents],
        total=total,
        page=page,
        per_page=per_page,
        pages=math.ceil(total / per_page) if total > 0 else 1,
    )


@router.post("/", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    request: Request,
    agent_data: AgentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "moderator"])),
):
    """Create a new agent."""
    # Check for duplicate name
    existing = crud.get_agent_by_name(db, agent_data.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "CONFLICT",
                "message": f"Agent with name '{agent_data.name}' already exists",
            },
        )

    agent = crud.create_agent(db, agent_data, created_by=current_user.id)

    # Audit log
    log_action(
        db=db,
        user=current_user,
        action=AuditAction.AGENT_CREATE,
        resource_type="agent",
        resource_id=agent.id,
        changes={"created": agent_data.model_dump(exclude={"api_key"})},
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )

    return agent_to_response(agent)


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single agent by ID."""
    agent = crud.get_agent(db, agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": "Agent not found"},
        )

    return agent_to_response(agent)


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    request: Request,
    agent_id: str,
    agent_data: AgentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "moderator"])),
):
    """Update an agent."""
    agent = crud.get_agent(db, agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": "Agent not found"},
        )

    # Compute changes for audit
    update_data = agent_data.model_dump(exclude_unset=True)
    changes = compute_changes(agent, update_data, list(update_data.keys()))

    updated_agent = crud.update_agent(
        db, agent_id, agent_data, updated_by=current_user.id
    )

    # Audit log
    if changes:
        log_action(
            db=db,
            user=current_user,
            action=AuditAction.AGENT_UPDATE,
            resource_type="agent",
            resource_id=agent_id,
            changes=changes,
            ip_address=get_client_ip(request),
            user_agent=request.headers.get("user-agent"),
        )

    return agent_to_response(updated_agent)


@router.delete("/{agent_id}")
async def delete_agent(
    request: Request,
    agent_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"])),
):
    """Delete an agent (soft delete)."""
    agent = crud.get_agent(db, agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": "Agent not found"},
        )

    crud.delete_agent(db, agent_id)

    # Audit log
    log_action(
        db=db,
        user=current_user,
        action=AuditAction.AGENT_DELETE,
        resource_type="agent",
        resource_id=agent_id,
        changes={"deleted": True, "name": agent.name},
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )

    return {"status": "deleted", "id": agent_id}


# ============================================================================
# Voice Settings
# ============================================================================


@router.put("/{agent_id}/voice", response_model=VoiceSettingsBase)
async def update_voice_settings(
    request: Request,
    agent_id: str,
    settings: VoiceSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "moderator"])),
):
    """Update agent voice settings."""
    agent = crud.get_agent(db, agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": "Agent not found"},
        )

    updated = crud.update_agent_voice_settings(db, agent_id, settings)

    # Audit log
    log_action(
        db=db,
        user=current_user,
        action=AuditAction.AGENT_VOICE_UPDATE,
        resource_type="agent",
        resource_id=agent_id,
        changes=settings.model_dump(exclude_unset=True),
        ip_address=get_client_ip(request),
    )

    return VoiceSettingsBase(
        tts_enabled=updated.tts_enabled,
        tts_provider=updated.tts_provider,
        tts_model=updated.tts_model,
        tts_voice=updated.tts_voice,
        speaking_rate=updated.speaking_rate,
        pitch=updated.pitch,
        stt_enabled=updated.stt_enabled,
        stt_provider=updated.stt_provider,
        stt_model=updated.stt_model,
    )


# ============================================================================
# Memory Settings
# ============================================================================


@router.put("/{agent_id}/memory", response_model=MemorySettingsBase)
async def update_memory_settings(
    request: Request,
    agent_id: str,
    settings: MemorySettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "moderator"])),
):
    """Update agent memory settings."""
    agent = crud.get_agent(db, agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": "Agent not found"},
        )

    updated = crud.update_agent_memory_settings(db, agent_id, settings)

    # Audit log
    log_action(
        db=db,
        user=current_user,
        action=AuditAction.AGENT_MEMORY_UPDATE,
        resource_type="agent",
        resource_id=agent_id,
        changes=settings.model_dump(exclude_unset=True),
        ip_address=get_client_ip(request),
    )

    return MemorySettingsBase(
        memory_enabled=updated.memory_enabled,
        embedding_provider=updated.embedding_provider,
        embedding_model=updated.embedding_model,
        embedding_base_url=updated.embedding_base_url,
        retention_days=updated.retention_days,
        top_k=updated.top_k,
    )


@router.delete("/{agent_id}/memory")
async def clear_agent_memory(
    request: Request,
    agent_id: str,
    session_id: Optional[str] = Query(
        None, description="Optional session ID to clear memory for specific session"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "moderator"])),
):
    """
    Clear an agent's long-term memory.

    This endpoint deletes embeddings from the ChromaDB vector store for the specified agent.
    If session_id is provided, only memory for that session is cleared.
    Otherwise, all memory for the agent is cleared.
    """
    from ..config import Settings
    from ..memory import MemoryStore
    from ..providers import build_embedding_provider

    agent = crud.get_agent(db, agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": "Agent not found"},
        )

    # Initialize settings and memory store to perform actual deletion
    try:
        settings = Settings()

        # Build embedding provider for memory store
        embedding_provider = build_embedding_provider(
            provider=settings.embedding_provider,
            base_url=settings.embedding_base_url,
            api_key=settings.embedding_api_key or settings.openai_api_key,
            model=settings.embedding_model,
        )

        # Create memory store instance for this agent
        # Use agent name as collection name (matching how ChatAgent initializes it)
        memory_store = MemoryStore(
            collection_name=f"{agent.name}_memory",
            persist_dir=settings.chroma_dir,
            embedding_provider=embedding_provider,
        )

        # Clear memory with appropriate filters
        entries_before = memory_store.count()
        memory_store.clear(session_id=session_id, agent_id=agent.name)
        entries_after = memory_store.count()
        entries_cleared = entries_before - entries_after

        # Audit log
        changes = {"entries_cleared": entries_cleared, "agent_name": agent.name}
        if session_id:
            changes["session_id"] = session_id

        log_action(
            db=db,
            user=current_user,
            action=AuditAction.AGENT_MEMORY_CLEAR,
            resource_type="agent",
            resource_id=agent_id,
            changes=changes,
            ip_address=get_client_ip(request),
            user_agent=request.headers.get("user-agent"),
        )

        return {
            "status": "memory_cleared",
            "agent_id": agent_id,
            "agent_name": agent.name,
            "entries_cleared": entries_cleared,
            "session_id": session_id,
        }
    except Exception as e:
        # Log the error but still audit the attempt
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Failed to clear memory for agent {agent_id}: {e}")

        log_action(
            db=db,
            user=current_user,
            action=AuditAction.AGENT_MEMORY_CLEAR,
            resource_type="agent",
            resource_id=agent_id,
            changes={"error": "Memory clear failed", "session_id": session_id},
            ip_address=get_client_ip(request),
            user_agent=request.headers.get("user-agent"),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "MEMORY_CLEAR_FAILED",
                "message": "Failed to clear memory. Please contact administrator.",
            },
        )


# ============================================================================
# Permissions
# ============================================================================


@router.put("/{agent_id}/permissions", response_model=PermissionsBase)
async def update_permissions(
    request: Request,
    agent_id: str,
    permissions: PermissionsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"])),
):
    """Update agent permissions (admin only)."""
    agent = crud.get_agent(db, agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": "Agent not found"},
        )

    updated = crud.update_agent_permissions(db, agent_id, permissions)

    # Audit log
    log_action(
        db=db,
        user=current_user,
        action=AuditAction.AGENT_PERMISSIONS_UPDATE,
        resource_type="agent",
        resource_id=agent_id,
        changes=permissions.model_dump(exclude_unset=True),
        ip_address=get_client_ip(request),
    )

    return PermissionsBase(
        tool_permissions=updated.tool_permissions or [],
        allowed_topics=updated.allowed_topics or [],
        blocked_topics=updated.blocked_topics or [],
        filter_enabled=(
            updated.filter_enabled if updated.filter_enabled is not None else True
        ),
        blocked_words=updated.blocked_words or [],
        filter_action=updated.filter_action or "block",
        filter_message=updated.filter_message
        or "This message contains inappropriate content and has been blocked.",
        rate_limit_rpm=updated.rate_limit_rpm,
        rate_limit_tpm=updated.rate_limit_tpm,
    )
