# Configuration Reference

Complete reference for all configuration options in ChatMode.

---

## Environment Variables

### LLM Provider Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `OPENAI_API_KEY` | string | `""` | API key for OpenAI or compatible endpoints |
| `OPENAI_BASE_URL` | string | `https://api.openai.com/v1` | Base URL for OpenAI-compatible API |
| `OPENAI_MODEL` | string | `gpt-4o-mini` | Default chat model name |
| `OLLAMA_BASE_URL` | string | `http://localhost:11434` | Ollama server URL |

### Embedding Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `EMBEDDING_PROVIDER` | string | `ollama` | Provider: `ollama` or `openai` |
| `EMBEDDING_MODEL` | string | `qwen:0.5b` | Embedding model name |
| `EMBEDDING_BASE_URL` | string | `http://localhost:11434` | Embedding API base URL |
| `EMBEDDING_API_KEY` | string | `""` | API key for embedding service |

### TTS Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `TTS_ENABLED` | bool | `false` | Enable text-to-speech |
| `TTS_BASE_URL` | string | `https://api.openai.com/v1` | TTS API base URL |
| `TTS_API_KEY` | string | `""` | TTS API key |
| `TTS_MODEL` | string | `tts-1` | TTS model name |
| `TTS_VOICE` | string | `alloy` | Default voice ID |
| `TTS_OUTPUT_DIR` | string | `./tts_out` | Audio output directory |

### Storage Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `CHROMA_DIR` | string | `./data/chroma` | ChromaDB persistence directory |
| `DATABASE_URL` | string | `sqlite:///./data/chatmode.db` | Database connection string |

### Conversation Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `MAX_CONTEXT_TOKENS` | int | `32000` | Maximum tokens in context window |
| `MAX_OUTPUT_TOKENS` | int | `512` | Maximum tokens in response |
| `MEMORY_TOP_K` | int | `5` | Number of memory results to retrieve |
| `HISTORY_MAX_MESSAGES` | int | `20` | Maximum messages in conversation history |
| `TEMPERATURE` | float | `0.9` | LLM temperature (0.0-2.0) |
| `SLEEP_SECONDS` | float | `2` | Delay between agent responses |

### Admin & Debug

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `ADMIN_USE_LLM` | bool | `true` | Use LLM to generate topics |
| `VERBOSE` | bool | `false` | Enable verbose logging |
| `SECRET_KEY` | string | (required) | JWT signing key (production) |

---

## Settings Dataclass

The `Settings` class in `config.py` loads all environment variables:

```python
@dataclass
class Settings:
    # LLM
    openai_api_key: str
    openai_base_url: str
    default_chat_model: str
    ollama_base_url: str
    
    # Embeddings
    embedding_provider: str
    embedding_model: str
    embedding_base_url: str
    embedding_api_key: str
    
    # TTS
    tts_enabled: bool
    tts_base_url: str
    tts_api_key: str
    tts_model: str
    tts_voice: str
    tts_output_dir: str
    
    # Storage
    chroma_dir: str
    
    # Conversation
    max_context_tokens: int
    max_output_tokens: int
    memory_top_k: int
    history_max_messages: int
    temperature: float
    sleep_seconds: float
    
    # Admin
    admin_use_llm: bool
    verbose: bool
```

---

## Agent Configuration

### agent_config.json

The main agent roster file:

```json
{
  "agents": [
    {
      "name": "agent_id",
      "file": "/path/to/profiles/agent.json"
    }
  ]
}
```

### Agent Profile Schema

Each agent profile (`profiles/*.json`) follows this schema:

```json
{
    "name": "Display Name",
    "model": "model-name-or-id",
    "api": "ollama | openai",
    "url": "http://api-base-url",
    "api_key": "optional-api-key",
    "params": {
        "num_ctx": 32768,
        "temperature": 0.8
    },
    "speak_model": {
        "api": "openai",
        "url": "http://tts-api-url/v1",
        "model": "tts-1",
        "voice": "alloy"
    },
    "conversing": "System prompt for conversation mode...",
    "coding": "System prompt for coding mode..."
}
```

