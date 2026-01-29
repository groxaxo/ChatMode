# Assumptions & Design Decisions

This document records the assumptions made during development and the rationale behind key design decisions.

---

## Assumptions

### A1: Single-Instance Deployment (Initial)

**Assumption:** The initial deployment runs as a single instance without horizontal scaling requirements.

**Rationale:** 
- Simplifies state management (in-memory sessions)
- Reduces infrastructure complexity
- Appropriate for small-to-medium deployments

**Migration Path:**
- Move session state to Redis
- Use database for message queue
- Deploy behind load balancer

---

### A2: SQLite for Development, PostgreSQL for Production

**Assumption:** SQLite is sufficient for development and small deployments; production uses PostgreSQL.

**Rationale:**
- SQLite requires no setup
- File-based, easy to backup
- PostgreSQL for concurrent access and scaling

**Implementation:**
```python
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/chatmode.db")
```

---

### A3: Local File Storage for Audio (Default)

**Assumption:** Audio files are stored on local filesystem by default.

**Rationale:**
- Simplest implementation
- No cloud dependencies
- Suitable for single-server deployment

**Migration Path:**
- Implement S3/Azure Blob adapter
- Update storage_path to use object store URLs
- Use signed URLs for access

---

### A4: JWT Authentication with Symmetric Keys

**Assumption:** JWT tokens use HS256 (symmetric) signing.

**Rationale:**
- Simpler key management
- Sufficient for single-domain deployment
- Easy to rotate secrets

**Alternative:** RS256 (asymmetric) for distributed verification

---

### A5: ChromaDB for Vector Storage

**Assumption:** ChromaDB is sufficient for memory/embedding storage.

**Rationale:**
- Embedded, no separate service
- Persistent storage
- Good for moderate scale (~100k vectors)

**Migration Path:** Pinecone, Weaviate, or pgvector for larger scale

---

### A6: Soft Deletes for Agents

**Assumption:** Deleting an agent sets `enabled=false` rather than removing the record.

**Rationale:**
- Preserves audit trail
- Allows restoration
- Maintains referential integrity with conversations

---

### A7: Round-Robin Turn-Taking

**Assumption:** Agents take turns in fixed order during conversations.

**Rationale:**
- Predictable behavior
- Simple to implement
- Easy to debug

**Alternative Strategies:**
- Reactive (respond when mentioned)
- LLM-selected (model decides who speaks)
- User-directed (admin picks next speaker)

---

### A8: English-Only UI and Documentation

**Assumption:** All UI text and documentation is in English.

**Rationale:**
- Simplifies initial development
- Common language for technical content

**Migration Path:** Add i18n framework for localization

---

### A9: Admin Manages All Agents

**Assumption:** Any admin can edit any agent (no per-agent ownership).

**Rationale:**
- Simpler permission model
- Appropriate for small teams

**Alternative:** Per-agent ownership with delegation

---

### A10: Audio Retention Policy

**Assumption:** Default 30-day retention for uploaded audio files.

**Rationale:**
- Balance storage cost with usefulness
- Configurable via environment

---

## Design Decisions

### D1: Provider Abstraction Pattern

**Decision:** Abstract LLM and embedding interactions behind interfaces.

```python
class ChatProvider:
    def chat(self, model, messages, temperature, max_tokens, options) -> str:
        raise NotImplementedError
```

**Benefits:**
- Easy to add new providers
- Mockable for testing
- Clean separation of concerns

---

### D2: Agent Profiles as JSON

**Decision:** Store agent personalities as JSON files, not in code.

**Benefits:**
- Non-developers can customize
- Version-controllable
- Hot-reloadable
- Easy to share/export

**Trade-off:** Less type safety than code-based config

---

### D3: Dual Storage for Agent Config

**Decision:** Support both JSON files and database for agent configuration.

**Rationale:**
- JSON for simple deployments
- Database for Agent Manager features
- Migration path from simple to advanced

**Implementation:** `AgentLoader` checks database first, falls back to JSON

---

### D4: Audit Logging for All Admin Actions

**Decision:** Log every administrative change with before/after state.

**Benefits:**
- Compliance requirements
- Debug capability
- Accountability

**Implementation:**
```python
log_action(user, "agent.update", resource_id, {"temperature": {"old": 0.9, "new": 0.7}})
```

---

### D5: Embedding Per-Agent Memory

**Decision:** Each agent has its own ChromaDB collection for memory.

**Benefits:**
- Memory isolation
- Targeted retrieval
- Easy to clear individual agent memory

**Trade-off:** More collections to manage

---

### D6: TTS as Optional Feature

**Decision:** TTS is disabled by default and opt-in via configuration.

**Rationale:**
- Reduces external dependencies
- Faster without TTS
- Not all use cases need voice

---

### D7: CORS Permissive in Development

**Decision:** Allow all origins in development mode.

**Rationale:**
- Simplifies frontend development
- Vite dev server on different port

**Production:** Configure specific allowed origins

---

### D8: Stateless API with Session Context

**Decision:** API endpoints are stateless; session state managed by `ChatSession`.

**Benefits:**
- Easier to scale (with shared state)
- Clear separation
- Standard REST patterns

---

### D9: Audio Streaming with Range Support

**Decision:** Support HTTP Range requests for audio playback.

**Benefits:**
- Seeking without full download
- Bandwidth efficient
- Standard browser support

---

### D10: Role-Based Access Control (RBAC)

**Decision:** Three-tier role system: Admin > Moderator > Viewer.

| Action | Admin | Moderator | Viewer |
|--------|-------|-----------|--------|
| View agents | ✓ | ✓ | ✓ |
| Edit agents | ✓ | ✓ | ✗ |
| Delete agents | ✓ | ✗ | ✗ |
| Manage users | ✓ | ✗ | ✗ |
| View audit log | ✓ | ✗ | ✗ |
| View conversations | ✓ | ✓ | ✓ |
| Inject messages | ✓ | ✓ | ✗ |

**Rationale:** Simple model covering common access patterns.

---

### D11: Message Format Consistency

**Decision:** All messages use consistent structure:

```json
{
    "sender": "Display Name",
    "sender_id": "agent_id",
    "content": "...",
    "timestamp": "ISO-8601",
    "audio": null | { "id": "...", "url": "..." }
}
```

**Benefits:**
- Predictable API responses
- Easy frontend rendering
- Supports mixed agent/human messages

---

### D12: Error Response Format

**Decision:** Standardized error response:

```json
{
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Human-readable description",
        "details": { ... }
    }
}
```

**Benefits:**
- Consistent error handling
- Machine-parseable codes
- Human-readable messages

---

## Future Considerations

### F1: WebSocket for Real-Time Updates

Currently using polling (`GET /status`). Future: WebSocket for push updates.

### F2: Multi-Tenant Support

Current: Single-tenant. Future: Organization-scoped data isolation.

### F3: Plugin System for Tools

Current: Hard-coded tool permissions. Future: Plugin registry with sandboxed execution.

### F4: Streaming Responses

Current: Wait for full response. Future: Stream tokens for faster perceived latency.

### F5: Conversation Branching

Current: Linear conversation. Future: Branch points, parallel threads.

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-01-30 | Initial documentation |

---

*Back to: [Documentation Home](./README.md)*
