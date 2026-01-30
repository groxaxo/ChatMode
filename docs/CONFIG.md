# ChatMode Configuration Reference

Complete reference for all configuration options, environment variables, and agent profiles in ChatMode.

---

## Environment Variables

### Quick Reference

Create a `.env` file in the project root with these variables:

```env
# === LLM Provider ===
OPENAI_API_KEY=sk-your-key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
OLLAMA_BASE_URL=http://localhost:11434

# === Embeddings ===
EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL=nomic-embed-text
EMBEDDING_BASE_URL=http://localhost:11434
EMBEDDING_API_KEY=

# === TTS (Text-to-Speech) ===
TTS_ENABLED=true
TTS_BASE_URL=https://api.openai.com/v1
TTS_API_KEY=sk-your-key
TTS_MODEL=tts-1
TTS_VOICE=alloy
TTS_OUTPUT_DIR=./tts_out

# === Storage ===
CHROMA_DIR=./data/chroma
DATABASE_URL=sqlite:///./data/chatmode.db

# === Conversation Settings ===
MAX_CONTEXT_TOKENS=32000
MAX_OUTPUT_TOKENS=512
MEMORY_TOP_K=5
HISTORY_MAX_MESSAGES=20
TEMPERATURE=0.9
SLEEP_SECONDS=2

# === Admin & Debug ===
ADMIN_USE_LLM=true
VERBOSE=false

# === Security (Production) ===
SECRET_KEY=your-strong-secret-key-change-in-production
ALLOWED_ORIGINS=https://yourdomain.com
```

---

## Configuration Details

### LLM Provider Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `OPENAI_API_KEY` | string | `""` | API key for OpenAI or compatible endpoints |
| `OPENAI_BASE_URL` | string | `https://api.openai.com/v1` | Base URL for OpenAI-compatible API |
| `OPENAI_MODEL` | string | `gpt-4o-mini` | Default chat model (fallback if not in profile) |
| `OLLAMA_BASE_URL` | string | `http://localhost:11434` | Ollama server URL |

**Provider Selection:**
- Agents can use different providers (configured per-agent in profiles)
- Set `api: "openai"` or `api: "ollama"` in agent profile
- API base URLs can be overridden per agent

### Embedding Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `EMBEDDING_PROVIDER` | string | `ollama` | Provider: `ollama` or `openai` |
| `EMBEDDING_MODEL` | string | `nomic-embed-text` | Embedding model name |
| `EMBEDDING_BASE_URL` | string | `http://localhost:11434` | Embedding API base URL |
| `EMBEDDING_API_KEY` | string | `""` | API key for embedding service (OpenAI only) |

**Recommended Models:**
- **Ollama**: `nomic-embed-text` (fast, good quality)
- **OpenAI**: `text-embedding-3-small` (affordable, high quality)
- **OpenAI**: `text-embedding-3-large` (best quality, higher cost)

### TTS Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `TTS_ENABLED` | bool | `false` | Enable text-to-speech synthesis |
| `TTS_BASE_URL` | string | `https://api.openai.com/v1` | TTS API base URL |
| `TTS_API_KEY` | string | `""` | TTS API key |
| `TTS_MODEL` | string | `tts-1` | TTS model (`tts-1` or `tts-1-hd`) |
| `TTS_VOICE` | string | `alloy` | Default voice ID |
| `TTS_OUTPUT_DIR` | string | `./tts_out` | Directory for generated audio files |

**Available Voices (OpenAI TTS):**
- `alloy` – Balanced, neutral
- `echo` – Masculine, clear
- `fable` – Warm, expressive
- `onyx` – Deep, authoritative
- `nova` – Feminine, energetic
- `shimmer` – Soft, gentle

**Per-Agent TTS Override:**
Agents can override voice in their profile:
```json
{
  "speak_model": {
    "voice": "nova"
  }
}
```

### Storage Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `CHROMA_DIR` | string | `./data/chroma` | ChromaDB vector database directory |
| `DATABASE_URL` | string | `sqlite:///./data/chatmode.db` | SQLAlchemy database URL |

**Database URL Examples:**
- SQLite: `sqlite:///./data/chatmode.db`
- PostgreSQL: `postgresql://user:pass@localhost/chatmode`
- MySQL: `mysql://user:pass@localhost/chatmode`

### Conversation Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `MAX_CONTEXT_TOKENS` | int | `32000` | Maximum tokens in context window |
| `MAX_OUTPUT_TOKENS` | int | `512` | Maximum tokens per agent response |
| `MEMORY_TOP_K` | int | `5` | Number of semantic memories to retrieve |
| `HISTORY_MAX_MESSAGES` | int | `20` | Maximum recent messages to include |
| `TEMPERATURE` | float | `0.9` | LLM temperature (0.0=deterministic, 2.0=very creative) |
| `SLEEP_SECONDS` | float | `2` | Delay between agent responses (seconds) |

**Tuning Guidelines:**
- **Temperature**: 0.7-0.9 for debates, 0.3-0.5 for technical discussions
- **MEMORY_TOP_K**: Increase for longer context, decrease for faster responses
- **HISTORY_MAX_MESSAGES**: Balance between context and token usage
- **SLEEP_SECONDS**: Adjust for pacing (0=instant, 5=thoughtful pauses)

### Admin & Debug

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `ADMIN_USE_LLM` | bool | `true` | Use LLM to generate debate topics |
| `ADMIN_TOPIC` | string | `""` | Pre-set topic (bypasses prompt/generation) |
| `VERBOSE` | bool | `false` | Enable verbose logging to console |

