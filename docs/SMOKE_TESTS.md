# ChatMode Smoke Tests

This document describes the smoke tests for ChatMode features and how to run them.

## Overview

The smoke tests validate the following critical features:

1. **Profiles**: Loading profiles with `extra_prompt` and backward compatibility
2. **Solo Mode**: Single agent mode with AdminAgent interaction
3. **Memory**: Session/agent-scoped memory with proper tagging and filtering
4. **MCP Tools**: Tool listing, security blocking, and execution
5. **Exports**: Transcript downloads in markdown and CSV formats
6. **Tool Call Robustness**: Proper handling without relying on `finish_reason`

## Prerequisites

Install required dependencies:

```bash
pip install -r requirements.txt
pip install pytest pytest-asyncio
```

## Running the Tests

### Run All Smoke Tests

```bash
pytest tests/test_smoke_tests.py -v
```

### Run Specific Test Categories

**Profile Loading Tests:**
```bash
pytest tests/test_smoke_tests.py::TestProfileLoading -v
```

**Solo Mode Tests:**
```bash
pytest tests/test_smoke_tests.py::TestSoloMode -v
```

**Memory Tests:**
```bash
pytest tests/test_smoke_tests.py::TestMemory -v
```

**MCP Tools Tests:**
```bash
pytest tests/test_smoke_tests.py::TestMCPTools -v
```

**Export Tests:**
```bash
pytest tests/test_smoke_tests.py::TestExports -v
```

**Tool Call Robustness Tests:**
```bash
pytest tests/test_smoke_tests.py::TestToolCallRobustness -v
```

### Run Individual Tests

```bash
pytest tests/test_smoke_tests.py::TestProfileLoading::test_profile_with_extra_prompt -v
```

## Test Details

### 1. Profile Tests

#### Test: `test_profile_with_extra_prompt`
**Purpose**: Verify that `extra_prompt` in profile is appended to system prompt, not replaced.

**What it validates**:
- Profile loads successfully with `extra_prompt` field
- Original `conversing` content is preserved
- `extra_prompt` content is added to the system prompt
- No silent rewriting occurs

**Example profile**:
```json
{
  "name": "Test Agent",
  "model": "gpt-4o-mini",
  "api": "openai",
  "conversing": "You are a helpful assistant.",
  "extra_prompt": "Additional instructions for testing."
}
```

#### Test: `test_profile_backward_compatibility_without_optional_fields`
**Purpose**: Ensure old profiles without new fields still work.

**What it validates**:
- Legacy profiles load without error
- Optional fields default to `None` or empty
- Agent functions normally with minimal config

### 2. Solo Mode Tests

#### Test: `test_admin_agent_creates_clarifying_questions`
**Purpose**: Verify AdminAgent generates thoughtful responses.

**What it validates**:
- AdminAgent doesn't dead-loop
- Generates clarifying questions
- Challenges assumptions appropriately
- Produces sensible conversational turns

#### Test: `test_session_supports_solo_mode`
**Purpose**: Confirm session creates AdminAgent when only 1 agent present.

**What it validates**:
- ChatSession detects single-agent configuration
- AdminAgent is initialized automatically
- Solo mode path is activated

### 3. Memory Tests

#### Test: `test_memory_entries_tagged_by_session_and_agent`
**Purpose**: Verify memory entries include session_id and agent_id tags.

**What it validates**:
- Memory.add() accepts session_id and agent_id parameters
- Metadata is properly stored with entries

#### Test: `test_memory_retrieval_respects_filters`
**Purpose**: Ensure memory queries filter by session/agent correctly.

**What it validates**:
- Query accepts session_id filter
- Query accepts agent_id filter
- No cross-session or cross-agent bleed occurs

#### Test: `test_memory_purge_*`
**Purpose**: Verify selective memory clearing works.

**What it validates**:
- Purge by agent_id only
- Purge by session_id only
- Purge with both filters
- Other memories remain intact

### 4. MCP Tools Tests

#### Test: `test_list_tools_returns_available_tools`
**Purpose**: Verify MCP client can list available tools.

**What it validates**:
- GET /tools/list?agent_name=X returns tool definitions
- Tool names and descriptions are included

#### Test: `test_tool_call_blocked_if_not_allowed`
**Purpose**: Ensure unauthorized tools are blocked.

