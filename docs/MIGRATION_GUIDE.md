# Migration Guide: Upgrading to Advanced ChatMode

This guide helps you migrate your existing ChatMode setup to take advantage of the new features.

## Overview of Changes

The latest version of ChatMode introduces several enhancements:

1. **Flexible System Prompts** - `extra_prompt` field for customizable agent behavior
2. **Per-Agent Memory Settings** - Fine-tune memory and context per agent
3. **Solo Agent Mode** - Support for single-agent conversations
4. **MCP Integration** - Tool calling with external systems
5. **Advanced Providers** - Multiple embedding providers and function calling
6. **Enhanced Memory** - Session-scoped memory with better filtering
7. **Conversation Summarization** - Automatic summarization of long conversations

## Breaking Changes

**None!** All changes are backwards compatible. Existing configurations will continue to work.

## Step-by-Step Migration

### 1. Update Dependencies

```bash
cd ChatMode
pip install -r requirements.txt
```

This will install the new `mcp` package for tool calling support.

### 2. Profile Updates (Optional)

Your existing profiles will work as-is. To leverage new features, you can add optional fields:

**Before:**
```json
{
  "name": "Researcher",
  "model": "gpt-4o-mini",
  "api": "openai",
  "conversing": "You are a research assistant..."
}
```

**After (with new features):**
```json
{
  "name": "Researcher",
  "model": "gpt-4o-mini",
  "api": "openai",
  "conversing": "You are a research assistant...",
  "extra_prompt": "Focus on evidence-based research and cite sources.",
  "memory_top_k": 10,
  "max_context_tokens": 64000,
  "mcp_command": "mcp-server-browsermcp",
  "mcp_args": ["--headless"],
  "allowed_tools": ["browser_navigate", "browser_screenshot"]
}
```

### 3. MCP Setup (Optional)

If you want to enable browser automation or other MCP tools:

**Install Browser MCP:**
```bash
npm install -g @browsermcp/mcp
```

**Add to Agent Profile:**
```json
{
  "mcp_command": "mcp-server-browsermcp",
  "allowed_tools": ["browser_navigate"]
}
```

### 4. Environment Configuration

No changes required to `.env` file. Optional enhancements:

```env
# Use alternative embedding providers (optional)
EMBEDDING_PROVIDER=deepinfra
EMBEDDING_BASE_URL=https://api.deepinfra.com/v1
EMBEDDING_API_KEY=your-key-here
EMBEDDING_MODEL=BAAI/bge-large-en-v1.5
```

### 5. Agent Configuration

**Solo Agent Mode (New):**

Previously required at least 2 agents. Now you can run with just one:

```json
{
  "agents": [
    {
      "name": "brainstormer",
      "file": "/path/to/brainstormer.json"
    }
  ]
}
```

The system will automatically create an AdminAgent for interactive discussion.

### 6. Testing Your Setup

**Basic Test:**
```bash
python -c "from chatmode.agent import ChatAgent; print('✅ Import successful')"
```

**With MCP:**
```python
from chatmode.mcp_client import MCPClient
import asyncio

client = MCPClient("mcp-server-browsermcp")
tools = asyncio.run(client.list_tools())
print(f"✅ MCP working - {len(tools)} tools available")
```

### 7. API Changes

All existing API endpoints remain unchanged. New endpoints added:

- `GET /api/v1/transcript/download?format=markdown` - Download conversations
- `POST /api/v1/memory/purge?agent_name=X` - Clear agent memory
- `GET /api/v1/tools/list?agent_name=X` - List available MCP tools
- `POST /api/v1/tools/call` - Manually trigger tool calls

## Feature-by-Feature Migration

### Using Per-Agent Memory Settings

**Problem:** Some agents need more context than others.

**Solution:** Add per-agent overrides:

```json
{
  "name": "Lightweight Agent",
  "memory_top_k": 3,
  "max_context_tokens": 16000
}
```

```json
{
  "name": "Advanced Agent",
  "memory_top_k": 15,
  "max_context_tokens": 128000
}
```

### Customizing Agent Behavior

**Problem:** Want different modes for different agents.

**Solution:** Use `extra_prompt`:

```json
{
  "name": "Debater",
  "extra_prompt": "Challenge assumptions and present counterarguments."
}
```

