# ChatMode Documentation

Welcome to the official ChatMode documentation. This is the single source of truth for understanding, deploying, and extending the ChatMode platform.

## What is ChatMode?

ChatMode is an **AI agent orchestration platform** that enables multi-agent conversations with rich personality modeling, long-term memory, voice synthesis (TTS), and administrative oversight. It supports multiple LLM providers (OpenAI-compatible APIs and Ollama) and provides a web-based admin console for real-time conversation management.

---

## Documentation Structure

| Section | Description |
|---------|-------------|
| [Architecture Overview](./01-architecture.md) | System components, data flow, and design decisions |
| [Setup & Deployment](./02-setup-deployment.md) | Local development, production deployment, GPU notes |
| [Configuration Reference](./03-configuration.md) | All settings, environment variables, defaults |
| [API Reference](./04-api-reference.md) | REST endpoints, schemas, authentication, error codes |
| [Agent System](./05-agent-system.md) | Roles, prompts, memory, provider routing, safety |
| [Agent Manager](./06-agent-manager.md) | Admin console for managing agents (CRUD, RBAC, audit) |
| [Chat & Voice](./07-chat-voice.md) | Message handling, audio attachments, playback, permissions |
| [Troubleshooting & FAQ](./08-troubleshooting.md) | Common issues and solutions |
| [Assumptions & Design Decisions](./09-assumptions.md) | Documented decisions and rationale |

---

## Quick Links

- **Start a conversation**: `POST /start` with a topic
- **View status**: `GET /status`
- **Manage agents**: `GET /api/v1/agents`
- **Admin Console**: Open `http://localhost:8000/` in your browser

---

## Getting Started

```bash
# Clone and setup
git clone <repo-url>
cd ChatMode
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Start the server
uvicorn web_admin:app --host 0.0.0.0 --port 8000

# Open http://localhost:8000 in your browser
```

---

## Key Features

✅ **Multi-Agent Conversations** – Configure multiple AI agents with distinct personalities  
✅ **Provider Flexibility** – OpenAI, Ollama, Azure, and custom endpoints  
✅ **Long-Term Memory** – ChromaDB-backed semantic memory per agent  
✅ **Voice Synthesis** – Real-time TTS with customizable voices  
✅ **Admin Console** – Web UI for session management and oversight  
✅ **Agent Manager** – Full CRUD for agents with RBAC and audit logging  
✅ **Voice Attachments** – Attach and playback audio in chat messages  

---

## Version

- **Documentation Version**: 1.0.0
- **ChatMode Version**: See `requirements.txt` for dependencies

---

## Contributing

See the main README.md for contribution guidelines.

---

*Last updated: January 2026*
