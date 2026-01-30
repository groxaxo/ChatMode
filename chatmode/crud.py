"""
CRUD operations for database models.
"""

from datetime import datetime
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func

from .models import (
    User, Agent, AgentVoiceSettings, AgentMemorySettings, AgentPermissions,
    Conversation, Message, VoiceAsset, AuditLog
)
from .schemas import (
    AgentCreate, AgentUpdate, VoiceSettingsUpdate, MemorySettingsUpdate,
    PermissionsUpdate, UserCreate, UserUpdate
)
from .auth import hash_password, encrypt_api_key


# ============================================================================
# Users
# ============================================================================

def get_user(db: Session, user_id: str) -> Optional[User]:
    """Get user by ID."""
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Get user by username."""
    return db.query(User).filter(User.username == username).first()


def get_users(db: Session, page: int = 1, per_page: int = 20) -> Tuple[List[User], int]:
    """Get paginated list of users."""
    total = db.query(func.count(User.id)).scalar()
    users = db.query(User).offset((page - 1) * per_page).limit(per_page).all()
    return users, total


def create_user(db: Session, user_data: UserCreate) -> User:
    """Create a new user."""
    user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        role=user_data.role.value
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, user_id: str, user_data: UserUpdate) -> Optional[User]:
    """Update a user."""
    user = get_user(db, user_id)
    if not user:
        return None
    
    update_data = user_data.dict(exclude_unset=True)
    if 'role' in update_data:
        update_data['role'] = update_data['role'].value
    
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user_id: str) -> bool:
    """Delete a user (soft delete by disabling)."""
    user = get_user(db, user_id)
    if not user:
        return False
    
    user.enabled = False
    db.commit()
    return True


# ============================================================================
# Agents
# ============================================================================

def get_agent(db: Session, agent_id: str) -> Optional[Agent]:
    """Get agent by ID."""
    return db.query(Agent).filter(Agent.id == agent_id).first()


def get_agent_by_name(db: Session, name: str) -> Optional[Agent]:
    """Get agent by name."""
    return db.query(Agent).filter(Agent.name == name).first()


def get_agents(
    db: Session,
    page: int = 1,
    per_page: int = 20,
    enabled: Optional[bool] = None
) -> Tuple[List[Agent], int]:
    """Get paginated list of agents."""
    query = db.query(Agent)
    
    if enabled is not None:
        query = query.filter(Agent.enabled == enabled)
    
    total = query.count()
    agents = query.offset((page - 1) * per_page).limit(per_page).all()
    
    return agents, total


def create_agent(
    db: Session,
    agent_data: AgentCreate,
    created_by: Optional[str] = None
) -> Agent:
    """Create a new agent with related settings."""
    # Create main agent record
    agent = Agent(
        name=agent_data.name,
        display_name=agent_data.display_name,
        system_prompt=agent_data.system_prompt,
        developer_prompt=agent_data.developer_prompt,
        model=agent_data.model,
        provider=agent_data.provider,
        api_url=agent_data.api_url,
        api_key_encrypted=encrypt_api_key(agent_data.api_key) if agent_data.api_key else None,
        temperature=agent_data.temperature,
        max_tokens=agent_data.max_tokens,
        top_p=agent_data.top_p,
        stop_sequences=agent_data.stop_sequences,
        enabled=agent_data.enabled,
        created_by=created_by,
        updated_by=created_by
    )
    db.add(agent)
    db.flush()  # Get agent.id
    
    # Create voice settings
    voice_data = agent_data.voice_settings or {}
    voice_settings = AgentVoiceSettings(
        agent_id=agent.id,
        **voice_data.dict() if hasattr(voice_data, 'dict') else voice_data
    )
    db.add(voice_settings)
    
    # Create memory settings
    memory_data = agent_data.memory_settings or {}
    memory_settings = AgentMemorySettings(
        agent_id=agent.id,
        **memory_data.dict() if hasattr(memory_data, 'dict') else memory_data
    )
    db.add(memory_settings)
    
    # Create permissions
    perms_data = agent_data.permissions or {}
    permissions = AgentPermissions(
        agent_id=agent.id,
        **perms_data.dict() if hasattr(perms_data, 'dict') else perms_data
    )
    db.add(permissions)
    
    db.commit()
    db.refresh(agent)
    
    return agent


def update_agent(
    db: Session,
    agent_id: str,
    agent_data: AgentUpdate,
    updated_by: Optional[str] = None
) -> Optional[Agent]:
    """Update an agent."""
    agent = get_agent(db, agent_id)
    if not agent:
        return None
    
    update_data = agent_data.dict(exclude_unset=True)
    
    # Handle API key encryption
    if 'api_key' in update_data:
        api_key = update_data.pop('api_key')
        if api_key:
            update_data['api_key_encrypted'] = encrypt_api_key(api_key)
    
    for field, value in update_data.items():
        setattr(agent, field, value)
    
    agent.updated_by = updated_by
    agent.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(agent)
    
    return agent


def delete_agent(db: Session, agent_id: str) -> bool:
    """Delete an agent (soft delete)."""
    agent = get_agent(db, agent_id)
    if not agent:
        return False
    
    agent.enabled = False
    agent.updated_at = datetime.utcnow()
    db.commit()
    
    return True


def update_agent_voice_settings(
    db: Session,
    agent_id: str,
    settings_data: VoiceSettingsUpdate
) -> Optional[AgentVoiceSettings]:
    """Update agent voice settings."""
    agent = get_agent(db, agent_id)
    if not agent:
        return None
    
    if not agent.voice_settings:
        agent.voice_settings = AgentVoiceSettings(agent_id=agent_id)
        db.add(agent.voice_settings)
    
    update_data = settings_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(agent.voice_settings, field, value)
    
    agent.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(agent.voice_settings)
    
    return agent.voice_settings


def update_agent_memory_settings(
    db: Session,
    agent_id: str,
    settings_data: MemorySettingsUpdate
) -> Optional[AgentMemorySettings]:
    """Update agent memory settings."""
    agent = get_agent(db, agent_id)
    if not agent:
        return None
    
    if not agent.memory_settings:
        agent.memory_settings = AgentMemorySettings(agent_id=agent_id)
        db.add(agent.memory_settings)
    
    update_data = settings_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(agent.memory_settings, field, value)
    
    agent.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(agent.memory_settings)
    
    return agent.memory_settings


def update_agent_permissions(
    db: Session,
    agent_id: str,
    perms_data: PermissionsUpdate
) -> Optional[AgentPermissions]:
    """Update agent permissions."""
    agent = get_agent(db, agent_id)
    if not agent:
        return None
    
    if not agent.permissions:
        agent.permissions = AgentPermissions(agent_id=agent_id)
        db.add(agent.permissions)
    
    update_data = perms_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(agent.permissions, field, value)
    
    agent.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(agent.permissions)
    
    return agent.permissions


# ============================================================================
# Conversations
# ============================================================================

def get_conversation(db: Session, conversation_id: str) -> Optional[Conversation]:
    """Get conversation by ID."""
    return db.query(Conversation).filter(Conversation.id == conversation_id).first()


def get_conversations(
    db: Session,
    page: int = 1,
    per_page: int = 20,
    is_active: Optional[bool] = None,
    has_audio: Optional[bool] = None
) -> Tuple[List[Conversation], int]:
    """Get paginated list of conversations."""
    query = db.query(Conversation)
    
    if is_active is not None:
        query = query.filter(Conversation.is_active == is_active)
    
    total = query.count()
    conversations = query.order_by(Conversation.started_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
    
    return conversations, total


def create_conversation(db: Session, topic: str, settings_snapshot: dict = None) -> Conversation:
    """Create a new conversation."""
    conversation = Conversation(
        topic=topic,
        settings_snapshot=settings_snapshot
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


def end_conversation(db: Session, conversation_id: str) -> Optional[Conversation]:
    """Mark a conversation as ended."""
    conversation = get_conversation(db, conversation_id)
    if not conversation:
        return None
    
    conversation.is_active = False
    conversation.ended_at = datetime.utcnow()
    db.commit()
    db.refresh(conversation)
    
    return conversation


def delete_conversation(db: Session, conversation_id: str) -> bool:
    """Delete a conversation and all related data."""
    conversation = get_conversation(db, conversation_id)
    if not conversation:
        return False
    
    db.delete(conversation)
    db.commit()
    return True


# ============================================================================
# Messages
# ============================================================================

def create_message(
    db: Session,
    conversation_id: str,
    sender: str,
    content: str,
    sender_id: Optional[str] = None,
    sender_type: str = "agent",
    model: Optional[str] = None,
    tokens_used: Optional[int] = None,
    generation_time_ms: Optional[int] = None
) -> Message:
    """Create a new message."""
    message = Message(
        conversation_id=conversation_id,
        sender=sender,
        sender_id=sender_id,
        sender_type=sender_type,
        content=content,
        model=model,
        tokens_used=tokens_used,
        generation_time_ms=generation_time_ms
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def get_messages(
    db: Session,
    conversation_id: str,
    limit: int = 100
) -> List[Message]:
    """Get messages for a conversation."""
    return db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.timestamp).limit(limit).all()


# ============================================================================
# Voice Assets
# ============================================================================

def create_voice_asset(
    db: Session,
    message_id: str,
    filename: str,
    storage_path: str,
    mime_type: str,
    size_bytes: int,
    duration_seconds: Optional[float] = None,
    checksum: Optional[str] = None,
    original_filename: Optional[str] = None,
    created_by: Optional[str] = None,
    expires_at: Optional[datetime] = None
) -> VoiceAsset:
    """Create a voice asset record."""
    asset = VoiceAsset(
        message_id=message_id,
        filename=filename,
        original_filename=original_filename,
        storage_path=storage_path,
        mime_type=mime_type,
        size_bytes=size_bytes,
        duration_seconds=duration_seconds,
        checksum=checksum,
        created_by=created_by,
        expires_at=expires_at
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


def get_voice_asset(db: Session, asset_id: str) -> Optional[VoiceAsset]:
    """Get voice asset by ID."""
    return db.query(VoiceAsset).filter(VoiceAsset.id == asset_id).first()


def get_voice_asset_by_message(db: Session, message_id: str) -> Optional[VoiceAsset]:
    """Get voice asset for a message."""
    return db.query(VoiceAsset).filter(VoiceAsset.message_id == message_id).first()


def delete_voice_asset(db: Session, asset_id: str) -> bool:
    """Delete a voice asset."""
    asset = get_voice_asset(db, asset_id)
    if not asset:
        return False
    
    db.delete(asset)
    db.commit()
    return True


# ============================================================================
# Audit Log
# ============================================================================

def get_audit_logs(
    db: Session,
    page: int = 1,
    per_page: int = 50,
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> Tuple[List[AuditLog], int]:
    """Get paginated audit logs with filters."""
    query = db.query(AuditLog)
    
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if action:
        query = query.filter(AuditLog.action == action)
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)
    if start_date:
        query = query.filter(AuditLog.timestamp >= start_date)
    if end_date:
        query = query.filter(AuditLog.timestamp <= end_date)
    
    total = query.count()
    logs = query.order_by(AuditLog.timestamp.desc()).offset((page - 1) * per_page).limit(per_page).all()
    
    return logs, total
