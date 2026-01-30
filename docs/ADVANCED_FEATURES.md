# ChatMode Advanced Features Guide

This guide covers the advanced features added to ChatMode, including refactored prompt handling, improved memory management, MCP integration, and more.

## Table of Contents

- [System Prompt Refactoring](#system-prompt-refactoring)
- [Memory and Context Improvements](#memory-and-context-improvements)
- [Multi-Agent Support](#multi-agent-support)
- [MCP Integration](#mcp-integration)
- [Advanced Provider Features](#advanced-provider-features)
- [Web UI Extensions](#web-ui-extensions)

---

## System Prompt Refactoring

### Overview

The hardcoded system prompt has been refactored to support flexible agent configuration through the `extra_prompt` field.

### Agent Profile Schema

Agent profiles now support an optional `extra_prompt` field:

```json
{
  "name": "Dr. Sophia Chen",
  "model": "gpt-4o-mini",
  "api": "openai",
  "conversing": "You are Dr. Sophia Chen, a philosopher...",
  "extra_prompt": "MODE: PURE CHAT. Do not mention Minecraft, inventory, or health. You are in a meeting room debating a topic."
}
```

### Backwards Compatibility

All existing profiles have been updated with the default `extra_prompt` to maintain backwards compatibility:

```json
"extra_prompt": "MODE: PURE CHAT. Do not mention Minecraft, inventory, or health. You are in a meeting room debating a topic."
```

You can customize this field for different agent types:

- **Debater:** `"extra_prompt": "Focus on logical arguments and counterarguments."`
- **Researcher:** `"extra_prompt": "Provide evidence-based insights with citations."`
- **Summarizer:** `"extra_prompt": "Provide concise summaries of the discussion."`

---

## Memory and Context Improvements

### Per-Agent Memory Settings

Agents can now have customized memory and context settings:

```json
{
  "name": "Advanced Agent",
  "model": "gpt-4",
  "memory_top_k": 10,
  "max_context_tokens": 64000
}
```

- **`memory_top_k`**: Number of memory snippets to retrieve (overrides global `MEMORY_TOP_K`)
- **`max_context_tokens`**: Maximum tokens in context window (overrides global `MAX_CONTEXT_TOKENS`)

### Session-Scoped Memory

Memory entries are now tagged with session ID and agent ID:

```python
# Memory is automatically tagged
agent.remember_message(
    sender="User",
    content="Important information",
    session_id=session.session_id,
    topic="Discussion topic"
)
```

### Clearing Memory

Clear memory by session, agent, or both:

```python
# Clear all memory for a session
memory_store.clear(session_id="abc-123")

# Clear all memory for an agent
memory_store.clear(agent_id="researcher")

# Clear all memory
memory_store.clear()
```

### Conversation Summarization

When conversation history exceeds `history_max_messages`, the system automatically:

1. Takes the oldest half of messages
2. Generates an LLM-powered summary
3. Replaces old messages with the summary
4. Maintains context without exceeding token limits

This prevents important context from being lost when conversations become lengthy.

---

## Multi-Agent Support

### Arbitrary Number of Agents

ChatMode now supports **any number of agents** (≥1), removing the previous "at least 2 agents" constraint.

### Solo Agent Mode

When only one agent is configured, ChatMode automatically creates an **AdminAgent** that:

- Asks clarifying questions
- Challenges assumptions
- Requests elaboration on interesting points
- Deepens the discussion

Example configuration:

```json
{
  "agents": [
    {
      "name": "researcher",
      "file": "/path/to/researcher.json"
    }
  ]
}
```

In this mode, the conversation alternates between:
1. **Main Agent** - Provides thoughts and responses
2. **AdminAgent** - Asks follow-up questions

---

## MCP Integration

### Overview

The Model Context Protocol (MCP) integration enables agents to use external tools like browser automation, code execution, and more.

### Installing MCP Server

For browser automation (Browser MCP):

```bash
npm install -g @browsermcp/mcp
```

For custom MCP servers, ensure they're accessible via command line.

### Configuring MCP in Agent Profiles

Add MCP configuration to your agent profile:

```json
{
  "name": "Researcher",
  "model": "gpt-4o",
  "api": "openai",
  "conversing": "You are a research assistant...",
  "mcp_command": "mcp-server-browsermcp",
  "mcp_args": ["--headless"],
  "allowed_tools": [
    "browser_navigate",
    "browser_enumerate_elements",
    "browser_click_by_selector",
    "browser_screenshot"
  ]
}
```

**Fields:**

- **`mcp_command`**: Command to launch the MCP server
- **`mcp_args`**: Optional command-line arguments
- **`allowed_tools`**: List of tool names this agent can use

### How It Works

1. **Initialization**: When the agent starts, it initializes an MCP client
2. **Tool Schema**: Available tools are converted to OpenAI function calling format
3. **Tool Calling**: When the LLM decides to use a tool, it returns a tool call
4. **Execution**: The agent executes the tool via MCP
5. **Response**: Tool results are injected into the conversation

### Example: Browser Automation

```json
{
  "name": "Web Researcher",
  "model": "gpt-4o",
  "api": "openai",
  "conversing": "You are a web researcher that can browse websites...",
  "mcp_command": "mcp-server-browsermcp",
  "allowed_tools": [
    "browser_navigate",
    "browser_screenshot"
  ]
}
```

The agent can now:
- Navigate to websites
- Take screenshots
- Extract information

### Security Considerations

- **Allowed Tools**: Always specify `allowed_tools` to limit what the agent can do
- **Manual Approval**: For sensitive operations, implement confirmation steps
- **Sandboxing**: Run MCP servers in isolated environments

---

## Advanced Provider Features

### Tool Calling Support

The OpenAI provider now supports function/tool calling:

```python
response = provider.chat(
    model="gpt-4o",
    messages=messages,
    tools=[
        {
            "type": "function",
            "function": {
                "name": "search_web",
                "description": "Search the web",
                "parameters": {...}
            }
        }
    ],
    tool_choice="auto"
)
```

### Multiple Embedding Providers

ChatMode now supports additional embedding providers:

**DeepInfra:**
```env
EMBEDDING_PROVIDER=deepinfra
EMBEDDING_BASE_URL=https://api.deepinfra.com/v1
EMBEDDING_API_KEY=your-key
EMBEDDING_MODEL=BAAI/bge-large-en-v1.5
```

**HuggingFace:**
```env
EMBEDDING_PROVIDER=huggingface
EMBEDDING_BASE_URL=https://api-inference.huggingface.co/v1
EMBEDDING_API_KEY=your-key
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

Both providers use OpenAI-compatible APIs.

---

## Web UI Extensions

### Conversation Transcript Download

Download conversation transcripts in Markdown or CSV format:

**Endpoint:**
```
GET /api/v1/transcript/download?format=markdown
GET /api/v1/transcript/download?format=csv
```

**Markdown Format:**
```markdown
# Conversation Transcript

**Topic:** Is AI consciousness possible?
**Session ID:** abc-123

---

## Dr. Sophia Chen

I believe that consciousness requires...

---
```

**CSV Format:**
```csv
Sender,Content,Audio
Dr. Sophia Chen,"I believe that...",/audio/chen_001.mp3
Admin,"Can you elaborate?",
```

### Memory Purge

Clear memory for specific agents or sessions:

**Endpoint:**
```
POST /api/v1/memory/purge?agent_name=researcher&session_id=abc-123
```

### MCP Tool Management

List available tools:
```
GET /api/v1/tools/list?agent_name=researcher
```

Manually trigger tool calls:
```
POST /api/v1/tools/call
{
  "agent_name": "researcher",
  "tool_name": "browser_navigate",
  "arguments": {"url": "https://example.com"}
}
```

---

## Migration Guide

### Updating Existing Profiles

1. **Add `extra_prompt`** (optional - already added to all profiles):
   ```json
   "extra_prompt": "Custom mode instructions..."
   ```

2. **Add per-agent memory settings** (optional):
   ```json
   "memory_top_k": 8,
   "max_context_tokens": 32000
   ```

3. **Add MCP configuration** (optional):
   ```json
   "mcp_command": "mcp-server-browsermcp",
   "mcp_args": [],
   "allowed_tools": ["browser_navigate"]
   ```

### Environment Variables

No new required environment variables. Optional additions:

```env
# For alternative embedding providers
EMBEDDING_PROVIDER=deepinfra  # or huggingface
EMBEDDING_BASE_URL=https://api.deepinfra.com/v1
```

---

## Troubleshooting

### MCP Issues

**Problem:** MCP tools not working
- Ensure MCP server is installed: `npm install -g @browsermcp/mcp`
- Verify command in agent profile: `"mcp_command": "mcp-server-browsermcp"`
- Check allowed_tools list matches server capabilities

**Problem:** Tool calls not executing
- Verify OpenAI model supports function calling (gpt-4o, gpt-4-turbo, etc.)
- Check tool schema format in logs

### Memory Issues

**Problem:** Memory not persisting
- Ensure `CHROMA_DIR` is writable
- Check session_id is being passed to `remember_message()`

**Problem:** Too many/few memory snippets
- Adjust `memory_top_k` in agent profile or globally

### Solo Agent Mode

**Problem:** AdminAgent not appearing
- Ensure only one agent in `agent_config.json`
- Check logs for AdminAgent initialization

---

## API Reference

### Agent Profile Schema

```typescript
interface AgentProfile {
  name: string;                    // Agent display name
  model: string;                   // LLM model name
  api: "openai" | "ollama";        // Provider type
  url?: string;                    // Custom API URL
  api_key?: string;                // API key
  conversing: string;              // System prompt
  extra_prompt?: string;           // Additional prompt text
  memory_top_k?: number;           // Memory retrieval limit
  max_context_tokens?: number;     // Context window size
  mcp_command?: string;            // MCP server command
  mcp_args?: string[];             // MCP server arguments
  allowed_tools?: string[];        // Allowed MCP tools
  speak_model?: {                  // TTS settings
    model?: string;
    voice?: string;
  };
}
```

---

## Examples

### Example 1: Research Agent with Browser Tools

```json
{
  "name": "Research Assistant",
  "model": "gpt-4o",
  "api": "openai",
  "conversing": "You are a research assistant that can browse the web and gather information.",
  "extra_prompt": "Use browser tools to verify facts and gather evidence.",
  "memory_top_k": 12,
  "max_context_tokens": 64000,
  "mcp_command": "mcp-server-browsermcp",
  "allowed_tools": [
    "browser_navigate",
    "browser_screenshot",
    "browser_enumerate_elements"
  ]
}
```

### Example 2: Solo Brainstorming Agent

```json
{
  "agents": [
    {
      "name": "creative",
      "file": "/path/to/creative-agent.json"
    }
  ]
}
```

Agent will interact with AdminAgent for brainstorming and ideation.

### Example 3: Multi-Agent with Mixed Capabilities

```json
{
  "agents": [
    {
      "name": "researcher",
      "file": "/path/to/researcher.json"
    },
    {
      "name": "analyst", 
      "file": "/path/to/analyst.json"
    },
    {
      "name": "critic",
      "file": "/path/to/critic.json"
    }
  ]
}
```

Different agents can have different:
- Memory settings
- Context windows
- Tool access
- Prompts

---

## Best Practices

1. **Start Simple**: Begin with basic profiles, add MCP tools later
2. **Limit Tools**: Only grant necessary tools to each agent
3. **Monitor Usage**: Track tool calls and memory usage
4. **Iterate Prompts**: Refine `extra_prompt` based on agent behavior
5. **Test Locally**: Use Ollama for development, OpenAI for production
6. **Backup Memory**: Regularly export ChromaDB data

---

## Security and Access Control

### Role-Based Access Control

ChatMode implements role-based access control (RBAC) with three roles:

- **Admin** – Full access to all features including agent deletion and permission updates
- **Moderator** – Can manage agents, clear memory, and execute tools
- **Viewer** – Read-only access to view agents and conversations

### Protected Endpoints

**Authentication Required:**
- `GET /api/v1/tools/list` – List MCP tools (all authenticated users)
- `GET /api/v1/transcript/download` – Download transcripts (all authenticated users)

**Admin/Moderator Required:**
- `DELETE /api/v1/agents/{agent_id}/memory` – Clear agent memory
- `POST /api/v1/memory/purge` – Purge session memory
- `POST /api/v1/tools/call` – Execute MCP tools manually
- `POST /api/v1/agents` – Create agents
- `PUT /api/v1/agents/{agent_id}` – Update agents

**Admin Only:**
- `DELETE /api/v1/agents/{agent_id}` – Delete agents
- `PUT /api/v1/agents/{agent_id}/permissions` – Update agent permissions

### Audit Logging

All sensitive operations are logged with:
- User identity
- Action performed
- Resource affected
- IP address
- User agent
- Timestamp
- Changes made

**Example Audit Entry:**
```json
{
  "user_id": "user-123",
  "action": "AGENT_MEMORY_CLEAR",
  "resource_type": "agent",
  "resource_id": "researcher",
  "changes": {
    "agent": "researcher",
    "session_id": "abc-123",
    "entries_cleared": 42
  },
  "ip_address": "192.168.1.100",
  "timestamp": "2024-01-30T12:34:56Z"
}
```

### Tool Security

**Allowed Tools Whitelist:**

Agents can only execute tools in their `allowed_tools` list:

```json
{
  "name": "Web Researcher",
  "mcp_command": "mcp-server-browsermcp",
  "allowed_tools": ["browser_navigate", "browser_screenshot"]
}
```

Any tool call not in the whitelist is rejected with a 403 Forbidden error.

**Argument Validation:**

Tool arguments are validated before execution:
- Must be valid JSON dictionary
- Maximum argument length: 10,000 characters per field
- Type validation for expected argument types

**Audit Trail:**

All tool executions are logged:
- Tool name and arguments
- Execution result or error
- User who triggered the call (for manual calls)
- Timestamp

---

## API Reference

### Memory Management

**Clear Agent Memory:**
```http
DELETE /api/v1/agents/{agent_id}/memory?session_id={optional_session_id}
Authorization: Bearer <token>
```

**Response:**
```json
{
  "status": "memory_cleared",
  "agent_id": "researcher",
  "agent_name": "researcher",
  "entries_cleared": 42,
  "session_id": "abc-123"
}
```

**Purge Session Memory:**
```http
POST /api/v1/memory/purge?agent_name={name}&session_id={id}
Authorization: Bearer <token>
```

**Response:**
```json
{
  "status": "success",
  "message": "Memory purged for agent=researcher, session=abc-123",
  "entries_cleared": 42
}
```

### Tool Management

**List Tools:**
```http
GET /api/v1/tools/list?agent_name={name}
Authorization: Bearer <token>
```

**Response:**
```json
{
  "agent": "researcher",
  "tools": [
    {
      "name": "browser_navigate",
      "description": "Navigate to a URL",
      "input_schema": {
        "type": "object",
        "properties": {
          "url": {"type": "string"}
        }
      }
    }
  ],
  "allowed_tools": ["browser_navigate", "browser_screenshot"],
  "count": 2
}
```

**Call Tool:**
```http
POST /api/v1/tools/call
Authorization: Bearer <token>
Content-Type: application/json

{
  "agent_name": "researcher",
  "tool_name": "browser_navigate",
  "arguments": {
    "url": "https://example.com"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "agent": "researcher",
  "tool": "browser_navigate",
  "arguments": {"url": "https://example.com"},
  "result": {
    "content": "Page loaded successfully",
    "title": "Example Domain"
  }
}
```

### Transcript Export

**Download Transcript:**
```http
GET /api/v1/transcript/download?format=markdown
Authorization: Bearer <token>
```

**Response:** File download (markdown or CSV)

---

## Troubleshooting

### Memory Clearing Issues

**Problem:** Memory not clearing properly

**Solutions:**
1. Check that ChromaDB is running
2. Verify session_id and agent_id are correct
3. Check audit logs for error details
4. Ensure user has admin/moderator role

### Tool Execution Failures

**Problem:** Tool calls failing with 403 Forbidden

**Solutions:**
1. Verify tool is in agent's `allowed_tools` list
2. Check MCP server is running
3. Verify MCP command is correct in agent profile
4. Check audit logs for detailed error

**Problem:** Tool not found

**Solutions:**
1. Run `GET /api/v1/tools/list` to see available tools
2. Verify MCP server supports the tool
3. Check MCP server logs for errors
4. Restart MCP server if needed

### Authentication Issues

**Problem:** 401 Unauthorized errors

**Solutions:**
1. Verify authentication token is valid
2. Check token expiration
3. Ensure user account is enabled
4. Verify user has required role for endpoint

---

## Future Enhancements

Planned features:

- **Async Run Loop**: Full asyncio support with streaming responses
- **Enhanced Web UI**: Rich tool visualization and management
- **More MCP Servers**: Code execution, database access, file management
- **Agent Collaboration**: Direct agent-to-agent communication
- **Workflow Automation**: Predefined agent collaboration patterns

---

For support, visit the [GitHub repository](https://github.com/groxaxo/ChatMode) or open an issue.
