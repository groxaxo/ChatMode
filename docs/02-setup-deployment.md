# Setup & Deployment

This guide covers local development setup, production deployment, environment configuration, and GPU considerations.

---

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.10+ | 3.11 recommended |
| pip | 23.0+ | Or conda/uv |
| Git | 2.30+ | For cloning |
| Docker | 24.0+ | Optional, for containerized deployment |
| Ollama | 0.1.29+ | Optional, for local LLM inference |

---

## Local Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/ChatMode.git
cd ChatMode
```

### 2. Create Virtual Environment

**Using venv:**
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate    # Windows
```

**Using conda:**
```bash
conda create -n ChatMode python=3.11
conda activate ChatMode
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

**Additional dependencies for full functionality:**
```bash
pip install chromadb>=0.4.0     # Vector database
pip install aiosqlite           # Async database support
pip install python-jose[cryptography]  # JWT authentication
pip install passlib[bcrypt]     # Password hashing
pip install alembic             # Database migrations
```

### 4. Configure Environment

Create a `.env` file from the template:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
# === LLM Provider Configuration ===
OPENAI_API_KEY=sk-your-key-here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini

# === Ollama (Local) ===
OLLAMA_BASE_URL=http://localhost:11434

# === Embeddings ===
EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL=nomic-embed-text
EMBEDDING_BASE_URL=http://localhost:11434

# === TTS ===
TTS_ENABLED=true
TTS_BASE_URL=https://api.openai.com/v1
TTS_API_KEY=sk-your-key-here
TTS_MODEL=tts-1
TTS_VOICE=alloy

# === Storage ===
CHROMA_DIR=./data/chroma
TTS_OUTPUT_DIR=./tts_out

# === Conversation Settings ===
MAX_CONTEXT_TOKENS=32000
MAX_OUTPUT_TOKENS=512
MEMORY_TOP_K=5
HISTORY_MAX_MESSAGES=20
TEMPERATURE=0.9
SLEEP_SECONDS=2

# === Admin ===
ADMIN_USE_LLM=true
VERBOSE=false

# === Security (Production) ===
SECRET_KEY=your-secret-key-change-in-production
DATABASE_URL=sqlite:///./data/chatmode.db
```

### 5. Initialize Database

```bash
# Run database migrations
alembic upgrade head

# Or for fresh install
python -c "from database import init_db; init_db()"
```

### 6. Start the Server

**Development mode (with auto-reload):**
```bash
uvicorn web_admin:app --host 0.0.0.0 --port 8000 --reload
```

**Production mode:**
```bash
uvicorn web_admin:app --host 0.0.0.0 --port 8000 --workers 4
```

### 7. Access the Admin Console

Open your browser to: `http://localhost:8000`

---

## Ollama Setup (Local LLM)

If you want to run models locally:

### 1. Install Ollama

```bash
# Linux
curl -fsSL https://ollama.com/install.sh | sh

# macOS
brew install ollama
```

### 2. Pull Required Models

```bash
# Chat model
ollama pull llama3.2:3b

# Embedding model
ollama pull nomic-embed-text

# Optional: larger models
ollama pull mistral-nemo:12b
ollama pull qwen2.5:14b
```

### 3. Start Ollama Server

```bash
ollama serve
```

### 4. Configure ChatMode for Ollama

Update `.env`:
```env
EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL=nomic-embed-text
EMBEDDING_BASE_URL=http://localhost:11434
```

Update agent profiles (`profiles/*.json`) to use Ollama:
```json
{
    "api": "ollama",
    "url": "http://localhost:11434",
    "model": "llama3.2:3b"
}
```

---

## Docker Deployment

### Using Docker Compose

```bash
# Build and start
docker compose up -d

# View logs
docker compose logs -f

# Stop
docker compose down
```

### Docker Compose Configuration

