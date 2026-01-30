"""
Advanced features routes: transcript downloads, MCP tool management, memory purging.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import Response
from typing import Optional, List
import csv
import io
import json
import asyncio

from ..session import ChatSession
from ..config import Settings

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
    format: str = Query("markdown", pattern="^(markdown|csv)$"),
    session: ChatSession = Depends(get_chat_session),
):
    """
    Download conversation transcript in Markdown or CSV format.
    
    Args:
        format: Output format - "markdown" or "csv"
        
    Returns:
        File download response
    """
    if not session.history:
        raise HTTPException(status_code=404, detail="No conversation history available")
    
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
    agent_name: Optional[str] = None,
    session_id: Optional[str] = None,
    session: ChatSession = Depends(get_chat_session),
):
    """
    Purge memory for a specific agent or session.
    
    Args:
        agent_name: Name of agent to purge memory for (optional)
        session_id: Session ID to purge memory for (optional)
        session: Current chat session
        
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
        
        # Fixed: Use agent_name for agent_id filter in all cases
        agent.memory.clear(session_id=session_id, agent_id=agent_name)
        return {
            "status": "success",
            "message": f"Memory purged for agent={agent_name}, session={session_id}",
            "entries_cleared": "N/A"  # ChromaDB doesn't return count
        }
    
    # If session_id specified but no agent, purge for all agents in that session
    elif session_id:
        for agent in session.agents:
            agent.memory.clear(session_id=session_id)
        return {
            "status": "success",
            "message": f"Memory purged for all agents in session={session_id}",
            "agents_affected": len(session.agents)
        }
    
    # If neither specified, error
    else:
        raise HTTPException(
            status_code=400,
            detail="Must specify at least one of: agent_name, session_id"
        )


@router.get("/tools/list")
async def list_mcp_tools(
    agent_name: str,
    session: ChatSession = Depends(get_chat_session),
):
    """
    List available MCP tools for an agent.
    
    Args:
        agent_name: Name of the agent
        session: Current chat session
        
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
    agent_name: str,
    tool_name: str,
    arguments: Optional[dict] = None,
    session: ChatSession = Depends(get_chat_session),
):
    """
    Manually trigger an MCP tool call.
    
    Args:
        agent_name: Name of the agent
        tool_name: Name of the tool to call
        arguments: Tool arguments (optional, defaults to empty dict)
        session: Current chat session
        
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
        raise HTTPException(
            status_code=403,
            detail=f"Tool {tool_name} is not in agent's allowed_tools list"
        )
    
    try:
        result = await agent.mcp_client.call_tool(tool_name, arguments)
        return {
            "status": "success",
            "agent": agent_name,
            "tool": tool_name,
            "arguments": arguments,
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tool call failed: {str(e)}")
