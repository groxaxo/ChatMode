"""
Advanced features routes: transcript downloads, MCP tool management, memory purging.
"""

from fastapi import APIRouter, HTTPException, Query, Depends, Request
from fastapi.responses import Response
from typing import Optional, List
import csv
import io
import json
import asyncio

from ..session import ChatSession
from ..state_sync import sync_profiles_from_db
from ..config import Settings
from ..auth import get_current_user, require_role
from ..models import User
from ..database import get_db
from ..audit import log_action, get_client_ip, AuditAction
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/v1", tags=["advanced"])

# Global session reference - will be set by main.py
_global_chat_session: Optional[ChatSession] = None

def set_global_chat_session(session: ChatSession):
    """Set the global chat session reference."""
    global _global_chat_session
    _global_chat_session = session

def get_chat_session() -> ChatSession:
    """Dependency to get the chat session."""
    if _global_chat_session is None:
        raise HTTPException(status_code=500, detail="Chat session not initialized")
    return _global_chat_session


@router.get("/transcript/download")
async def download_transcript(
    request: Request,
    format: str = Query("markdown", pattern="^(markdown|csv)$"),
    session: ChatSession = Depends(get_chat_session),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Download conversation transcript in Markdown or CSV format (requires authentication).
    
    Args:
        format: Output format - "markdown" or "csv"
        session: Current chat session
        current_user: Authenticated user
        db: Database session
        
    Returns:
        File download response
    """
    if not session.history:
        raise HTTPException(status_code=404, detail="No conversation history available")
    
    # Audit log
    log_action(
        db=db,
        user=current_user,
        action=AuditAction.AGENT_READ,
        resource_type="transcript",
        resource_id=str(session.session_id),
        changes={"format": format, "messages_count": len(session.history)},
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent")
    )
    
    if format == "markdown":
        # Generate Markdown transcript
        lines = [
            f"# Conversation Transcript",
            f"",
            f"**Topic:** {session.topic}",
            f"**Session ID:** {session.session_id}",
            f"",
            f"---",
            f"",
        ]
        
        for msg in session.history:
            sender = msg.get("sender", "Unknown")
            content = msg.get("content", "")
            lines.append(f"## {sender}")
            lines.append(f"")
            lines.append(content)
            lines.append(f"")
            lines.append(f"---")
            lines.append(f"")
        
        transcript = "\n".join(lines)
        
        return Response(
            content=transcript,
            media_type="text/markdown",
            headers={
                "Content-Disposition": f'attachment; filename="transcript_{session.session_id}.md"'
            },
        )
    
    else:  # CSV format
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(["Sender", "Content", "Audio"])
        
        # Write messages
        for msg in session.history:
            writer.writerow([
                msg.get("sender", "Unknown"),
                msg.get("content", ""),
                msg.get("audio", ""),
            ])
        
        csv_content = output.getvalue()
        
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="transcript_{session.session_id}.csv"'
            },
        )


@router.post("/memory/purge")
async def purge_memory(
    request: Request,
    agent_name: Optional[str] = None,
    session_id: Optional[str] = None,
    session: ChatSession = Depends(get_chat_session),
    current_user: User = Depends(require_role(["admin", "moderator"])),
    db: Session = Depends(get_db),
):
    """
    Purge memory for a specific agent or session (admin/moderator only).
    
    This endpoint deletes memory entries from ChromaDB. Access is restricted
    to admin and moderator roles for security.
    
    Args:
        agent_name: Name of agent to purge memory for (optional)
        session_id: Session ID to purge memory for (optional)
        session: Current chat session
        current_user: Authenticated user with admin/moderator role
        db: Database session
        
    Returns:
        Status message
    """
    if not session.agents:
        raise HTTPException(status_code=400, detail="No agents loaded in session")
    
    # If agent_name specified, purge that agent's memory
    if agent_name:
        agent = next((a for a in session.agents if a.name == agent_name), None)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")
        
        # Get count before clearing
        entries_before = agent.memory.count()
        
        # Fixed: Use agent_name for agent_id filter in all cases
        agent.memory.clear(session_id=session_id, agent_id=agent_name)
        
        entries_after = agent.memory.count()
        entries_cleared = entries_before - entries_after
        
        # Audit log
        log_action(
            db=db,
            user=current_user,
            action=AuditAction.AGENT_MEMORY_CLEAR,
            resource_type="agent_memory",
            resource_id=agent_name,
            changes={
                "agent": agent_name,
                "session_id": session_id,
                "entries_cleared": entries_cleared
            },
            ip_address=get_client_ip(request),
            user_agent=request.headers.get("user-agent")
        )
        
        return {
            "status": "success",
            "message": f"Memory purged for agent={agent_name}, session={session_id}",
            "entries_cleared": entries_cleared
        }
    
    # If session_id specified but no agent, purge for all agents in that session
    elif session_id:
        total_cleared = 0
        for agent in session.agents:
            entries_before = agent.memory.count()
            agent.memory.clear(session_id=session_id)
            entries_after = agent.memory.count()
            total_cleared += (entries_before - entries_after)
        
        # Audit log
        log_action(
            db=db,
            user=current_user,
            action=AuditAction.AGENT_MEMORY_CLEAR,
            resource_type="session_memory",
            resource_id=session_id,
            changes={
                "session_id": session_id,
                "agents_affected": len(session.agents),
                "total_entries_cleared": total_cleared
            },
            ip_address=get_client_ip(request),
            user_agent=request.headers.get("user-agent")
        )
        
        return {
            "status": "success",
            "message": f"Memory purged for all agents in session={session_id}",
            "agents_affected": len(session.agents),
            "total_entries_cleared": total_cleared
        }
    
    # If neither specified, error
    else:
        raise HTTPException(
            status_code=400,
            detail="Must specify at least one of: agent_name, session_id"
        )


@router.get("/tools/list")
async def list_mcp_tools(
    request: Request,
    agent_name: str,
    session: ChatSession = Depends(get_chat_session),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List available MCP tools for an agent (requires authentication).
    
    Args:
        agent_name: Name of the agent
        session: Current chat session
        current_user: Authenticated user
        db: Database session
        
    Returns:
        List of available tools
    """
    if not session.agents:
        raise HTTPException(status_code=400, detail="No agents loaded in session")
    
    agent = next((a for a in session.agents if a.name == agent_name), None)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")
    
    if not agent.mcp_client:
        return {
            "agent": agent_name,
            "tools": [],
            "message": "Agent does not have MCP configured"
        }
    
    try:
        tools = await agent.mcp_client.list_tools()
        
        # Audit log for tool listing
        log_action(
            db=db,
            user=current_user,
            action=AuditAction.TOOL_LIST,
            resource_type="mcp_tools",
            resource_id=agent_name,
            changes={"tools_count": len(tools)},
            ip_address=get_client_ip(request),
            user_agent=request.headers.get("user-agent")
        )
        
        return {
            "agent": agent_name,
            "tools": tools,
            "allowed_tools": agent.allowed_tools,
            "count": len(tools)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list tools: {str(e)}")


@router.post("/tools/call")
async def call_mcp_tool(
    request: Request,
    agent_name: str,
    tool_name: str,
    arguments: Optional[dict] = None,
    session: ChatSession = Depends(get_chat_session),
    current_user: User = Depends(require_role(["admin", "moderator"])),
    db: Session = Depends(get_db),
):
    """
    Manually trigger an MCP tool call (admin/moderator only).
    
    This is a powerful endpoint that allows manual tool execution.
    Access is restricted to admin and moderator roles for security.
    
    Args:
        agent_name: Name of the agent
        tool_name: Name of the tool to call
        arguments: Tool arguments (optional, defaults to empty dict)
        session: Current chat session
        current_user: Authenticated user with admin/moderator role
        db: Database session
        
    Returns:
        Tool execution result
    """
    if arguments is None:
        arguments = {}
    
    if not session.agents:
        raise HTTPException(status_code=400, detail="No agents loaded in session")
    
    agent = next((a for a in session.agents if a.name == agent_name), None)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")
    
    if not agent.mcp_client:
        raise HTTPException(status_code=400, detail="Agent does not have MCP configured")
    
    # Security check: Verify tool is in allowed_tools
    if tool_name not in agent.allowed_tools:
        # Audit failed attempt
        log_action(
            db=db,
            user=current_user,
            action=AuditAction.TOOL_CALL,
            resource_type="mcp_tool_call",
            resource_id=agent_name,
            changes={
                "tool": tool_name,
                "status": "forbidden",
                "reason": "not_in_allowed_tools"
            },
            ip_address=get_client_ip(request),
            user_agent=request.headers.get("user-agent")
        )
        
        raise HTTPException(
            status_code=403,
            detail=f"Tool {tool_name} is not in agent's allowed_tools list"
        )
    
    # Validate arguments to prevent injection attacks
    try:
        if not isinstance(arguments, dict):
            raise ValueError("Arguments must be a dictionary")
        
        # Check for suspicious patterns in string arguments
        for key, value in arguments.items():
            if isinstance(value, str):
                # Basic sanitization checks
                if len(value) > 10000:  # Prevent extremely long inputs
                    raise ValueError(f"Argument '{key}' exceeds maximum length")
    except Exception as e:
        log_action(
            db=db,
            user=current_user,
            action=AuditAction.TOOL_CALL,
            resource_type="mcp_tool_call",
            resource_id=agent_name,
            changes={
                "tool": tool_name,
                "status": "validation_failed",
                "error": str(e)
            },
            ip_address=get_client_ip(request),
            user_agent=request.headers.get("user-agent")
        )
        raise HTTPException(status_code=400, detail=f"Invalid arguments: {str(e)}")
    
    try:
        result = await agent.mcp_client.call_tool(tool_name, arguments)
        
        # Audit successful tool execution
        log_action(
            db=db,
            user=current_user,
            action=AuditAction.TOOL_CALL,
            resource_type="mcp_tool_call",
            resource_id=agent_name,
            changes={
                "tool": tool_name,
                "arguments": arguments,
                "status": "success"
            },
            ip_address=get_client_ip(request),
            user_agent=request.headers.get("user-agent")

        @router.post("/state/sync")
        async def sync_state(
            request: Request,
            session: ChatSession = Depends(get_chat_session),
            current_user: User = Depends(require_role(["admin", "moderator"])),
            db: Session = Depends(get_db),
        ):
            """Synchronize agent state across DB, profiles, memory, and MCP."""
            profile_sync = sync_profiles_from_db(db=db, include_disabled=False)
            runtime_state = await session.sync_state()

            log_action(
                db=db,
                user=current_user,
                action=AuditAction.AGENT_UPDATE,
                resource_type="state_sync",
                resource_id=session.session_id or "none",
                changes={"profile_sync": profile_sync, "agent_count": len(session.agents)},
                ip_address=get_client_ip(request),
                user_agent=request.headers.get("user-agent"),
            )

            return {
                "status": "synced",
                "profiles": profile_sync,
                "agent_states": runtime_state,
            }
        )
        
        return {
            "status": "success",
            "agent": agent_name,
            "tool": tool_name,
            "arguments": arguments,
            "result": result
        }
    except Exception as e:
        # Audit failed tool execution
        log_action(
            db=db,
            user=current_user,
            action=AuditAction.TOOL_CALL,
            resource_type="mcp_tool_call",
            resource_id=agent_name,
            changes={
                "tool": tool_name,
                "arguments": arguments,
                "status": "failed",
                "error": str(e)
            },
            ip_address=get_client_ip(request),
            user_agent=request.headers.get("user-agent")
        )
        raise HTTPException(status_code=500, detail="Tool call failed")