```json
{
  "name": "Summarizer",
  "extra_prompt": "Provide concise summaries of key points."
}
```

### Enabling Tool Calling

**Problem:** Agent needs to browse the web or access external systems.

**Solution:** Configure MCP:

1. Install MCP server:
   ```bash
   npm install -g @browsermcp/mcp
   ```

2. Update profile:
   ```json
   {
     "mcp_command": "mcp-server-browsermcp",
     "allowed_tools": [
       "browser_navigate",
       "browser_screenshot",
       "browser_enumerate_elements"
     ]
   }
   ```

3. Ensure you're using a model that supports function calling (gpt-4o, gpt-4-turbo, etc.)

### Using Alternative Embedding Providers

**Problem:** Want to use DeepInfra or HuggingFace for embeddings.

**Solution:** Update `.env`:

**DeepInfra:**
```env
EMBEDDING_PROVIDER=deepinfra
EMBEDDING_BASE_URL=https://api.deepinfra.com/v1
EMBEDDING_API_KEY=your-deepinfra-key
EMBEDDING_MODEL=BAAI/bge-large-en-v1.5
```

**HuggingFace:**
```env
EMBEDDING_PROVIDER=huggingface
EMBEDDING_BASE_URL=https://api-inference.huggingface.co/v1
EMBEDDING_API_KEY=your-hf-token
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

### Session-Scoped Memory

Memory is now automatically tagged with session IDs. No configuration needed.

**Clear memory for a session:**
```python
from chatmode.memory import MemoryStore

memory.clear(session_id="abc-123")
```

**Clear memory for an agent:**
```python
memory.clear(agent_id="researcher")
```

### Conversation Summarization

Automatically enabled. When conversation history exceeds `HISTORY_MAX_MESSAGES`, older messages are summarized using the agent's LLM.

**Configure in `.env`:**
```env
HISTORY_MAX_MESSAGES=30  # Summarize after 30 messages
```

## Rollback Instructions

If you encounter issues, you can rollback:

```bash
git checkout <previous-commit>
pip install -r requirements.txt
```

Your data (ChromaDB, SQLite) will remain compatible.

## Common Issues

### MCP Server Not Found

**Error:** `Failed to initialize MCP client`

**Solution:**
- Ensure MCP server is installed: `npm list -g @browsermcp/mcp`
- Verify `mcp_command` matches the actual command name
- Check PATH includes npm global bin directory

### Tool Calls Not Working

**Error:** Tools are not being called by the agent

**Solution:**
- Verify you're using a model that supports function calling (gpt-4o, gpt-4-turbo)
- Check `allowed_tools` list matches available tools
- Ensure `api` is set to "openai" (Ollama doesn't support tool calling yet)

### Import Errors

**Error:** `ModuleNotFoundError: No module named 'mcp'`

**Solution:**
```bash
pip install mcp>=1.0.0
```

### Memory Not Persisting

**Error:** Memory is lost between sessions

**Solution:**
- Check `CHROMA_DIR` is writable
- Verify session_id is being passed (automatic in new version)
- Ensure ChromaDB directory is not being deleted

## Performance Considerations

1. **MCP Overhead:** Tool calls add latency. Use sparingly for critical operations.
2. **Memory Size:** Larger `memory_top_k` values increase prompt size and latency.
3. **Context Windows:** Larger contexts use more tokens but provide better responses.
4. **Summarization:** Adds an extra LLM call when history limit is reached.

## Best Practices

1. **Start Simple:** Enable new features gradually
2. **Test Locally:** Use Ollama for development
3. **Monitor Costs:** Tool calls and large contexts increase API costs
4. **Security:** Limit `allowed_tools` to only what's needed
5. **Backup Data:** Export ChromaDB before major changes

## Getting Help

- **Documentation:** See `docs/ADVANCED_FEATURES.md`
- **Examples:** Check `profiles/` directory for sample configurations
- **Issues:** https://github.com/groxaxo/ChatMode/issues
- **Discussions:** https://github.com/groxaxo/ChatMode/discussions

## What's Next?

Future enhancements planned:

- Full async/await support with streaming
- More MCP servers (code execution, database access)
- Enhanced web UI for tool management
- Agent collaboration patterns
- Performance optimizations

Stay tuned for updates!

---

## Security Updates (v2.0)

### Authentication Required for API Endpoints

**Breaking Change:** Several API endpoints now require authentication.

Previously public endpoints now require authentication:
- `GET /api/v1/tools/list`
- `GET /api/v1/transcript/download`
- `POST /api/v1/memory/purge`
- `POST /api/v1/tools/call`

**Migration Steps:**

1. **Create a user account:**
   ```bash
   # Use the admin UI or API to create users
   ```

2. **Update API clients to send authentication:**
   ```python
   import requests
   
   headers = {
       "Authorization": f"Bearer {access_token}"
   }
   
   response = requests.get(
       "http://localhost:8000/api/v1/tools/list",
       headers=headers,
       params={"agent_name": "researcher"}
   )
   ```

3. **Verify user roles:**
   - Admin: Full access to all endpoints
   - Moderator: Can manage agents, clear memory, call tools
   - Viewer: Read-only access

### Enhanced Memory Clearing

**New Feature:** Real ChromaDB deletion instead of just logging.

The `DELETE /api/v1/agents/{agent_id}/memory` endpoint now:
- Actually deletes embeddings from ChromaDB
- Returns count of entries cleared
- Supports session_id query parameter for selective clearing
- Logs all deletion operations for audit

**Example:**
```bash
# Clear all memory for an agent
curl -X DELETE \
  -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/agents/researcher-123/memory

