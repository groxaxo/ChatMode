# Troubleshooting & FAQ

Common issues and solutions for ChatMode.

---

## Quick Diagnostics

```bash
# Check server status
curl -s http://localhost:8000/status | jq

# Check Ollama connection
curl -s http://localhost:11434/api/tags | jq

# Check loaded agents
curl -s http://localhost:8000/agents | jq

# Check database connection
python -c "from database import test_connection; test_connection()"

# Check embedding generation
python -c "
from config import load_settings
from providers import build_embedding_provider
settings = load_settings()
p = build_embedding_provider(settings.embedding_provider, settings.embedding_base_url, '', settings.embedding_model)
print(f'Embedding dimension: {len(p.embed([\"test\"])[0])}')
"
```

---

## Common Issues

### Server Won't Start

**Error: Port already in use**
```
ERROR: [Errno 98] Address already in use
```

**Solution:**
```bash
# Find and kill process using port 8000
fuser -k 8000/tcp
# Or
lsof -ti:8000 | xargs kill -9
```

---

**Error: Module not found**
```
ModuleNotFoundError: No module named 'chromadb'
```

**Solution:**
```bash
pip install -r requirements.txt
# Or specifically
pip install chromadb
```

---

### Agent Loading Fails

**Error: Failed to load agent**
```
Failed to load agent lawyer: [Errno 2] No such file or directory
```

**Cause:** Profile path in `agent_config.json` is incorrect.

**Solution:**
1. Check `agent_config.json` has correct absolute paths
2. Ensure profile JSON files exist in `profiles/` directory
3. Use absolute paths or paths relative to project root

```json
{
  "agents": [
    {
      "name": "lawyer",
      "file": "/home/user/ChatMode/profiles/lawyer.json"
    }
  ]
}
```

---

### LLM Connection Issues

**Error: Connection refused (Ollama)**
```
requests.exceptions.ConnectionError: Connection refused
```

**Solutions:**
1. Start Ollama server: `ollama serve`
2. Check Ollama is running: `ollama list`
3. Verify URL in `.env`: `OLLAMA_BASE_URL=http://localhost:11434`

---

**Error: 401 Unauthorized (OpenAI)**
```
openai.AuthenticationError: Incorrect API key
```

**Solutions:**
1. Verify API key in `.env`: `OPENAI_API_KEY=sk-...`
2. Check key is valid at https://platform.openai.com/api-keys
3. Ensure no trailing spaces in `.env` file

---

**Error: Model not found**
```
Error: model "mistral-nemo:12b" not found
```

**Solution:**
```bash
# Pull the model
ollama pull mistral-nemo:12b

# Or use available model
ollama list
```

---

### Memory/Embedding Issues

**Error: ChromaDB dimension mismatch**
```
chromadb.errors.InvalidDimensionException: Embedding dimension X does not match collection dimension Y
```

**Cause:** Embedding model changed after collection was created.

**Solution:**
```bash
# Remove existing collections and restart
rm -rf data/chroma/*
```

Or clear memory via API:
```bash
curl -X POST http://localhost:8000/memory/clear
```

---

**Error: Embedding failed**
```
Memory query failed: Connection refused
```

**Solutions:**
1. Check embedding provider is running
2. Verify `EMBEDDING_BASE_URL` in `.env`
3. Test embedding manually:
```bash
curl http://localhost:11434/api/embed -d '{"model":"nomic-embed-text","input":"test"}'
```

---

### TTS Issues

**Error: TTS failed**
```
TTSClient: Failed to generate speech
```

**Solutions:**
1. Check TTS is enabled: `TTS_ENABLED=true`
2. Verify TTS API key is set
3. Test TTS manually:
```python
from openai import OpenAI
client = OpenAI(base_url="https://api.openai.com/v1", api_key="sk-...")
response = client.audio.speech.create(model="tts-1", voice="alloy", input="Hello")
```

---

**No audio playing in browser**

**Solutions:**
1. Check audio files exist in `tts_out/`
2. Verify audio URL is accessible: `curl http://localhost:8000/audio/filename.mp3`
3. Check browser console for errors
4. Ensure CORS is configured

---

### Database Issues

**Error: Database locked**
```
sqlite3.OperationalError: database is locked
```

**Cause:** Multiple processes accessing SQLite.

**Solutions:**
1. Use only one server instance
2. Migrate to PostgreSQL for production
3. Increase busy timeout:
```python
engine = create_engine("sqlite:///...", connect_args={"timeout": 30})
```

---

**Error: Migration failed**
```
alembic.util.exc.CommandError: Target database is not up to date
```

**Solution:**
```bash
# Check current state
alembic current

# Run pending migrations
alembic upgrade head

# If corrupted, reset
alembic stamp head
```

---

### Authentication Issues