**What it validates**:
- Tools not in `allowed_tools` are rejected
- Security check happens before execution
- Appropriate error is returned

#### Test: `test_tool_call_execution_end_to_end`
**Purpose**: Verify POST /tools/call works completely.

**What it validates**:
- Tool execution completes successfully
- Arguments are passed correctly
- Results are returned properly

### 5. Export Tests

#### Test: `test_transcript_export_markdown`
**Purpose**: Verify markdown transcript generation.

**What it validates**:
- Markdown format is correct
- Topic and session ID are included
- All messages are formatted properly
- Sender names and content are preserved

#### Test: `test_transcript_export_csv`
**Purpose**: Verify CSV transcript generation.

**What it validates**:
- CSV headers are correct (Sender, Content, Audio)
- All messages are exported
- Format is valid CSV

### 6. Tool Call Robustness Tests

#### Test: `test_tool_call_detection_uses_tool_calls_presence`
**Purpose**: Ensure we check tool_calls attribute, not finish_reason.

**What it validates**:
- Code checks `tool_calls` presence
- No reliance on `finish_reason`
- Follows OpenAI best practices

#### Test: `test_safe_json_loads_handles_invalid_json`
**Purpose**: Verify malformed JSON doesn't crash the system.

**What it validates**:
- Valid JSON parses correctly
- Invalid JSON returns empty dict
- Already-parsed dicts are handled
- No exceptions are raised

#### Test: `test_tool_message_format_includes_tool_call_id`
**Purpose**: Ensure proper tool message format.

**What it validates**:
- Tool responses use `role="tool"`
- `tool_call_id` is included (required by OpenAI)
- Content is properly formatted

## API Endpoint Tests

These tests can also be run manually against a running server:

### Test Memory Purge

```bash
# Purge memory for specific agent
curl -X POST "http://localhost:8000/api/v1/memory/purge?agent_name=agent1"

# Purge memory for specific session
curl -X POST "http://localhost:8000/api/v1/memory/purge?session_id=session_123"

# Purge memory for agent in specific session
curl -X POST "http://localhost:8000/api/v1/memory/purge?agent_name=agent1&session_id=session_123"
```

### Test Tool Listing

```bash
curl "http://localhost:8000/api/v1/tools/list?agent_name=agent1"
```

### Test Tool Execution

```bash
curl -X POST "http://localhost:8000/api/v1/tools/call" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "agent1",
    "tool_name": "example_tool",
    "arguments": {"param": "value"}
  }'
```

### Test Transcript Download

```bash
# Download as Markdown
curl "http://localhost:8000/api/v1/transcript/download?format=markdown" \
  -o transcript.md

# Download as CSV
curl "http://localhost:8000/api/v1/transcript/download?format=csv" \
  -o transcript.csv
```

## Known Limitations

1. **ChromaDB Path Issues**: Some tests may fail if ChromaDB has issues with the persist directory path. This is usually due to environment-specific path handling.

2. **External Dependencies**: Tests that require external services (Ollama, OpenAI API, MCP servers) are mocked to avoid actual calls. For full integration testing, configure real services.

3. **Async Tests**: MCP tool tests use `pytest-asyncio` and require it to be installed.

## Troubleshooting

### ChromaDB Errors

If you see "range start index out of range" errors:
- Clear the `data/chroma` directory
- Use a clean temporary directory for tests
- Check ChromaDB version compatibility

### Import Errors

If imports fail:
```bash
pip install -r requirements.txt
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Async Warnings

If you see "Unknown pytest.mark.asyncio" warnings:
```bash
pip install pytest-asyncio
```

## Success Criteria

All smoke tests should pass before deploying new features:

- ✅ Profile tests pass (extra_prompt works, backward compatible)
- ✅ Solo mode tests pass (AdminAgent creates good turns)
- ✅ Memory tests pass (session/agent scoping works, purge works)
- ✅ MCP tests pass (tools listed, blocked when unauthorized, execute correctly)
- ✅ Export tests pass (markdown and CSV formats work)
- ✅ Robustness tests pass (no finish_reason reliance, safe JSON, proper tool messages)

## Contributing

When adding new features, update the smoke tests:

1. Add test cases for new functionality
2. Update this documentation
3. Ensure all tests pass before submitting PR
4. Follow existing test patterns and naming conventions
