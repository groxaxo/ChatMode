# ChatMode

Python multi-agent chat interface with autonomous conversation, long-term memory via embeddings, optional TTS, and a FastAPI admin UI.

## Quick Start (local)

```bash
cd /home/op/ChatMode
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python main.py
```

You will be prompted for a topic. Leave it blank to auto-generate.

## Admin Web UI

```bash
cd /home/op/ChatMode
python -m uvicorn web_admin:app --host 0.0.0.0 --port 8000
```

- Admin UI: `http://localhost:8000/`
- Frontend (copied from the other project):
  - `http://localhost:8000/frontend/chat.html`
  - `http://localhost:8000/frontend/index.html`

### Frontend directory override
If you keep the UI in a separate folder, set:

```
FRONTEND_DIR=/path/to/frontend
```

The server will also automatically use `/home/op/ChatMode/Reun10n/frontend` when present.

## Launching the Whole Stack

To run the complete ChatMode system with CrewAI agents and remote Ollama:

1. **Ensure Ollama is running** on the remote server (e.g., `100.85.200.51:11434`). Pull required models if needed:
   ```bash
   # On the Ollama server
   ollama pull llama3.2:3b  # or your preferred model
   ```

2. **Set environment variables** for Ollama and other configs:
   ```bash
   export OLLAMA_BASE_URL=http://100.85.200.51:11434
   export EMBEDDING_PROVIDER=ollama
   export EMBEDDING_MODEL=llama3.2:3b
   # Add other .env variables as needed
   ```

3. **Activate the conda environment** and start the backend:
   ```bash
   cd /home/op/ChatMode
   conda activate ChatMode  # or conda run -n ChatMode
   python -m uvicorn web_admin_crewai:app --host 0.0.0.0 --port 8002
   ```

4. **Open the frontend** in your browser:
   - Admin Console: `http://localhost:8002/frontend/index.html`
   - Live Monitor: `http://localhost:8002/frontend/chat.html`

The agents are loaded from `agent_config.json` and profiles in `profiles/`. Start a session via the UI to begin the multi-agent discussion.

## CLI Agent Manager

For command-line control of agents without the web UI, featuring beautiful terminal output with Rich:

```bash
cd /home/op/ChatMode
conda activate ChatMode
python agent_manager.py --help
```

### Available Commands

- `start <topic>`: Start a new session with the given topic (shows live status)
- `stop`: Stop the current session
- `resume`: Resume a paused session (shows live status)
- `status`: Show current session status and recent messages in a table
- `list-agents`: List all available agents in a table
- `inject <sender> <message>`: Inject a message into the ongoing session
- `clear-memory`: Clear the conversation memory

Example:
```bash
python agent_manager.py start "The future of AI"
python agent_manager.py status
python agent_manager.py inject Admin "What do you think about quantum computing?"
python agent_manager.py stop
```

## Configuration (.env)

Create a `.env` in `/home/op/ChatMode` to configure providers. All settings are optional.

### OpenAI-compatible chat/embeddings

```bash
OPENAI_API_KEY=your_key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini

# Embeddings (can also use OpenAI-compatible)
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_BASE_URL=https://api.openai.com/v1
```

### Ollama chat + embeddings (recommended for local)

```bash
# Chat models per agent are set in profiles/*.json
OLLAMA_BASE_URL=http://localhost:11434

# Embeddings via Ollama
EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL=qwen:0.5b
EMBEDDING_BASE_URL=http://localhost:11434
```

### TTS (OpenAI-compatible)

```bash
TTS_ENABLED=true
TTS_BASE_URL=https://api.openai.com/v1
TTS_API_KEY=your_key
TTS_MODEL=tts-1
TTS_VOICE=alloy
TTS_OUTPUT_DIR=./tts_out
```

### Runtime controls

```bash
MAX_CONTEXT_TOKENS=32000
MAX_OUTPUT_TOKENS=512
MEMORY_TOP_K=5
HISTORY_MAX_MESSAGES=20
TEMPERATURE=0.9
SLEEP_SECONDS=2
ADMIN_USE_LLM=true
ADMIN_TOPIC=""  # Optional: set topic directly (overrides prompt)
CHROMA_DIR=./data/chroma
```

## Profiles

Each agent profile (e.g. `profiles/lawyer.json`) defines:

- `name`: display name
- `model`: chat model name
- `api`: `openai` or `ollama`
- `url`: base URL for that provider
- `params`: provider-specific options (e.g., `num_ctx: 32768` for Ollama)
- `speak_model`: optional TTS override per agent

## Docker

Build and run:

```bash
docker build -t chat_mode -f /home/op/ChatMode/Dockerfile /home/op/ChatMode

docker run --rm -it \
  --env-file /home/op/ChatMode/.env \
  -v /home/op/ChatMode/data:/app/data \
  -p 8000:8000 \
  chat_mode
```

Notes:
- The container persists memory in `/app/data/chroma`.
- If using Ollama running on the host, set `OLLAMA_BASE_URL` (or agent profile `url`) to `http://host.docker.internal:11434` on macOS/Windows, or use the host network on Linux.
- For the admin UI in Docker, run: `python -m uvicorn web_admin:app --host 0.0.0.0 --port 8000` inside the container.
