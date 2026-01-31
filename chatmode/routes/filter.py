"""
Content Filter Routes

Routes for managing the global content filter.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/v1/filter", tags=["filter"])

# We'll inject the session reference on startup
_chat_session = None


def set_filter_session(session):
    """Set the chat session for filter operations."""
    global _chat_session
    _chat_session = session


class FilterToggleRequest(BaseModel):
    """Request model for toggling filter."""
    enabled: bool


class FilterStatusResponse(BaseModel):
    """Response model for filter status."""
    enabled: bool
    action: Optional[str] = None
    blocked_words_count: int = 0
    message: Optional[str] = None


@router.get("/status", response_model=FilterStatusResponse)
async def get_filter_status():
    """Get current content filter status."""
    if _chat_session is None:
        raise HTTPException(status_code=500, detail="Session not initialized")
    
    if _chat_session.content_filter:
        return FilterStatusResponse(
            enabled=_chat_session.content_filter.enabled,
            action=_chat_session.content_filter.action,
            blocked_words_count=len(_chat_session.content_filter.blocked_words),
        )
    else:
        return FilterStatusResponse(
            enabled=False,
            message="No filter configured"
        )


@router.post("/toggle")
async def toggle_filter(request: FilterToggleRequest):
    """Toggle content filter on/off globally."""
    if _chat_session is None:
        raise HTTPException(status_code=500, detail="Session not initialized")
    
    if _chat_session.content_filter:
        _chat_session.content_filter.enabled = request.enabled
        return {
            "status": "filter_toggled",
            "enabled": request.enabled,
            "message": f"Content filter {'enabled' if request.enabled else 'disabled'}",
        }
    else:
        raise HTTPException(status_code=400, detail="No content filter configured")


@router.post("/reload")
async def reload_filter():
    """Reload content filter settings from database."""
    if _chat_session is None:
        raise HTTPException(status_code=500, detail="Session not initialized")
    
    try:
        from ..database import get_db
        from ..content_filter import ContentFilter, create_filter_from_permissions
        from .. import crud

        db = next(get_db())
        try:
            agents, _ = crud.get_agents(db, page=1, per_page=1, enabled=True)
            if agents and agents[0].permissions:
                perms = agents[0].permissions
                filter_instance = create_filter_from_permissions(
                    {
                        "filter_enabled": perms.filter_enabled,
                        "blocked_words": perms.blocked_words,
                        "filter_action": perms.filter_action,
                        "filter_message": perms.filter_message,
                    }
                )
                _chat_session.set_content_filter(filter_instance)
                return {
                    "status": "filter_reloaded",
                    "enabled": filter_instance.enabled,
                    "blocked_words_count": len(filter_instance.blocked_words),
                    "source_agent": agents[0].name,
                }

            # No enabled agent with permissions - set disabled filter
            default_filter = ContentFilter(
                enabled=False,
                blocked_words=[],
                action="block",
                filter_message="This message contains inappropriate content and has been blocked.",
            )
            _chat_session.set_content_filter(default_filter)
            return {
                "status": "no_filter_configured",
                "enabled": False,
                "blocked_words_count": 0,
                "message": "No enabled agent with filter permissions found",
            }
        finally:
            db.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