### Profile Fields Reference

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Display name shown in UI |
| `model` | string | Yes | Model identifier |
| `api` | string | No | Provider: `ollama` or `openai` (default: `ollama`) |
| `url` | string | No | Override base URL for this agent |
| `api_key` | string | No | Override API key for this agent |
| `params` | object | No | Additional model parameters |
| `params.num_ctx` | int | No | Context window size |
| `params.temperature` | float | No | Override temperature |
| `speak_model` | object | No | TTS configuration override |
| `speak_model.model` | string | No | TTS model name |
| `speak_model.voice` | string | No | TTS voice ID |
| `conversing` | string | Yes | System prompt for debate mode |
| `coding` | string | No | System prompt for coding assistance |

---

## Example Configurations

### Minimal OpenAI Configuration

```env
OPENAI_API_KEY=sk-xxx
OPENAI_MODEL=gpt-4o-mini
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small
TTS_ENABLED=true
```

### Full Ollama Configuration

```env
OLLAMA_BASE_URL=http://localhost:11434
OPENAI_API_KEY=not-needed
OPENAI_BASE_URL=http://localhost:11434/v1
OPENAI_MODEL=llama3.2:3b
EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL=nomic-embed-text
EMBEDDING_BASE_URL=http://localhost:11434
TTS_ENABLED=false
```

### Hybrid Configuration (Ollama + OpenAI TTS)

```env
OLLAMA_BASE_URL=http://localhost:11434
EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL=nomic-embed-text
TTS_ENABLED=true
TTS_BASE_URL=https://api.openai.com/v1
TTS_API_KEY=sk-xxx
TTS_MODEL=tts-1-hd
TTS_VOICE=nova
```

---

## Agent Profile Examples

### Local Ollama Agent

```json
{
    "name": "Sage",
    "model": "llama3.2:3b",
    "api": "ollama",
    "url": "http://localhost:11434",
    "params": {
        "num_ctx": 8192
    },
    "conversing": "You are Sage, a thoughtful philosopher..."
}
```

### OpenAI Agent

```json
{
    "name": "Nova",
    "model": "gpt-4o",
    "api": "openai",
    "url": "https://api.openai.com/v1",
    "api_key": "${OPENAI_API_KEY}",
    "speak_model": {
        "model": "tts-1-hd",
        "voice": "nova"
    },
    "conversing": "You are Nova, an enthusiastic optimist..."
}
```

### Azure OpenAI Agent

```json
{
    "name": "Azure Bot",
    "model": "gpt-4o-deployment-name",
    "api": "openai",
    "url": "https://your-resource.openai.azure.com/openai/deployments/gpt-4o",
    "api_key": "your-azure-key",
    "conversing": "You are a helpful Azure-hosted assistant..."
}
```

---

## Database Schema (Agent Manager)

When using the Agent Manager, configuration moves to the database:

### agents table
```sql
CREATE TABLE agents (
    id UUID PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    display_name VARCHAR(200),
    system_prompt TEXT,
    developer_prompt TEXT,
    model VARCHAR(200),
    provider VARCHAR(50),
    api_url VARCHAR(500),
    api_key_ref VARCHAR(100),
    temperature FLOAT DEFAULT 0.9,
    max_tokens INTEGER DEFAULT 512,
    top_p FLOAT DEFAULT 1.0,
    enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### agent_voice_settings table
```sql
CREATE TABLE agent_voice_settings (
    id UUID PRIMARY KEY,
    agent_id UUID REFERENCES agents(id),
    tts_enabled BOOLEAN DEFAULT true,
    tts_provider VARCHAR(50),
    tts_model VARCHAR(100),
    tts_voice VARCHAR(100),
    speaking_rate FLOAT DEFAULT 1.0,
    pitch FLOAT DEFAULT 0.0,
    stt_enabled BOOLEAN DEFAULT false,
    stt_provider VARCHAR(50),
    stt_model VARCHAR(100)
);
```

### agent_memory_settings table
```sql
CREATE TABLE agent_memory_settings (
    id UUID PRIMARY KEY,
    agent_id UUID REFERENCES agents(id),
    memory_enabled BOOLEAN DEFAULT true,
    embedding_provider VARCHAR(50),
    embedding_model VARCHAR(100),
    retention_days INTEGER DEFAULT 90,
    top_k INTEGER DEFAULT 5
);
```

---

## Hot Reload

Configuration changes take effect:

| Config Type | Reload Method |
|-------------|---------------|
| Environment variables | Restart server |
| Agent profiles (JSON) | Automatic on next session |
| Database settings | Immediate (Agent Manager) |
| agent_config.json | Automatic on next session |

---

*Next: [API Reference](./04-api-reference.md)*
