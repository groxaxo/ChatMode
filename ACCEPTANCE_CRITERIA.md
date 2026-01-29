# ChatMode Acceptance Criteria & Testing Checklist

## Overview

This document defines the acceptance criteria for the ChatMode Agent Manager system.
Use this checklist to verify all features are working correctly before deployment.

---

## 1. Authentication & Authorization

### 1.1 User Login
- [ ] **AC-1.1.1**: User can login with valid username/password
- [ ] **AC-1.1.2**: Invalid credentials return 401 error
- [ ] **AC-1.1.3**: JWT token is returned on successful login
- [ ] **AC-1.1.4**: Token contains user ID, username, and role
- [ ] **AC-1.1.5**: Token expires after configured duration (default: 24h)

### 1.2 Role-Based Access Control (RBAC)
- [ ] **AC-1.2.1**: Admin can access all endpoints
- [ ] **AC-1.2.2**: Moderator can manage agents but not users
- [ ] **AC-1.2.3**: Viewer has read-only access
- [ ] **AC-1.2.4**: Unauthorized access returns 403 error

### 1.3 Session Management
- [ ] **AC-1.3.1**: Logout endpoint revokes session
- [ ] **AC-1.3.2**: `/me` endpoint returns current user info
- [ ] **AC-1.3.3**: Expired tokens are rejected

---

## 2. Agent Management

### 2.1 Agent CRUD
- [ ] **AC-2.1.1**: Create agent with all required fields
- [ ] **AC-2.1.2**: Agent names must be unique
- [ ] **AC-2.1.3**: Update agent preserves unmodified fields
- [ ] **AC-2.1.4**: Delete performs soft-delete (agent disabled)
- [ ] **AC-2.1.5**: List agents supports pagination
- [ ] **AC-2.1.6**: Filter agents by enabled status

### 2.2 Agent Configuration
- [ ] **AC-2.2.1**: System prompt can be up to 32KB
- [ ] **AC-2.2.2**: Developer prompt stored separately from system prompt
- [ ] **AC-2.2.3**: Model parameters (temp, max_tokens, top_p) are validated
- [ ] **AC-2.2.4**: API key is encrypted at rest
- [ ] **AC-2.2.5**: Provider can be set to openai or ollama

### 2.3 Voice Settings
- [ ] **AC-2.3.1**: TTS can be enabled/disabled per agent
- [ ] **AC-2.3.2**: TTS provider, model, voice are configurable
- [ ] **AC-2.3.3**: Speaking rate (0.5-2.0) is validated
- [ ] **AC-2.3.4**: STT settings are separate from TTS

### 2.4 Memory Settings
- [ ] **AC-2.4.1**: Long-term memory can be enabled/disabled
- [ ] **AC-2.4.2**: Embedding provider/model are configurable
- [ ] **AC-2.4.3**: Retention period (days) is configurable
- [ ] **AC-2.4.4**: Top-K retrieval count is configurable
- [ ] **AC-2.4.5**: Memory can be cleared without deleting agent

### 2.5 Permissions
- [ ] **AC-2.5.1**: Tool permissions list is configurable
- [ ] **AC-2.5.2**: Allowed/blocked topics are configurable
- [ ] **AC-2.5.3**: Rate limits (RPM, TPM) are configurable
- [ ] **AC-2.5.4**: Only admins can modify permissions

---

## 3. Voice/Audio Management

### 3.1 Audio Upload
- [ ] **AC-3.1.1**: Upload accepts mp3, wav, ogg, webm, m4a formats
- [ ] **AC-3.1.2**: File size limit (default 10MB) is enforced
- [ ] **AC-3.1.3**: Invalid file types return 415 error
- [ ] **AC-3.1.4**: Files are stored with unique generated names
- [ ] **AC-3.1.5**: Original filename is preserved in metadata

### 3.2 Audio Streaming
- [ ] **AC-3.2.1**: Stream endpoint returns audio with correct MIME type
- [ ] **AC-3.2.2**: Download endpoint sets Content-Disposition: attachment
- [ ] **AC-3.2.3**: Range requests are supported for seeking
- [ ] **AC-3.2.4**: Missing files return 404 error

### 3.3 Audio Attachment
- [ ] **AC-3.3.1**: Audio can be attached to any message
- [ ] **AC-3.3.2**: Multiple audio files can attach to one message
- [ ] **AC-3.3.3**: Audio can be uploaded before message exists
- [ ] **AC-3.3.4**: Transcript can be added/updated

### 3.4 Admin Review
- [ ] **AC-3.4.1**: Conversations show voice attachments inline
- [ ] **AC-3.4.2**: Audio plays in browser without download
- [ ] **AC-3.4.3**: File size is displayed
- [ ] **AC-3.4.4**: Transcript is shown if available

---

## 4. Conversation Management

### 4.1 Conversation Listing
- [ ] **AC-4.1.1**: List supports pagination
- [ ] **AC-4.1.2**: Filter by agent ID
- [ ] **AC-4.1.3**: Filter by status (active, archived, deleted)
- [ ] **AC-4.1.4**: Shows message count and token count

### 4.2 Message Retrieval
- [ ] **AC-4.2.1**: Messages ordered chronologically
- [ ] **AC-4.2.2**: Includes role, content, agent_id
- [ ] **AC-4.2.3**: Includes token count and latency
- [ ] **AC-4.2.4**: Voice assets are nested in response

### 4.3 Conversation Actions
- [ ] **AC-4.3.1**: Archive sets status to "archived"
- [ ] **AC-4.3.2**: Delete sets status to "deleted" (soft delete)
- [ ] **AC-4.3.3**: Export supports JSON, Markdown, TXT formats
- [ ] **AC-4.3.4**: Stats endpoint returns aggregated metrics