### Security (Production)

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `SECRET_KEY` | string | (required) | Secret key for JWT signing |
| `ALLOWED_ORIGINS` | string | `*` | CORS allowed origins (comma-separated) |

**Production Security Checklist:**
- [ ] Generate strong `SECRET_KEY` (32+ random characters)
- [ ] Set `ALLOWED_ORIGINS` to your domain only
- [ ] Use HTTPS in production
- [ ] Restrict database access
- [ ] Enable authentication middleware

---

## Agent Configuration

### Main Agent Registry

The `agent_config.json` file defines which agents are active:

```json
{
  "agents": [
    {
      "name": "philosopher",
      "file": "profiles/philosopher.json"
    },
    {
      "name": "scientist",
      "file": "profiles/scientist.json"
    }
  ]
}
```

**Fields:**
- `name` – Internal identifier (used in logs, API)
- `file` – Path to agent profile JSON

### Agent Profile Schema

Each agent has a profile JSON in the `profiles/` directory:

```json
{
  "name": "Dr. Sophia Chen",
  "model": "gpt-4o-mini",
  "api": "openai",
  "url": "https://api.openai.com/v1",
  "api_key": "",
  "params": {
    "temperature": 0.8,
    "max_tokens": 512
  },
  "speak_model": {
    "voice": "nova"
  },
  "conversing": "You are Dr. Sophia Chen, a philosopher specializing in ethics and consciousness..."
}
```

**Profile Fields:**

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `name` | Yes | string | Display name shown in UI |
| `model` | Yes | string | LLM model identifier |
| `api` | Yes | string | Provider: `"openai"` or `"ollama"` |
| `url` | No | string | Custom API endpoint (overrides env) |
| `api_key` | No | string | Custom API key (overrides env) |
| `params` | No | object | Provider-specific parameters |
| `speak_model` | No | object | TTS override (`voice`, `model`) |
| `conversing` | Yes | string | System prompt for personality |

**Provider-Specific Parameters:**

**For Ollama (`params`):**
```json
{
  "num_ctx": 32768,      // Context window size
  "num_predict": 512,    // Max output tokens
  "temperature": 0.8,    // Randomness
  "top_p": 0.9,          // Nucleus sampling
  "top_k": 40            // Top-k sampling
}
```

**For OpenAI (`params`):**
```json
{
  "temperature": 0.8,
  "max_tokens": 512,
  "top_p": 0.9,
  "frequency_penalty": 0.0,
  "presence_penalty": 0.0
}
```

---

## Profile Examples

### Ollama Local Agent

```json
{
  "name": "Local Assistant",
  "model": "llama3.2:3b",
  "api": "ollama",
  "url": "http://localhost:11434",
  "params": {
    "num_ctx": 8192,
    "temperature": 0.7
  },
  "conversing": "You are a helpful, concise assistant."
}
```

### OpenAI Cloud Agent

```json
{
  "name": "Cloud Expert",
  "model": "gpt-4o",
  "api": "openai",
  "url": "https://api.openai.com/v1",
  "params": {
    "temperature": 0.8,
    "max_tokens": 1024
  },
  "speak_model": {
    "voice": "alloy"
  },
  "conversing": "You are an expert AI researcher with deep knowledge of LLMs."
}
```

### Custom OpenAI-Compatible Endpoint

```json
{
  "name": "Custom LLM",
  "model": "custom-model-v1",
  "api": "openai",
  "url": "https://your-api.example.com/v1",
  "api_key": "your-custom-key",
  "conversing": "You are a specialized agent."
}
```

---

## Managing Configurations

### Via Web UI

1. Open **http://localhost:8000**
2. Navigate to **Agent Manager** tab
3. **Create/Edit/Delete** agents through the interface
4. Changes are saved to `profiles/` and `agent_config.json`

### Via Files (Manual)

1. Create/edit JSON files in `profiles/`
2. Update `agent_config.json` to include new agents
3. Restart server or reload (changes take effect on next session start)

### Via CLI (Scripting)

```bash
# List all agents
python agent_manager.py list-agents

# Manually edit profiles
nano profiles/my_agent.json
nano agent_config.json

# Restart to apply changes
pkill -f web_admin
uvicorn web_admin:app --reload
```

---

## Configuration Best Practices

### Development

- Use `TTS_ENABLED=false` to save API costs
- Set `VERBOSE=true` for debugging
- Use Ollama for free local testing
- Keep `TEMPERATURE` at 0.9 for creative debates

### Production

- Generate strong `SECRET_KEY`
- Restrict `ALLOWED_ORIGINS`
- Use PostgreSQL instead of SQLite for concurrency
- Set up proper logging and monitoring
- Use reverse proxy (Nginx) with HTTPS
- Backup `data/` directory regularly

### Performance Tuning

- Reduce `MEMORY_TOP_K` if responses are slow
- Decrease `HISTORY_MAX_MESSAGES` for faster startup
- Use smaller models (`llama3.2:3b`) for speed
- Increase `SLEEP_SECONDS` to avoid rate limits

### Memory Management

- Clear ChromaDB periodically: `rm -rf data/chroma`
- Archive old audio: `mv tts_out tts_archive_$(date +%Y%m%d)`
- Monitor disk usage in production

---

*See also: [Setup Guide](./SETUP.md) | [Architecture](./ARCHITECTURE.md) | [Agent System](./AGENTS.md)*
