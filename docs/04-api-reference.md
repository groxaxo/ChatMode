# API Reference

Complete reference for all REST API endpoints in ChatMode.

---

## Base URL

```
http://localhost:8000
```

---

## Authentication

### Public Endpoints
- `GET /status`
- `GET /` (frontend)

### Protected Endpoints (require authentication)
All Agent Manager and admin endpoints require a valid JWT token.

```http
Authorization: Bearer <jwt_token>
```

### Obtaining a Token

```http
POST /api/v1/auth/login
Content-Type: application/json

{
    "username": "admin",
    "password": "your-password"
}
```

**Response:**
```json
{
    "access_token": "eyJ...",
    "token_type": "bearer",
    "expires_in": 3600
}
```

---

## Session Management

### GET /status

Get current session status and recent messages.

**Response:**
```json
{
    "running": true,
    "topic": "Is artificial consciousness possible?",
    "last_messages": [
        {
            "sender": "Vivian Cross",
            "content": "From a legal standpoint...",
            "audio": "http://localhost:8000/audio/vivian_123456789.mp3"
        }
    ]
}
```

### POST /start

Start a new conversation session.

**Request:**
```http
Content-Type: application/x-www-form-urlencoded

topic=Is+AI+sentient?
```

**Response:** Redirect to `/` (303)

### POST /stop

Stop the current session.

**Response:** Redirect to `/` (303)

### POST /resume

Resume a paused session.

**Response:**
```json
{
    "status": "resumed"
}
```

**Error Response (400):**
```json
{
    "status": "failed",
    "reason": "Already running or no topic"
}
```

### POST /messages

Inject a message into the conversation (admin override).

**Request:**
```http
Content-Type: application/x-www-form-urlencoded

content=Please+focus+on+ethical+implications
sender=Admin
```

**Response:**
```json
{
    "status": "sent"
}
```

### POST /memory/clear

Clear conversation memory.

**Response:**
```json
{
    "status": "memory_cleared"
}
```

---

## Agent Information

### GET /agents

List all configured agents.

**Response:**
```json
{
    "agents": [
        {
            "name": "Vivian Cross",
            "model": "mistral-nemo:12b",
            "api": "ollama"
        },
        {
            "name": "Frankie Grift",
            "model": "llama3.2:3b",
            "api": "ollama"
        }
    ]
}
```

---

## Agent Manager API (v1)

All endpoints prefixed with `/api/v1/`.

### Agents CRUD

#### GET /api/v1/agents

List all agents with full configuration.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | int | 1 | Page number |
| `per_page` | int | 20 | Items per page |
| `enabled` | bool | null | Filter by enabled status |

**Response:**
```json
{
    "items": [
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "name": "lawyer",
            "display_name": "Vivian Cross",
            "model": "mistral-nemo:12b",
            "provider": "ollama",
            "enabled": true,
            "created_at": "2026-01-15T10:30:00Z",
            "updated_at": "2026-01-20T14:22:00Z"
        }
    ],
    "total": 4,
    "page": 1,
    "per_page": 20,
    "pages": 1
}
```

#### POST /api/v1/agents

Create a new agent.

**Request:**
```json
{
    "name": "philosopher",
    "display_name": "Aristotle",
    "system_prompt": "You are Aristotle, the ancient Greek philosopher...",
    "model": "llama3.2:3b",
    "provider": "ollama",
    "api_url": "http://localhost:11434",
    "temperature": 0.8,
    "max_tokens": 512,
    "enabled": true
}
```

**Response (201):**
```json
{
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "name": "philosopher",
    "display_name": "Aristotle",
    "created_at": "2026-01-30T12:00:00Z"
}
```

#### GET /api/v1/agents/{agent_id}

Get a single agent's full configuration.

**Response:**
```json
{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "lawyer",
    "display_name": "Vivian Cross",
    "system_prompt": "You are Vivian Cross, a ruthless trial attorney...",
    "developer_prompt": null,
    "model": "mistral-nemo:12b",
    "provider": "ollama",
    "api_url": "http://localhost:11434",
    "temperature": 0.9,
    "max_tokens": 512,
    "top_p": 1.0,
    "enabled": true,
    "voice_settings": {
        "tts_enabled": true,
        "tts_provider": "openai",
        "tts_model": "tts-1",
        "tts_voice": "alloy",
        "speaking_rate": 1.0
    },
    "memory_settings": {
        "memory_enabled": true,
        "embedding_provider": "ollama",
        "embedding_model": "nomic-embed-text",
        "retention_days": 90,
        "top_k": 5
    },
    "tool_permissions": ["web_search", "calculator"],
    "rate_limits": {
        "requests_per_minute": 60,
        "tokens_per_minute": 100000
    }
}
```

#### PUT /api/v1/agents/{agent_id}

Update an agent's configuration.

**Request:**
```json
{
    "display_name": "Vivian Cross, Esq.",
    "temperature": 0.7,
    "max_tokens": 1024
}
```

**Response:**
```json
{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "updated_at": "2026-01-30T12:30:00Z"
}
```

#### DELETE /api/v1/agents/{agent_id}

Delete an agent (soft delete, sets enabled=false).