---

## 5. User Management (Admin Only)

### 5.1 User CRUD
- [ ] **AC-5.1.1**: Create user with username, password, role
- [ ] **AC-5.1.2**: Usernames must be unique
- [ ] **AC-5.1.3**: Emails must be unique (if provided)
- [ ] **AC-5.1.4**: Password is hashed with bcrypt
- [ ] **AC-5.1.5**: Delete removes user (admin cannot delete self)

### 5.2 User Status
- [ ] **AC-5.2.1**: Enable/disable endpoint toggles account
- [ ] **AC-5.2.2**: Disabled users cannot login
- [ ] **AC-5.2.3**: Admin cannot disable self

### 5.3 Role Management
- [ ] **AC-5.3.1**: Change role endpoint updates user role
- [ ] **AC-5.3.2**: Valid roles: admin, moderator, viewer
- [ ] **AC-5.3.3**: Role change is audited

---

## 6. Audit Logging

### 6.1 Event Capture
- [ ] **AC-6.1.1**: All CRUD operations are logged
- [ ] **AC-6.1.2**: Login/logout events are logged
- [ ] **AC-6.1.3**: Permission changes are logged
- [ ] **AC-6.1.4**: Audio upload/delete is logged

### 6.2 Audit Details
- [ ] **AC-6.2.1**: Logs include user ID and username
- [ ] **AC-6.2.2**: Logs include action type
- [ ] **AC-6.2.3**: Logs include resource type and ID
- [ ] **AC-6.2.4**: Logs include change details (old/new values)
- [ ] **AC-6.2.5**: Logs include IP address and user agent

### 6.3 Audit Queries
- [ ] **AC-6.3.1**: List supports pagination
- [ ] **AC-6.3.2**: Filter by user, action, resource_type
- [ ] **AC-6.3.3**: Filter by date range
- [ ] **AC-6.3.4**: Resource history shows all changes to one entity
- [ ] **AC-6.3.5**: Stats summary aggregates by action type

---

## 7. Frontend (Agent Manager UI)

### 7.1 Login
- [ ] **AC-7.1.1**: Login modal appears when not authenticated
- [ ] **AC-7.1.2**: Error message shown for invalid credentials
- [ ] **AC-7.1.3**: Token persisted in localStorage
- [ ] **AC-7.1.4**: Logout clears token and shows login

### 7.2 Agent Tab
- [ ] **AC-7.2.1**: Agent table shows all agents
- [ ] **AC-7.2.2**: TTS/Memory status shown with icons
- [ ] **AC-7.2.3**: Create agent opens modal
- [ ] **AC-7.2.4**: Edit loads existing values
- [ ] **AC-7.2.5**: Delete confirms before action

### 7.3 Conversation Tab
- [ ] **AC-7.3.1**: Conversation list loads on tab switch
- [ ] **AC-7.3.2**: Selecting conversation shows messages
- [ ] **AC-7.3.3**: Voice attachments have inline player
- [ ] **AC-7.3.4**: Export button downloads file

### 7.4 Users Tab (Admin)
- [ ] **AC-7.4.1**: Tab only visible to admins
- [ ] **AC-7.4.2**: User table shows all users
- [ ] **AC-7.4.3**: Role badges use distinct colors
- [ ] **AC-7.4.4**: Enable/disable toggles status

### 7.5 Audit Tab (Admin)
- [ ] **AC-7.5.1**: Tab only visible to admins
- [ ] **AC-7.5.2**: Shows recent audit log entries
- [ ] **AC-7.5.3**: Action type shown as badge
- [ ] **AC-7.5.4**: Resource ID is truncated for display

---

## 8. API Documentation

### 8.1 OpenAPI/Swagger
- [ ] **AC-8.1.1**: `/docs` serves Swagger UI
- [ ] **AC-8.1.2**: `/redoc` serves ReDoc
- [ ] **AC-8.1.3**: All endpoints are documented
- [ ] **AC-8.1.4**: Request/response schemas shown
- [ ] **AC-8.1.5**: Auth requirements indicated

---

## 9. Golden Path Demo

### 9.1 Bootstrap
- [ ] **AC-9.1.1**: `bootstrap.py` creates admin user
- [ ] **AC-9.1.2**: Database tables are created
- [ ] **AC-9.1.3**: Duplicate run is idempotent

### 9.2 Demo Setup
- [ ] **AC-9.2.1**: `demo_setup.py` creates Sage agent
- [ ] **AC-9.2.2**: Sage has memory enabled
- [ ] **AC-9.2.3**: `demo_setup.py` creates Echo agent
- [ ] **AC-9.2.4**: Echo has TTS enabled
- [ ] **AC-9.2.5**: Moderator and viewer users created

---

## Testing Commands

```bash
# 1. Initialize database and create admin
python bootstrap.py --username admin --password admin123

# 2. Start the server
uvicorn web_admin:app --host 0.0.0.0 --port 8000 --reload

# 3. Run demo setup (in another terminal)
python demo_setup.py

# 4. Open Agent Manager UI
# http://localhost:8000/frontend/agent_manager.html

# 5. Run API tests (if pytest tests exist)
pytest tests/ -v

# 6. Manual API testing with curl
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -F "username=admin" -F "password=admin123"

# List agents (with token)
curl -H "Authorization: Bearer <TOKEN>" \
  http://localhost:8000/api/v1/agents/
```

---

## Sign-Off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Developer | | | |
| QA | | | |
| Product Owner | | | |

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-01-XX | AI Assistant | Initial acceptance criteria |