# Clear memory for specific session
curl -X DELETE \
  -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/agents/researcher-123/memory?session_id=abc-123"
```

### Tool Security Enhancements

**New Validation:** Tool arguments are now validated before execution.

1. **Maximum argument length:** 10,000 characters per field
2. **Type validation:** Arguments must be a valid JSON dictionary
3. **Audit logging:** All tool executions are logged with:
   - Tool name and arguments
   - Execution result or error
   - User identity (for manual calls)
   - IP address and timestamp

**Impact:** Invalid tool calls will be rejected with 400 Bad Request.

### Audit Logging

**New Feature:** Comprehensive audit trail for security-relevant operations.

All operations are logged to the database:
- Agent creation/update/deletion
- Memory clearing
- Tool executions
- Permission changes
- Failed authentication attempts

**View audit logs:**
```bash
# Via API (admin only)
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/audit/logs?resource_type=agent
```

---

## Testing and CI/CD

### GitHub Actions Workflow

**New Feature:** Automated testing on every push and pull request.

The CI workflow includes:
- **Linting:** black, isort, flake8, mypy
- **Unit Tests:** Python 3.10, 3.11, 3.12
- **Smoke Tests:** End-to-end testing
- **Security Scanning:** bandit, safety
- **Integration Tests:** MCP (manual trigger)

**No action required** - tests run automatically on GitHub.

### Test Environment Improvements

**Fixed:** ChromaDB test isolation issues.

Tests now use:
- Unique collection names per test run
- Temporary directories for ChromaDB
- Environment variable isolation
- Deterministic test fixtures

**Running tests locally:**
```bash
# Install test dependencies
pip install pytest pytest-cov pytest-asyncio pytest-mock

# Run tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=chatmode --cov-report=term-missing
```

---

## Rollback Instructions

If you need to rollback to the previous version:

1. **Checkout previous version:**
   ```bash
   git checkout <previous-tag>
   ```

2. **Reinstall dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Restart services:**
   ```bash
   ./launch.sh
   ```

**Data Compatibility:** Database schema is backwards compatible. No migrations needed.

---

## Migration Checklist

Use this checklist to track your migration:

- [ ] Updated dependencies (`pip install -r requirements.txt`)
- [ ] Reviewed new features in agent profiles
- [ ] Added `extra_prompt` to agents (optional)
- [ ] Added per-agent memory settings (optional)
- [ ] Installed MCP servers (optional)
- [ ] Updated `.env` for alternative providers (optional)
- [ ] Created user accounts for API access
- [ ] Updated API clients with authentication headers
- [ ] Reviewed audit logs to verify security
- [ ] Tested memory clearing functionality
- [ ] Verified tool calling with allowed_tools whitelist
- [ ] Ran tests locally (`pytest tests/ -v`)
- [ ] Reviewed CI/CD workflow in GitHub Actions

---

**Migration Complete!** Your ChatMode installation is now production-ready with enhanced security, testing, and advanced features.
