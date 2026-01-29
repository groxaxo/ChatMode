"""
Audit logging utilities.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from models import AuditLog, User


def log_action(
    db: Session,
    user: Optional[User],
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    changes: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> AuditLog:
    """
    Log an administrative action to the audit log.
    
    Args:
        db: Database session
        user: User performing the action (or None for system actions)
        action: Action identifier (e.g., "agent.create", "agent.update")
        resource_type: Type of resource (e.g., "agent", "user", "conversation")
        resource_id: ID of the affected resource
        changes: Dictionary of changes {"field": {"old": x, "new": y}}
        ip_address: Client IP address
        user_agent: Client user agent string
    
    Returns:
        Created AuditLog entry
    """
    entry = AuditLog(
        user_id=user.id if user else None,
        username=user.username if user else "system",
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        changes=changes,
        ip_address=ip_address,
        user_agent=user_agent,
        timestamp=datetime.utcnow()
    )
    
    db.add(entry)
    db.commit()
    db.refresh(entry)
    
    return entry


def compute_changes(old_obj: Any, new_data: Dict[str, Any], fields: list) -> Dict[str, Dict[str, Any]]:
    """
    Compute the changes between old object and new data.
    
    Args:
        old_obj: The original object (SQLAlchemy model)
        new_data: Dictionary of new values
        fields: List of field names to compare
    
    Returns:
        Dictionary of changes {"field": {"old": x, "new": y}}
    """
    changes = {}
    
    for field in fields:
        if field not in new_data:
            continue
        
        old_value = getattr(old_obj, field, None)
        new_value = new_data[field]
        
        # Skip if values are equal
        if old_value == new_value:
            continue
        
        # Redact sensitive fields
        if field in {"api_key", "password", "api_key_encrypted"}:
            changes[field] = {"old": "[REDACTED]", "new": "[REDACTED]"}
        else:
            changes[field] = {"old": old_value, "new": new_value}
    
    return changes


def get_client_ip(request) -> Optional[str]:
    """Extract client IP from request, handling proxies."""
    # Check for X-Forwarded-For header (when behind proxy)
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    # Check for X-Real-IP header
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip
    
    # Fall back to direct client IP
    if hasattr(request, "client") and request.client:
        return request.client.host
    
    return None


# Standard audit actions
class AuditAction:
    """Standard audit action identifiers."""
    
    # User actions
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    USER_CREATE = "user.create"
    USER_UPDATE = "user.update"
    USER_DELETE = "user.delete"
    USER_PASSWORD_CHANGE = "user.password_change"
    
    # Agent actions
    AGENT_CREATE = "agent.create"
    AGENT_UPDATE = "agent.update"
    AGENT_DELETE = "agent.delete"
    AGENT_VOICE_UPDATE = "agent.voice_update"
    AGENT_MEMORY_UPDATE = "agent.memory_update"
    AGENT_MEMORY_CLEAR = "agent.memory_clear"
    AGENT_PERMISSIONS_UPDATE = "agent.permissions_update"
    
    # Conversation actions
    CONVERSATION_START = "conversation.start"
    CONVERSATION_STOP = "conversation.stop"
    CONVERSATION_DELETE = "conversation.delete"
    MESSAGE_INJECT = "conversation.message_inject"
    
    # Voice asset actions
    AUDIO_UPLOAD = "audio.upload"
    AUDIO_DELETE = "audio.delete"
    
    # System actions
    SYSTEM_CONFIG_CHANGE = "system.config_change"
    SYSTEM_MAINTENANCE = "system.maintenance"
