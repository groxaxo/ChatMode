"""
Database models for ChatMode Agent Manager.

This module defines SQLAlchemy models for:
- Users and authentication
- Agents and their settings
- Conversations and messages
- Voice assets
- Audit logging
"""

import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column,
    String,
    Text,
    Boolean,
    Float,
    Integer,
    DateTime,
    ForeignKey,
    JSON,
    Index,
    UniqueConstraint,
    CheckConstraint,
    Enum as SQLEnum,
)
from sqlalchemy.dialects.postgresql import UUID, INET, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()


def generate_uuid():
    return str(uuid.uuid4())


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    MODERATOR = "moderator"
    VIEWER = "viewer"


class User(Base):
    """User account for authentication and RBAC."""

    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default=UserRole.VIEWER.value)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    # Relationships
    audit_logs = relationship("AuditLog", back_populates="user", lazy="dynamic")
    created_agents = relationship(
        "Agent", foreign_keys="Agent.created_by", back_populates="creator"
    )

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"


class Agent(Base):
    """AI agent configuration."""

    __tablename__ = "agents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(String(200), nullable=True)

    # Prompts
    system_prompt = Column(Text, nullable=True)
    developer_prompt = Column(Text, nullable=True)

    # Model configuration
    model = Column(String(200), nullable=False)
    provider = Column(String(50), nullable=False, default="ollama")
    api_url = Column(String(500), nullable=True)
    api_key_encrypted = Column(String(500), nullable=True)

    # Generation parameters
    temperature = Column(Float, default=0.9)
    max_tokens = Column(Integer, default=512)
    top_p = Column(Float, default=1.0)
    stop_sequences = Column(JSON, default=list)

    # Status
    enabled = Column(Boolean, default=True, index=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Ownership
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    updated_by = Column(String(36), ForeignKey("users.id"), nullable=True)

    # Relationships
    creator = relationship(
        "User", foreign_keys=[created_by], back_populates="created_agents"
    )
    voice_settings = relationship(
        "AgentVoiceSettings",
        back_populates="agent",
        uselist=False,
        cascade="all, delete-orphan",
    )
    memory_settings = relationship(
        "AgentMemorySettings",
        back_populates="agent",
        uselist=False,
        cascade="all, delete-orphan",
    )
    permissions = relationship(
        "AgentPermissions",
        back_populates="agent",
        uselist=False,
        cascade="all, delete-orphan",
    )
    messages = relationship("Message", back_populates="agent", lazy="dynamic")

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "temperature >= 0 AND temperature <= 2", name="check_temperature"
        ),
        CheckConstraint(
            "max_tokens >= 1 AND max_tokens <= 128000", name="check_max_tokens"
        ),
        CheckConstraint("top_p >= 0 AND top_p <= 1", name="check_top_p"),
    )

    def __repr__(self):
        return f"<Agent {self.name} ({self.provider}/{self.model})>"