```yaml
# compose.yaml
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

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create directories
RUN mkdir -p data/chroma tts_out

EXPOSE 8000

CMD ["uvicorn", "web_admin:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Production Deployment

### Recommended Stack

```
┌─────────────────────────────────────────────────────────┐
│                    Load Balancer                        │
│                  (nginx/Traefik)                        │
└─────────────────────┬───────────────────────────────────┘
                      │
        ┌─────────────┴─────────────┐
        │                           │
┌───────▼───────┐           ┌───────▼───────┐
│  ChatMode 1   │           │  ChatMode 2   │
│  (uvicorn)    │           │  (uvicorn)    │
└───────┬───────┘           └───────┬───────┘
        │                           │
        └─────────────┬─────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
┌───────▼───────┐ ┌───▼───┐ ┌───────▼───────┐
│  PostgreSQL   │ │ Redis │ │ Object Store  │
│  (sessions)   │ │(cache)│ │ (S3/Azure)    │
└───────────────┘ └───────┘ └───────────────┘
```

### Nginx Reverse Proxy

```nginx
upstream chatmode {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
}

server {
    listen 80;
    server_name chatmode.example.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name chatmode.example.com;

    ssl_certificate /etc/letsencrypt/live/chatmode.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/chatmode.example.com/privkey.pem;

    client_max_body_size 50M;  # For audio uploads

    location / {
        proxy_pass http://chatmode;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    location /audio/ {
        alias /var/www/chatmode/tts_out/;
        expires 1d;
        add_header Cache-Control "public, immutable";
    }
}
```

### Systemd Service

```ini
# /etc/systemd/system/chatmode.service
[Unit]
Description=ChatMode AI Agent Platform
After=network.target

[Service]
Type=exec
User=chatmode
Group=chatmode
WorkingDirectory=/opt/chatmode
Environment=PATH=/opt/chatmode/.venv/bin
ExecStart=/opt/chatmode/.venv/bin/uvicorn web_admin:app --host 127.0.0.1 --port 8000 --workers 4
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

---

## GPU Configuration

### NVIDIA GPU Support

For Ollama with GPU acceleration:

1. **Install NVIDIA drivers:**
```bash
sudo apt install nvidia-driver-535
```

2. **Install NVIDIA Container Toolkit:**
```bash
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt update
sudo apt install -y nvidia-container-toolkit
sudo systemctl restart docker
```

3. **Verify GPU access:**
```bash
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi
```

### Memory Requirements

| Model Size | VRAM Required | Example Models |
|------------|--------------|----------------|
| 1-3B | 2-4 GB | qwen:0.5b, llama3.2:1b |
| 7-8B | 6-8 GB | llama3:8b, mistral:7b |
| 12-14B | 10-12 GB | mistral-nemo:12b, qwen2.5:14b |
| 30-34B | 24-32 GB | codellama:34b |
| 70B+ | 48-80 GB | llama3:70b |

### CPU-Only Mode

If no GPU is available, set environment variable:
```bash
export OLLAMA_NUM_GPU=0
```

---

## Environment Variables Reference

See [Configuration Reference](./03-configuration.md) for complete list.

---

## Verification Steps

After setup, verify the installation:

```bash
# 1. Check server is running
curl http://localhost:8000/status

# 2. Check agents are loaded
curl http://localhost:8000/agents

# 3. Test Ollama connection (if using)
curl http://localhost:11434/api/tags

# 4. Test embedding generation
python -c "
from config import load_settings
from providers import build_embedding_provider
settings = load_settings()
provider = build_embedding_provider(
    settings.embedding_provider,
    settings.embedding_base_url,
    settings.embedding_api_key,
    settings.embedding_model
)
result = provider.embed(['test'])
print(f'Embedding dimension: {len(result[0])}')
"
```

---

## Troubleshooting Setup

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: chromadb` | `pip install chromadb` |
| `Connection refused` on Ollama | Start Ollama: `ollama serve` |
| `CUDA out of memory` | Use smaller model or reduce batch size |
| Port 8000 in use | Kill process: `fuser -k 8000/tcp` |
| Permission denied on tts_out | `chmod 755 tts_out` |

---

*Next: [Configuration Reference](./03-configuration.md)*
