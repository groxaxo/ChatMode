# ChatMode Setup & Deployment Guide

This guide covers installation, configuration, and deployment of ChatMode for both local development and production environments.

---

## Quick Start

### Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.10+ | 3.11 recommended |
| pip | 23.0+ | Or conda |
| Git | 2.30+ | For cloning |
| Docker | 24.0+ | Optional, for containerized deployment |
| Ollama | 0.1.29+ | Optional, for local LLM inference |

### 1. Clone and Install

```bash
# Clone the repository
git clone https://github.com/groxaxo/ChatMode.git
cd ChatMode

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate    # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Create .env file
cp .env.example .env

# Edit .env with your API keys and settings
nano .env  # or use your preferred editor
```

### 3. Start the Server

```bash
# Development mode with auto-reload
uvicorn web_admin:app --host 0.0.0.0 --port 8000 --reload

# Or use the launcher script
./launch.sh
```

### 4. Access the Interface

Open your browser to: **http://localhost:8000**

The unified web console provides all functionality in a single interface:
- **Session Control** – Start/stop conversations
- **Live Monitor** – Watch agent discussions in real-time
- **Agent Overview** – View all configured agents
- **Agent Manager** – Create and edit agent profiles

---

## Local Development Setup

### Using Virtual Environment (venv)

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate    # Windows

pip install -r requirements.txt
```

### Using Conda

```bash
# Create environment
conda create -n ChatMode python=3.11
conda activate ChatMode

# Install dependencies
pip install -r requirements.txt

# Or use environment.yml if available
conda env create -f environment.yml
```

### Initialize Database

```bash
# Initialize database
python -c "from database import init_db; init_db()"
```

### Run the Server

**Development (with auto-reload):**
```bash
uvicorn web_admin:app --host 0.0.0.0 --port 8000 --reload
```

**Production:**
```bash
uvicorn web_admin:app --host 0.0.0.0 --port 8000 --workers 4
```

**Using the launcher:**
```bash
./launch.sh
# Choose option 1: Start Web Interface
```

---

## Ollama Setup (Local LLM)

For running models locally without cloud API costs:

### 1. Install Ollama

**Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**macOS:**
```bash
brew install ollama
```

**Windows:**
Download from [ollama.com](https://ollama.com)

### 2. Pull Models

```bash
# Chat model (small, fast)
ollama pull llama3.2:3b

# Embedding model
ollama pull nomic-embed-text