**Response:**
```json
{
    "status": "deleted",
    "id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Voice Settings

#### PUT /api/v1/agents/{agent_id}/voice

Update agent voice settings.

**Request:**
```json
{
    "tts_enabled": true,
    "tts_provider": "openai",
    "tts_model": "tts-1-hd",
    "tts_voice": "nova",
    "speaking_rate": 1.1,
    "pitch": 0.0
}
```

### Memory Settings

#### PUT /api/v1/agents/{agent_id}/memory

Update agent memory settings.

**Request:**
```json
{
    "memory_enabled": true,
    "embedding_provider": "openai",
    "embedding_model": "text-embedding-3-small",
    "retention_days": 180,
    "top_k": 10
}
```

#### DELETE /api/v1/agents/{agent_id}/memory

Clear an agent's memory.

**Response:**
```json
{
    "status": "memory_cleared",
    "entries_deleted": 1542
}
```

---

## Voice Attachments API

### POST /api/v1/messages/{message_id}/audio

Upload audio attachment for a message.

**Request:**
```http
Content-Type: multipart/form-data

file: (binary audio data)
```

**Constraints:**
- Max file size: 25MB
- Allowed types: `audio/mp3`, `audio/wav`, `audio/ogg`, `audio/webm`
- Max duration: 300 seconds

**Response (201):**
```json
{
    "id": "audio_550e8400-e29b-41d4-a716-446655440000",
    "message_id": "msg_12345",
    "filename": "voice_message.mp3",
    "mime_type": "audio/mp3",
    "duration": 15.5,
    "size_bytes": 248576,
    "url": "/api/v1/audio/audio_550e8400.../stream",
    "created_at": "2026-01-30T12:00:00Z"
}
```

### GET /api/v1/audio/{audio_id}/stream

Stream audio file with range support.

**Headers:**
```http
Range: bytes=0-65535
```

**Response:**
```http
HTTP/1.1 206 Partial Content
Content-Type: audio/mpeg
Content-Range: bytes 0-65535/248576
Accept-Ranges: bytes

(binary audio data)
```

### GET /api/v1/audio/{audio_id}/download

Download audio file.

**Response:**
```http
Content-Disposition: attachment; filename="voice_message.mp3"
```

### DELETE /api/v1/audio/{audio_id}

Delete audio attachment (requires Admin role).

**Response:**
```json
{
    "status": "deleted"
}
```

---

## Conversations API

### GET /api/v1/conversations

List all conversations.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `page` | int | Page number |
| `per_page` | int | Items per page |
| `start_date` | datetime | Filter by start date |
| `end_date` | datetime | Filter by end date |
| `has_audio` | bool | Filter conversations with audio |

**Response:**
```json
{
    "items": [
        {
            "id": "conv_12345",
            "topic": "Is AI sentient?",
            "started_at": "2026-01-30T10:00:00Z",
            "ended_at": "2026-01-30T10:45:00Z",
            "message_count": 24,
            "audio_count": 12,
            "participants": ["Vivian Cross", "Frankie Grift"]
        }
    ],
    "total": 15
}
```

### GET /api/v1/conversations/{conversation_id}

Get conversation with all messages and audio.

**Response:**
```json
{
    "id": "conv_12345",
    "topic": "Is AI sentient?",
    "messages": [
        {
            "id": "msg_1",
            "sender": "Vivian Cross",
            "sender_id": "agent_lawyer",
            "content": "Objection! The premise assumes...",
            "timestamp": "2026-01-30T10:00:15Z",
            "audio": {
                "id": "audio_abc123",
                "url": "/api/v1/audio/audio_abc123/stream",
                "duration": 12.5
            }
        }
    ]
}
```

---

## Users & RBAC

### GET /api/v1/users

List all users (Admin only).

### POST /api/v1/users

Create a new user.

**Request:**
```json
{
    "username": "moderator1",
    "email": "mod@example.com",
    "password": "secure-password",
    "role": "moderator"
}
```

**Roles:**
| Role | Permissions |
|------|-------------|
| `admin` | Full access, user management, delete |
| `moderator` | Edit agents, view conversations, inject messages |
| `viewer` | Read-only access to conversations |

### PUT /api/v1/users/{user_id}/role

Update user role.

---

## Audit Log

### GET /api/v1/audit

Query audit log (Admin only).

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `user_id` | uuid | Filter by user |
| `action` | string | Filter by action type |
| `resource` | string | Filter by resource |
| `start_date` | datetime | Start of date range |
| `end_date` | datetime | End of date range |

**Response:**
```json
{
    "items": [
        {
            "id": "audit_12345",
            "timestamp": "2026-01-30T12:30:00Z",
            "user_id": "user_admin",
            "username": "admin",
            "action": "agent.update",
            "resource": "agent:lawyer",
            "changes": {
                "temperature": {"old": 0.9, "new": 0.7}
            },
            "ip_address": "192.168.1.100"
        }
    ],
    "total": 156
}
```

---

## Error Responses

All errors follow this format:

```json
{
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Invalid temperature value",
        "details": {
            "field": "temperature",
            "value": 3.0,
            "constraint": "must be between 0.0 and 2.0"
        }
    }
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `UNAUTHORIZED` | 401 | Missing or invalid token |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `VALIDATION_ERROR` | 422 | Invalid request data |
| `RATE_LIMITED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Server error |

---

## Rate Limits

| Endpoint | Limit |
|----------|-------|
| Authentication | 5 req/min |
| Agent updates | 30 req/min |
| Audio upload | 10 req/min |
| Status polling | 60 req/min |

---

## WebSocket (Future)

For real-time updates, a WebSocket endpoint is planned:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    // Handle: new_message, agent_speaking, session_ended
};
```

---

*Next: [Agent System](./05-agent-system.md)*