**Error: 401 Unauthorized**
```json
{"error": {"code": "UNAUTHORIZED", "message": "Token expired"}}
```

**Solution:**
1. Login again to get new token
2. Check `SECRET_KEY` hasn't changed
3. Verify token is included in request:
```bash
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/agents
```

---

**Error: 403 Forbidden**
```json
{"error": {"code": "FORBIDDEN", "message": "Insufficient permissions"}}
```

**Cause:** User role doesn't have permission for action.

**Solution:**
1. Check user role in database
2. Contact admin to upgrade permissions
3. Use admin account for administrative tasks

---

### Performance Issues

**Slow response times**

**Diagnostics:**
```bash
# Check model inference time
time curl -s http://localhost:11434/api/generate -d '{"model":"llama3.2:3b","prompt":"Hello"}'

# Check embedding time
time curl -s http://localhost:11434/api/embed -d '{"model":"nomic-embed-text","input":"test"}'
```

**Solutions:**
1. Use smaller model
2. Reduce `MEMORY_TOP_K`
3. Reduce `MAX_OUTPUT_TOKENS`
4. Enable GPU acceleration
5. Increase `num_ctx` for model

---

**High memory usage**

**Solutions:**
1. Reduce number of agents
2. Clear old ChromaDB data
3. Limit conversation history: `HISTORY_MAX_MESSAGES=10`
4. Use smaller embedding model

---

## FAQ

### General

**Q: How many agents can run simultaneously?**

A: There's no hard limit. Practical limit depends on memory and API rate limits. Tested with up to 10 agents.

---

**Q: Can I use different models for different agents?**

A: Yes, each agent profile specifies its own model. You can mix Ollama and OpenAI agents.

---

**Q: How do I add a new agent?**

A: 
1. Create profile JSON in `profiles/`
2. Add entry to `agent_config.json`
3. Restart session (agent loads automatically)

Or use Agent Manager UI.

---

### Models & Providers

**Q: What models are supported?**

A: Any model accessible via:
- Ollama API
- OpenAI-compatible API (OpenAI, Azure OpenAI, vLLM, etc.)

---

**Q: How do I use Azure OpenAI?**

A: Set in profile or `.env`:
```json
{
    "api": "openai",
    "url": "https://your-resource.openai.azure.com/openai/deployments/gpt-4o",
    "api_key": "your-azure-key",
    "model": "gpt-4o"
}
```

---

**Q: Can I use local models only (no API)?**

A: Yes, configure all agents to use Ollama with locally pulled models.

---

### Memory & Data

**Q: How is conversation history stored?**

A: 
- **Short-term**: In-memory (lost on restart)
- **Long-term**: ChromaDB vector store (persisted to disk)

---

**Q: How do I backup data?**

A:
```bash
# Backup ChromaDB
cp -r data/chroma data/chroma_backup

# Backup database
cp data/chatmode.db data/chatmode_backup.db

# Backup audio
cp -r data/audio data/audio_backup
```

---

**Q: How do I clear all data?**

A:
```bash
# Clear memory only
curl -X POST http://localhost:8000/memory/clear

# Clear everything
rm -rf data/chroma/* data/chatmode.db tts_out/*
```

---

### Voice & Audio

**Q: What TTS providers are supported?**

A: OpenAI TTS API and any compatible endpoint. ElevenLabs via adapter.

---

**Q: How do I change voices per agent?**

A: Set in profile:
```json
{
    "speak_model": {
        "voice": "nova"
    }
}
```

---

**Q: What audio formats are supported for upload?**

A: MP3, WAV, OGG, WebM (up to 25MB, 5 minutes)

---

### Admin & Security

**Q: How do I create admin user?**

A:
```python
# Using CLI
python -c "
from database import SessionLocal
from models import User
from auth import hash_password

db = SessionLocal()
user = User(
    username='admin',
    password_hash=hash_password('your-password'),
    role='admin'
)
db.add(user)
db.commit()
"
```

---

**Q: How do I reset admin password?**

A:
```python
from database import SessionLocal
from models import User
from auth import hash_password

db = SessionLocal()
user = db.query(User).filter(User.username == 'admin').first()
user.password_hash = hash_password('new-password')
db.commit()
```

---

**Q: Are API keys encrypted?**

A: Yes, API keys stored in database are encrypted. Keys in `.env` and profile JSON are plaintext (protect these files).

---

## Getting Help

1. Check this troubleshooting guide
2. Search existing issues on GitHub
3. Check server logs: `uvicorn web_admin:app --log-level debug`
4. Open new issue with:
   - Error message (full traceback)
   - Steps to reproduce
   - Environment info (OS, Python version, etc.)
   - Relevant config (redact secrets)

---

*Next: [Assumptions & Design Decisions](./09-assumptions.md)*