# Optional: larger models for better quality
ollama pull mistral-nemo:12b
ollama pull qwen2.5:14b
```

### 3. Start Ollama Server

```bash
ollama serve
```

### 4. Configure ChatMode for Ollama

Edit `.env`:
```env
EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL=nomic-embed-text
EMBEDDING_BASE_URL=http://localhost:11434
```

Update agent profiles in `profiles/*.json`:
```json
{
    "name": "Agent Name",
    "api": "ollama",
    "url": "http://localhost:11434",
    "model": "llama3.2:3b",
    "conversing": "Your system prompt here..."
}
```

---

## Docker Deployment

### Quick Docker Compose

```bash
# Build and start all services
docker compose up -d

# View logs
docker compose logs -f

# Stop services
docker compose down
```

### Docker Compose Configuration

The included `compose.yaml` provides a complete stack:

```yaml
version: '3.8'

services:
  chatmode:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./tts_out:/app/tts_out
      - ./profiles:/app/profiles
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - OLLAMA_BASE_URL=http://ollama:11434
    depends_on:
      - ollama

  ollama:
    image: ollama/ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]

volumes:
  ollama_data:
```

### Standalone Docker

```bash
# Build image
docker build -t chatmode .

# Run container
docker run --rm -it \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/tts_out:/app/tts_out \
  -v $(pwd)/profiles:/app/profiles \
  -p 8000:8000 \
  chatmode
```

**Note:** When using Ollama on the host machine with Docker:
- **macOS/Windows**: Set `OLLAMA_BASE_URL=http://host.docker.internal:11434`
- **Linux**: Use `--network host` or the host's IP address

---

## Agent Configuration

### Creating Your First Agent

#### Via Web UI (Recommended)

1. Open **http://localhost:8000**
2. Go to the **Agent Manager** tab
3. Click **Create New Agent**
4. Fill in the form:
   - **Agent ID**: `philosopher` (internal name)
   - **Display Name**: `Dr. Sophia Chen`
   - **Model**: `gpt-4o-mini` or `llama3.2:3b`
   - **API**: `openai` or `ollama`
   - **System Prompt**: Define the agent's personality
5. Click **Save**

#### Manually (Advanced)

1. Create `profiles/philosopher.json`:
```json
{
    "name": "Dr. Sophia Chen",
    "model": "gpt-4o-mini",
    "api": "openai",
    "url": "https://api.openai.com/v1",
    "conversing": "You are Dr. Sophia Chen, a philosopher specializing in ethics and consciousness. You approach debates with rigorous logic and Socratic questioning.",
    "speak_model": {
        "voice": "nova"
    }
}
```

2. Add to `agent_config.json`:
```json
{
  "agents": [
    {
      "name": "philosopher",
      "file": "profiles/philosopher.json"
    }
  ]
}
```

### Agent Profile Fields

| Field | Required | Description | Example |
|-------|----------|-------------|---------|
| `name` | Yes | Display name | `"Dr. Sarah Chen"` |
| `model` | Yes | LLM model identifier | `"gpt-4o-mini"`, `"llama3.2:3b"` |
| `api` | Yes | Provider type | `"openai"`, `"ollama"` |
| `url` | No | Custom API endpoint | `"http://localhost:11434"` |
| `conversing` | Yes | System prompt defining personality | See examples in `profiles/` |
| `speak_model` | No | TTS voice override | `{"voice": "alloy"}` |
| `params` | No | Provider-specific settings | `{"num_ctx": 32768}` |

---

## Starting a Conversation

### Via Web Interface

1. Open **http://localhost:8000**
2. Go to **Session Control** tab
3. Enter a topic (e.g., "Is artificial consciousness possible?")
4. Click **Start Session**
5. Switch to **Live Monitor** tab to watch the conversation

### Via CLI (Alternative)

```bash
# Using the CLI tool
python agent_manager.py start "Your debate topic"

# Check status
python agent_manager.py status

# Stop session
python agent_manager.py stop
```

---

## Production Deployment

### Environment Variables for Production

```env
# Security
SECRET_KEY=your-strong-secret-key-here
ALLOWED_ORIGINS=https://yourdomain.com

# Database
DATABASE_URL=postgresql://user:pass@localhost/chatmode

# LLM Provider
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://api.openai.com/v1

# Or use Ollama
OLLAMA_BASE_URL=http://ollama-server:11434

# TTS (optional)
TTS_ENABLED=true
TTS_BASE_URL=https://api.openai.com/v1
TTS_API_KEY=sk-...
```

### Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name chatmode.example.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket support (if needed)
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### Systemd Service

Create `/etc/systemd/system/chatmode.service`:

```ini
[Unit]
Description=ChatMode AI Agent Platform
After=network.target

[Service]
Type=simple
User=chatmode
WorkingDirectory=/opt/chatmode
Environment="PATH=/opt/chatmode/.venv/bin"
ExecStart=/opt/chatmode/.venv/bin/uvicorn web_admin:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable chatmode
sudo systemctl start chatmode
sudo systemctl status chatmode
```

---

## Troubleshooting

### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000

# Or use a different port
uvicorn web_admin:app --port 8001
```

### Ollama Connection Issues

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Restart Ollama
pkill ollama
ollama serve
```

### Database Issues

```bash
# Reset database
rm data/chatmode.db
python -c "from database import init_db; init_db()"
```

### Memory Issues

```bash
# Clear ChromaDB
rm -rf data/chroma

# Clear TTS cache
rm -rf tts_out/*.mp3
```

For more troubleshooting, see [TROUBLESHOOTING.md](./TROUBLESHOOTING.md).

---

*See also: [Configuration Guide](./CONFIG.md) | [Architecture](./ARCHITECTURE.md) | [Agent System](./AGENTS.md)*
