# ChatMode Setup & Deployment Guide

This guide covers installation, configuration, and deployment of ChatMode for both local development and production environments.

---

## Quick Start

### Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.10+ | 3.11 recommended |
| Conda | Latest | Required for auto-installer |
| Git | 2.30+ | For cloning |
| Docker | 24.0+ | Optional, for containerized deployment |
| Ollama | 0.1.29+ | Optional, for local LLM inference |

### 1. Auto-Install (Recommended)

**Linux/macOS:**
```bash
# Clone and auto-install
git clone https://github.com/groxaxo/ChatMode.git
cd ChatMode
./autoinstall.sh
```

**Windows:**
```cmd
# Clone and auto-install
git clone https://github.com/groxaxo/ChatMode.git
cd ChatMode
autoinstall.bat
```

The autoinstaller automatically:
- ✅ Creates conda environment
- ✅ Installs all dependencies (with bcrypt fix)
- ✅ Creates data directories
- ✅ Initializes database with admin/admin credentials
- ✅ Verifies agent_config.json
- ✅ Creates launcher script
- ✅ Offers to start the server

### 2. Manual Installation (Alternative)

#### Option A: Using Conda

```bash
# Clone the repository
git clone https://github.com/groxaxo/ChatMode.git
cd ChatMode

# Create conda environment from environment.yml
conda env create -f environment.yml
conda activate chatmode

# Verify bcrypt compatibility (critical)
pip install 'bcrypt>=4.0.0,<4.1.0' passlib==1.7.4
```

#### Option B: Using pip

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

# IMPORTANT: Fix bcrypt compatibility issue
pip install 'bcrypt>=4.0.0,<4.1.0' passlib==1.7.4
```

### 2. Configure Environment

```bash
# Create .env file
cp .env.example .env

# Edit .env with your API keys and settings
nano .env  # or use your preferred editor
```

### 3. Initialize Database

```bash
# Create required directories
mkdir -p data/chroma tts_out

# Initialize database and create admin user
python bootstrap_admin.py
```

### 4. Start the Server

```bash
# Development mode with auto-reload (default port 8002)
uvicorn web_admin:app --host 0.0.0.0 --port 8002 --reload

# Or use the launcher script
./launch.sh
```

### 5. Access the Interface

Open your browser to: **http://localhost:8002**

**Default Login Credentials:**
- **Username:** `admin`
- **Password:** `admin`

**Note:** The Agent Manager tab requires authentication. The autoinstaller automatically creates these credentials. If you manually installed, run `python bootstrap_admin.py` to create the admin user.

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

### Using Conda (Recommended)

```bash
# Create environment from environment.yml (includes all dependencies)
conda env create -f environment.yml
conda activate chatmode

# Verify bcrypt compatibility (critical for authentication)
pip install 'bcrypt>=4.0.0,<4.1.0' passlib==1.7.4
```

**Note:** The `environment.yml` includes all required dependencies: FastAPI, SQLAlchemy, ChromaDB, CrewAI, MCP, and development tools.

### Initialize Database

```bash
# Create required directories
mkdir -p data/chroma tts_out

# Initialize database and create admin user
python bootstrap_admin.py
```

**Note:** The `bootstrap_admin.py` script:
1. Initializes the SQLite database
2. Creates the admin user with default credentials (admin / admin)
3. Sets up required database tables

If you need to reset the database:
```bash
rm data/chatmode.db
python bootstrap_admin.py
```

### Run the Server

**Development (with auto-reload):**
```bash
uvicorn web_admin:app --host 0.0.0.0 --port 8002 --reload
```

**Production:**
```bash
uvicorn web_admin:app --host 0.0.0.0 --port 8002 --workers 4
```

**Using the launcher:**
```bash
./launch.sh
# Choose option 1: Start Web Interface
```

**Access:** http://localhost:8002

**Default Login:** admin / admin

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
      - "8002:8002"
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
  -p 8002:8002 \
  chatmode
```

**Note:** When using Ollama on the host machine with Docker:
- **macOS/Windows**: Set `OLLAMA_BASE_URL=http://host.docker.internal:11434`
- **Linux**: Use `--network host` or the host's IP address

---

## Agent Configuration

### Creating Your First Agent

#### Via Web UI (Recommended)

1. Open **http://localhost:8002**
2. Login with credentials: **admin** / **admin**
3. Go to the **Agent Manager** tab
4. Click **Create New Agent**
5. Fill in the form:
   - **Agent ID**: `philosopher` (internal name)
   - **Display Name**: `Dr. Sophia Chen`
   - **Model**: `gpt-4o-mini` or `llama3.2:3b`
   - **API**: `openai` or `ollama`
   - **System Prompt**: Define the agent's personality
