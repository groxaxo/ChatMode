# ChatMode - System Documentation

## Overview

ChatMode is a Python multi-agent chat interface that enables autonomous conversations between AI agents. It features long-term memory via embeddings, optional text-to-speech (TTS), and a FastAPI-based admin UI.

---

## Current Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              ChatMode System                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐                    │
│  │   main.py   │────▶│   agent.py  │────▶│ providers.py│                    │
│  │ (CLI Entry) │     │ (ChatAgent) │     │ (LLM/Embed) │                    │
│  └─────────────┘     └──────┬──────┘     └─────────────┘                    │
│                             │                                                │
│  ┌─────────────┐           │            ┌─────────────┐                     │
│  │ web_admin.py│◀──────────┼───────────▶│  memory.py  │                     │
│  │  (FastAPI)  │           │            │ (ChromaDB)  │                     │
│  └──────┬──────┘           │            └─────────────┘                     │
│         │                  │                                                 │
│  ┌──────▼──────┐     ┌─────▼─────┐     ┌─────────────┐                      │
│  │ session.py  │────▶│  admin.py │     │   tts.py    │                      │
│  │(ChatSession)│     │(AdminAgent│     │ (TTS Client)│                      │
│  └─────────────┘     └───────────┘     └─────────────┘                      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Component Breakdown

### 1. Entry Points

#### `main.py` - CLI Application
- Loads settings from environment variables
- Uses `AdminAgent` to generate debate topics (optional)
- Initializes multiple `ChatAgent` instances from `agent_config.json`
- Runs a conversation loop where agents take turns responding
- Stores messages in each agent's long-term memory

#### `web_admin.py` - Web Application (FastAPI)
- Provides REST API endpoints for controlling chat sessions
- Serves static frontend files
- Endpoints:
  - `GET /` - Admin page
  - `POST /start` - Start session with topic
  - `POST /stop` - Stop session
  - `POST /resume` - Resume paused session
  - `POST /messages` - Inject admin message
  - `GET /status` - Get current session status
  - `POST /memory/clear` - Clear conversation memory
  - `GET /agents` - List meeting participants

---

### 2. Core Modules

#### `agent.py` - ChatAgent Class

The main agent implementation with:

| Component | Description |
|-----------|-------------|
| **Profile Loading** | Loads persona from JSON files (`profiles/*.json`) |
| **Chat Provider** | Connects to OpenAI or Ollama APIs |
| **Embedding Provider** | Generates embeddings for memory |
| **Memory Store** | ChromaDB-based long-term memory |
| **TTS Client** | Optional text-to-speech output |

**Key Methods:**
- `load_profile()` - Load agent configuration from JSON
- `_build_messages()` - Construct prompt with memory context
- `generate_response()` - Generate agent response
- `remember_message()` - Store message in long-term memory

**Message Building Flow:**
```
1. Query memory with topic + recent conversation
2. Retrieve relevant memory snippets (top_k)
3. Build messages array:
   - System prompt (persona)
   - Memory context
   - Topic
   - Conversation history
   - Response instruction
4. Trim to fit context window
```

#### `memory.py` - MemoryStore Class

ChromaDB-based vector memory storage:

| Method | Description |
|--------|-------------|
| `add()` | Store text with embeddings and metadata |
| `query()` | Retrieve top-k similar items |

**Storage Structure:**
- Separate collection per agent (`{agent_name}_memory`)
- Persisted to `./data/chroma` directory
- Uses embedding provider for vectorization

#### `providers.py` - LLM & Embedding Providers

**Chat Providers:**
- `OpenAIChatProvider` - OpenAI-compatible API (GPT, Claude, etc.)
- `OllamaChatProvider` - Local Ollama models

**Embedding Providers:**
- `OpenAIEmbeddingProvider` - OpenAI embeddings API
- `OllamaEmbeddingProvider` - Local Ollama embeddings

**Factory Functions:**
- `build_chat_provider()` - Create chat provider instance
- `build_embedding_provider()` - Create embedding provider instance

#### `session.py` - ChatSession Class

Thread-safe session management:

| Method | Description |
|--------|-------------|
| `start()` | Initialize new session with topic |
| `stop()` | Stop running session |
| `resume()` | Resume paused session |
| `inject_message()` | Add admin message to history |
| `clear_memory()` | Clear session history |

**Session State:**
- `topic` - Current debate topic
- `history` - Full conversation history
- `last_messages` - Recent messages for UI display
- `agents` - List of active ChatAgent instances

#### `admin.py` - AdminAgent Class

Administrative agent for topic generation:
- Uses LLM to generate controversial/philosophical topics
- Fallback topic: "Is artificial consciousness possible?"

---

### 3. Configuration

#### `config.py` - Settings Dataclass

Environment-based configuration:

```python
Settings:
  # LLM Configuration
  openai_api_key, openai_base_url, default_chat_model
  ollama_base_url
  
  # Embedding Configuration
  embedding_provider, embedding_model, embedding_base_url, embedding_api_key
  
  # TTS Configuration
  tts_enabled, tts_base_url, tts_api_key, tts_model, tts_voice, tts_output_dir
  
  # Runtime Configuration
  chroma_dir, max_context_tokens, max_output_tokens
  memory_top_k, history_max_messages, temperature
  sleep_seconds, admin_use_llm
```

#### `agent_config.json` - Agent Registry

Defines which agents participate in conversations:
```json
{
  "agents": [
    {"name": "lawyer", "file": "/path/to/profiles/lawyer.json"},
    {"name": "crook", "file": "/path/to/profiles/crook.json"}
  ]
}
```

#### `profiles/*.json` - Agent Profiles

Individual agent persona definitions:
```json
{
  "name": "Display Name",
  "model": "model-name",
  "api": "openai|ollama",
  "url": "optional-base-url",
  "api_key": "optional-api-key",
  "params": {"temperature": 0.9},
  "conversing": "System prompt / persona description",
  "speak_model": {"model": "tts-1", "voice": "alloy"}
}
```

---

### 4. Data Flow

#### Conversation Loop
```
1. Admin generates/receives topic
2. For each round:
   a. For each agent:
      - Build context (topic + history + memory)
      - Generate response via LLM
      - Store response in all agents' memory
      - Optional: Generate TTS audio
      - Wait (sleep_seconds)
3. Continue until stopped
```

#### Memory Flow
```
Message → Embedding → ChromaDB Collection
                         ↓
Query → Embedding → Vector Similarity Search → Top-K Results
```

---

### 5. Frontend

#### Static Files (`frontend/`)
- `index.html` - Landing page
- `chat.html` - Chat interface

#### Vite Frontend (`frontend-msn/`)
- React + TypeScript application
- Vite build system
- Real-time chat display

---

### 6. Dependencies

```
openai>=1.40.0      # OpenAI API client
requests>=2.31.0    # HTTP client
python-dotenv>=1.0.1 # Environment loading
chromadb>=0.5.0     # Vector database
langchain>=0.2.0    # LLM framework (partially used)
fastapi>=0.110.0    # Web framework
uvicorn[standard]   # ASGI server
jinja2>=3.1.3       # Template engine
python-multipart    # Form data parsing
```

---

## Limitations of Current Implementation

1. **Custom Agent System** - Not using established multi-agent frameworks
2. **Simple Memory** - Basic vector similarity without advanced contextual memory
3. **No Task Management** - Agents just converse without structured tasks
4. **Limited Collaboration** - Agents don't delegate or collaborate on tasks
5. **No Workflow Control** - No conditional logic or process flows
6. **Manual Round-Robin** - Fixed turn-taking without dynamic orchestration

---

## Opportunities for Improvement

| Current | With CrewAI |
|---------|-------------|
| Custom agent class | Standardized `Agent` with roles/goals |
| Basic chat loop | Structured `Task` execution |
| Single memory store | Multi-type memory (STM, LTM, Entity) |
| No delegation | Agent delegation support |
| Manual flow | Sequential/Hierarchical processes |
| No tools | Rich tool ecosystem |

