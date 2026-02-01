"""
Pydantic schemas for API request/response validation.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, validator

# ============================================================================
# Enums
# ============================================================================


class UserRole(str, Enum):
    ADMIN = "admin"
    MODERATOR = "moderator"
    VIEWER = "viewer"


class SenderType(str, Enum):
    AGENT = "agent"
    ADMIN = "admin"
    USER = "user"


class AgentState(str, Enum):
    """Agent lifecycle states."""

    ACTIVE = "active"
    PAUSED = "paused"
    STOPPED = "stopped"
    FINISHED = "finished"


# ============================================================================
# Authentication
# ============================================================================


class TokenRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    email: Optional[EmailStr] = None
    role: UserRole = UserRole.VIEWER


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    enabled: Optional[bool] = None


class UserResponse(UserBase):
    id: str
    enabled: bool
    created_at: datetime
    last_login: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class UserListResponse(BaseModel):
    items: List["UserResponse"]
    total: int
    page: int
    per_page: int
    pages: int


# ============================================================================
# Agent Settings
# ============================================================================


class VoiceSettingsBase(BaseModel):
    tts_enabled: bool = True
    tts_provider: str = "openai"
    tts_model: str = "tts-1"
    tts_voice: str = "alloy"
    tts_format: str = Field(default="mp3", pattern="^(mp3|opus|aac|flac|wav|pcm)$")
    tts_speed: float = Field(default=1.0, ge=0.25, le=4.0)
    tts_instructions: Optional[str] = None
    speaking_rate: float = Field(default=1.0, ge=0.5, le=2.0)
    pitch: float = Field(default=0.0, ge=-1.0, le=1.0)
    stt_enabled: bool = False
    stt_provider: Optional[str] = None
    stt_model: Optional[str] = None


class VoiceSettingsUpdate(BaseModel):
    tts_enabled: Optional[bool] = None
    tts_provider: Optional[str] = None
    tts_model: Optional[str] = None
    tts_voice: Optional[str] = None
    tts_format: Optional[str] = Field(
        default=None, pattern="^(mp3|opus|aac|flac|wav|pcm)$"
    )
    tts_speed: Optional[float] = Field(default=None, ge=0.25, le=4.0)
    tts_instructions: Optional[str] = None
    speaking_rate: Optional[float] = Field(default=None, ge=0.5, le=2.0)
    pitch: Optional[float] = Field(default=None, ge=-1.0, le=1.0)
    stt_enabled: Optional[bool] = None
    stt_provider: Optional[str] = None
    stt_model: Optional[str] = None


class MemorySettingsBase(BaseModel):
    memory_enabled: bool = True
    embedding_provider: str = "ollama"
    embedding_model: str = "nomic-embed-text"
    embedding_base_url: Optional[str] = None
    retention_days: int = Field(default=90, ge=1, le=365)
    top_k: int = Field(default=5, ge=1, le=50)


class MemorySettingsUpdate(BaseModel):
    memory_enabled: Optional[bool] = None
    embedding_provider: Optional[str] = None
    embedding_model: Optional[str] = None
    embedding_base_url: Optional[str] = None
    retention_days: Optional[int] = Field(default=None, ge=1, le=365)
    top_k: Optional[int] = Field(default=None, ge=1, le=50)


class PermissionsBase(BaseModel):
    tool_permissions: List[str] = []
    allowed_topics: List[str] = []
    blocked_topics: List[str] = []
    # Content filter settings
    filter_enabled: bool = False
    blocked_words: List[str] = []
    filter_action: str = Field(default="block", pattern="^(block|warn|censor)$")
    filter_message: str = (
        "This message contains inappropriate content and has been blocked."
    )
    rate_limit_rpm: int = Field(default=60, ge=1)
    rate_limit_tpm: int = Field(default=100000, ge=1)


class PermissionsUpdate(BaseModel):
    tool_permissions: Optional[List[str]] = None
    allowed_topics: Optional[List[str]] = None
    blocked_topics: Optional[List[str]] = None
    # Content filter settings
    filter_enabled: Optional[bool] = None
    blocked_words: Optional[List[str]] = None
    filter_action: Optional[str] = Field(default=None, pattern="^(block|warn|censor)$")
    filter_message: Optional[str] = None
    rate_limit_rpm: Optional[int] = Field(default=None, ge=1)
    rate_limit_tpm: Optional[int] = Field(default=None, ge=1)


# ============================================================================
# Agents
# ============================================================================


class AgentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    display_name: Optional[str] = Field(None, max_length=200)
    system_prompt: Optional[str] = None
    developer_prompt: Optional[str] = None
    model: str = Field(..., min_length=1, max_length=200)
    provider: str = Field(default="ollama", max_length=50)
    api_url: Optional[str] = Field(None, max_length=500)
    temperature: float = Field(default=0.9, ge=0.0, le=2.0)
    max_tokens: int = Field(default=512, ge=1, le=128000)
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    stop_sequences: List[str] = []
    sleep_seconds: Optional[float] = Field(default=None, ge=0.0)
    enabled: bool = True


class AgentCreate(AgentBase):
    api_key: Optional[str] = None  # Will be encrypted before storage
    voice_settings: Optional[VoiceSettingsBase] = None
    memory_settings: Optional[MemorySettingsBase] = None
    permissions: Optional[PermissionsBase] = None


class AgentUpdate(BaseModel):
    display_name: Optional[str] = None
    system_prompt: Optional[str] = None
    developer_prompt: Optional[str] = None
    model: Optional[str] = None
    provider: Optional[str] = None
    api_url: Optional[str] = None
    api_key: Optional[str] = None  # Will be encrypted if provided
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, ge=1, le=128000)
    top_p: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    stop_sequences: Optional[List[str]] = None
    sleep_seconds: Optional[float] = Field(default=None, ge=0.0)
    enabled: Optional[bool] = None


class AgentResponse(AgentBase):
    id: str
    created_at: datetime
    updated_at: datetime
    voice_settings: Optional[VoiceSettingsBase] = None
    memory_settings: Optional[MemorySettingsBase] = None
    permissions: Optional[PermissionsBase] = None

    model_config = ConfigDict(from_attributes=True)


class AgentListResponse(BaseModel):
    items: List[AgentResponse]
    total: int
    page: int
    per_page: int
    pages: int


# ============================================================================
# Conversations & Messages
# ============================================================================


class AudioInfo(BaseModel):
    id: str
    url: str
    duration: Optional[float]
    size_bytes: Optional[int]
    mime_type: Optional[str]


class MessageBase(BaseModel):
    sender: str
    sender_id: Optional[str] = None
    sender_type: SenderType = SenderType.AGENT
    content: str
    timestamp: datetime


class MessageResponse(MessageBase):
    id: str
    model: Optional[str] = None
    tokens_used: Optional[int] = None
    # Legacy audio field
    audio: Optional[AudioInfo] = None
    # New audio fields
    audio_url: Optional[str] = None
    audio_format: Optional[str] = None
    audio_mime: Optional[str] = None
    audio_cached: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)


class MessageListResponse(BaseModel):
    items: List[MessageResponse]
    total: int
    page: int
    per_page: int
    pages: int


class ConversationBase(BaseModel):
    topic: str


class ConversationCreate(ConversationBase):
    pass


class ConversationResponse(ConversationBase):
    id: str
    started_at: datetime
    ended_at: Optional[datetime]
    is_active: bool
    message_count: int = 0
    audio_count: int = 0
    participants: List[str] = []

    model_config = ConfigDict(from_attributes=True)


class ConversationDetailResponse(ConversationResponse):
    messages: List[MessageResponse] = []


class ConversationListResponse(BaseModel):
    items: List[ConversationResponse]
    total: int
    page: int
    per_page: int


# ============================================================================
# Voice Assets
# ============================================================================


class VoiceAssetCreate(BaseModel):
    message_id: str


class VoiceAssetResponse(BaseModel):
    id: str
    message_id: str
    filename: str
    mime_type: str
    duration: Optional[float]
    size_bytes: int
    url: str
    created_at: datetime


class VoiceAssetListResponse(BaseModel):
    items: List[VoiceAssetResponse]
    total: int
    page: int
    per_page: int
    pages: int

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Audit Log
# ============================================================================


class AuditLogEntry(BaseModel):
    id: str
    timestamp: datetime
    user_id: Optional[str]
    username: Optional[str]
    action: str
    resource_type: str
    resource_id: Optional[str]
    changes: Optional[Dict[str, Any]]
    ip_address: Optional[str]

    model_config = ConfigDict(from_attributes=True)


# Single audit log is just AuditLogEntry
AuditLogResponse = AuditLogEntry


class AuditLogListResponse(BaseModel):
    items: List[AuditLogEntry]
    total: int
    page: int
    per_page: int
    pages: int


# ============================================================================
# Status & Health
# ============================================================================


class AgentStateInfo(BaseModel):
    """Information about an agent's current state."""

    state: AgentState
    changed_at: str
    reason: Optional[str] = None
    has_active_task: bool = False


class AgentStatesResponse(BaseModel):
    """Response containing all agent states."""

    agent_states: Dict[str, AgentStateInfo]


class SessionStatus(BaseModel):
    running: bool
    topic: Optional[str]
    session_id: Optional[str]
    last_messages: List[Dict[str, Any]]
    agent_states: Dict[str, AgentStateInfo]


class HealthCheck(BaseModel):
    status: str
    database: bool
    version: str


# ============================================================================
# Error Response
# ============================================================================


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    error: ErrorDetail