6. Click **Save**

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

2. Add to `agent_config.json` (in project root):
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

**Important:** The `agent_config.json` file must be in the project root directory (same level as `web_admin.py`). This file tells ChatMode which agents to load and where to find their profile configurations.

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

1. Open **http://localhost:8002**
2. Login with credentials: **admin** / **admin** (for Agent Manager features)
3. Go to **Session Control** tab
4. Enter a topic (e.g., "Is artificial consciousness possible?")
5. Click **Start Session**
6. Switch to **Live Monitor** tab to watch the conversation

**Important Notes:**
- **Content Filtering:** Agents have safety filters and will refuse explicit/inappropriate topics. They may redirect to safe topics like "The Ethics of Artificial Creativity." Use professional, educational topics for best results.
- **First Start:** The first message may take 10-30 seconds as agents initialize and query the LLM
- **Stop Button:** The stop command works immediately but the UI may take a moment to reflect the stopped state. Refresh the page if needed.

### Via CLI (Alternative)

```bash
# Using the web interface API
curl -X POST http://localhost:8002/start -d "topic=Your debate topic"

# Check status
curl http://localhost:8002/status

# Stop session
curl -X POST http://localhost:8002/stop
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
        proxy_pass http://localhost:8002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket support (if needed)
    location /ws {
        proxy_pass http://localhost:8002;
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
ExecStart=/opt/chatmode/.venv/bin/uvicorn web_admin:app --host 0.0.0.0 --port 8002 --workers 4
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

### bcrypt Compatibility Error

**Error:** `ValueError: password cannot be longer than 72 bytes` or authentication failures

**Solution:** Install compatible bcrypt version:
```bash
pip install 'bcrypt>=4.0.0,<4.1.0' passlib==1.7.4
```

Then recreate the admin user:
```bash
python bootstrap_admin.py
```

### Cannot Login

**Error:** "Incorrect username or password"

**Solution:** Reset to default credentials:
```bash
python bootstrap_admin.py
```
Default login: `admin` / `admin`

### Port Already in Use

```bash
# Find process using port 8002
lsof -i :8002

# Or use a different port
uvicorn web_admin:app --port 8003
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
python bootstrap_admin.py
```

This will recreate the database and admin user with default credentials.

### Memory Issues

```bash
# Clear ChromaDB
rm -rf data/chroma

# Clear TTS cache
rm -rf tts_out/*.mp3
```

### Conversation Start Errors ("Internal Server Error")

**Symptom:** Clicking "Start Session" shows "Internal Server Error"

**Common Causes & Solutions:**

1. **Missing agent_config.json**
   - Ensure `agent_config.json` exists in project root
   - Check that agent profile paths are correct

2. **Missing data directories**
   ```bash
   mkdir -p data/chroma tts_out
   ```

3. **Database not initialized**
   ```bash
   python bootstrap_admin.py
   ```

4. **bcrypt version incompatibility**
   ```bash
   pip install 'bcrypt>=4.0.0,<4.1.0' passlib==1.7.4
   ```

### Agents Ignore Topic or Discuss Something Else

**Symptom:** You enter "Talk about X" but agents discuss "The Ethics of Artificial Creativity" or refuse to engage

**Cause:** The LLM has content safety filters that block explicit, sexual, or inappropriate topics. Agents are programmed to redirect to safe, educational topics.

**Solution:** Use appropriate, professional topics such as:
- ✅ "The future of renewable energy"
- ✅ "Ethics in artificial intelligence"
- ✅ "Climate change solutions"
- ✅ "Space exploration"
- ✅ "Philosophy of consciousness"
- ❌ Avoid: explicit, sexual, or inappropriate content

### Stop Button Not Working

**Symptom:** Clicking "Stop Session" doesn't seem to work

**Explanation:** The stop command actually works (sets `running: false`), but the conversation thread may take a moment to finish its current iteration. Refresh the page or check the **Session Control** tab to verify the status shows "Stopped".

### Agent Configuration Not Found

**Error:** `FileNotFoundError: [Errno 2] No such file or directory: 'agent_config.json'`

**Solution:** This was fixed in `chatmode/session.py`. The system now looks for `agent_config.json` in the project root directory. Ensure:
1. `agent_config.json` exists in project root
2. All agent profile paths in the file are correct
3. Profile JSON files exist in the `profiles/` directory

For more troubleshooting, see [TROUBLESHOOTING.md](./TROUBLESHOOTING.md).

---

*See also: [Configuration Guide](./CONFIG.md) | [Architecture](./ARCHITECTURE.md) | [Agent System](./AGENTS.md)*