class AgentVoiceSettings(Base):
    """Voice/TTS settings for an agent."""

    __tablename__ = "agent_voice_settings"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    agent_id = Column(
        String(36),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    # TTS settings
    tts_enabled = Column(Boolean, default=True)
    tts_provider = Column(String(50), default="openai")
    tts_model = Column(String(100), default="tts-1")
    tts_voice = Column(String(100), default="alloy")
    speaking_rate = Column(Float, default=1.0)
    pitch = Column(Float, default=0.0)

    # STT settings
    stt_enabled = Column(Boolean, default=False)
    stt_provider = Column(String(50), nullable=True)
    stt_model = Column(String(100), nullable=True)

    # Relationship
    agent = relationship("Agent", back_populates="voice_settings")

    __table_args__ = (
        CheckConstraint(
            "speaking_rate >= 0.5 AND speaking_rate <= 2.0", name="check_speaking_rate"
        ),
        CheckConstraint("pitch >= -1.0 AND pitch <= 1.0", name="check_pitch"),
    )


class AgentMemorySettings(Base):
    """Memory/embedding settings for an agent."""

    __tablename__ = "agent_memory_settings"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    agent_id = Column(
        String(36),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    # Memory settings
    memory_enabled = Column(Boolean, default=True)
    embedding_provider = Column(String(50), default="ollama")
    embedding_model = Column(String(100), default="nomic-embed-text")
    embedding_base_url = Column(String(500), nullable=True)
    retention_days = Column(Integer, default=90)
    top_k = Column(Integer, default=5)

    # Relationship
    agent = relationship("Agent", back_populates="memory_settings")

    __table_args__ = (
        CheckConstraint(
            "retention_days >= 1 AND retention_days <= 365", name="check_retention"
        ),
        CheckConstraint("top_k >= 1 AND top_k <= 50", name="check_top_k"),
    )


class AgentPermissions(Base):
    """Permissions and rate limits for an agent."""

    __tablename__ = "agent_permissions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    agent_id = Column(
        String(36),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    # Tool permissions (JSON array of allowed tool names)
    tool_permissions = Column(JSON, default=list)

    # Topic restrictions (JSON arrays)
    allowed_topics = Column(JSON, default=list)
    blocked_topics = Column(JSON, default=list)

    # Content filter settings
    filter_enabled = Column(Boolean, default=False)
    blocked_words = Column(JSON, default=list)  # List of words/phrases to block
    filter_action = Column(String(20), default="block")  # "block", "warn", "censor"
    filter_message = Column(
        Text,
        default="This message contains inappropriate content and has been blocked.",
    )

    # Rate limits
    rate_limit_rpm = Column(Integer, default=60)  # Requests per minute
    rate_limit_tpm = Column(Integer, default=100000)  # Tokens per minute

    # Relationship
    agent = relationship("Agent", back_populates="permissions")


class Conversation(Base):
    """A conversation session between agents."""

    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    topic = Column(Text, nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

    # Metadata
    settings_snapshot = Column(JSON, nullable=True)  # Capture settings at start

    # Relationships
    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.timestamp",
    )

    __table_args__ = (
        Index("idx_conversation_active", "is_active"),
        Index("idx_conversation_started", "started_at"),
    )

    def __repr__(self):
        return f"<Conversation {self.id[:8]} topic='{self.topic[:30]}...'>"


class Message(Base):
    """A single message in a conversation."""

    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    conversation_id = Column(
        String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )

    # Sender info
    sender = Column(String(200), nullable=False)  # Display name
    sender_id = Column(
        String(36), ForeignKey("agents.id"), nullable=True
    )  # NULL for admin/human
    sender_type = Column(String(20), default="agent")  # 'agent', 'admin', 'user'

    # Content
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Generation metadata
    model = Column(String(200), nullable=True)
    tokens_used = Column(Integer, nullable=True)
    generation_time_ms = Column(Integer, nullable=True)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    agent = relationship("Agent", back_populates="messages")
    voice_asset = relationship(
        "VoiceAsset",
        back_populates="message",
        uselist=False,
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_message_conversation", "conversation_id"),
        Index("idx_message_timestamp", "timestamp"),
        Index("idx_message_sender", "sender_id"),
    )

    def __repr__(self):
        return f"<Message {self.sender}: {self.content[:30]}...>"


class VoiceAsset(Base):
    """Audio attachment for a message."""

    __tablename__ = "voice_assets"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    message_id = Column(
        String(36),
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    # File info
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=True)
    storage_path = Column(String(500), nullable=False)
    mime_type = Column(String(100), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    duration_seconds = Column(Float, nullable=True)
    checksum = Column(String(64), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)

    # Creator
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True)

    # Relationship
    message = relationship("Message", back_populates="voice_asset")

    __table_args__ = (
        Index("idx_voice_message", "message_id"),
        Index("idx_voice_expires", "expires_at"),
    )

    def __repr__(self):
        return f"<VoiceAsset {self.filename} ({self.duration_seconds}s)>"


class AuditLog(Base):
    """Audit log for administrative actions."""

    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # Who
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    username = Column(String(100), nullable=True)  # Denormalized for history

    # What
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(36), nullable=True)

    # Details
    changes = Column(JSON, nullable=True)  # {"field": {"old": x, "new": y}}

    # Context
    ip_address = Column(String(45), nullable=True)  # IPv6 max length
    user_agent = Column(Text, nullable=True)

    # Relationship
    user = relationship("User", back_populates="audit_logs")

    __table_args__ = (
        Index("idx_audit_user", "user_id"),
        Index("idx_audit_resource", "resource_type", "resource_id"),
    )

    def __repr__(self):
        return f"<AuditLog {self.action} by {self.username} at {self.timestamp}>"


# Helper for creating all tables
def create_all_tables(engine):
    """Create all database tables."""
    Base.metadata.create_all(engine)


def drop_all_tables(engine):
    """Drop all database tables (use with caution!)."""
    Base.metadata.drop_all(engine)
