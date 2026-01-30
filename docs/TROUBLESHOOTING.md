# ChatMode Troubleshooting Guide

Common issues, solutions, and FAQ for ChatMode.

---

## Quick Diagnostics

Run these commands to check system health:

```bash
# Check server status
curl -s http://localhost:8000/status | jq

# Check Ollama connection
curl -s http://localhost:11434/api/tags | jq

# Check loaded agents
curl -s http://localhost:8000/agents | jq

# Test embedding generation
python -c "
from config import load_settings
from providers import build_embedding_provider
settings = load_settings()
p = build_embedding_provider(
    settings.embedding_provider,
    settings.embedding_base_url,
    '',
    settings.embedding_model
)
print(f'Embedding dimension: {len(p.embed([\"test\"])[0])}')
"
```

---

## Server Issues

### Port Already in Use

**Error:**
```
ERROR: [Errno 98] Address already in use
```

**Solutions:**
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use a different port
uvicorn web_admin:app --port 8001
```

### Module Not Found

**Error:**
```
ModuleNotFoundError: No module named 'chromadb'
```

**Solution:**
```bash
# Install all dependencies
pip install -r requirements.txt

# Or install specific missing package
pip install chromadb
```

### Database Connection Failed

**Error:**
```
sqlalchemy.exc.OperationalError: unable to open database file
```

**Solution:**
```bash
# Create data directory
mkdir -p data

# Initialize database
python -c "from database import init_db; init_db()"

# Check permissions
chmod 755 data/
chmod 644 data/chatmode.db
```

---

## Agent Issues

### Agent Loading Failed

**Error:**
```
Failed to load agent lawyer: [Errno 2] No such file or directory: 'profiles/lawyer.json'
```

**Solutions:**

1. **Check profile exists:**
```bash
ls -la profiles/
```

2. **Verify agent_config.json:**
```json
{
  "agents": [
    {
      "name": "lawyer",
      "file": "profiles/lawyer.json"
    }
  ]
}
```

3. **Check file paths are relative to project root**

4. **Validate JSON syntax:**
```bash
cat profiles/lawyer.json | jq .
```

### Agent Not Responding

**Symptoms:**
- Session starts but no messages appear
- Agent seems stuck

**Solutions:**

1. **Check logs for errors:**
```bash
tail -f backend.log
```

2. **Verify model is loaded (Ollama):**
```bash
ollama list
# If model missing:
ollama pull llama3.2:3b
```

3. **Test LLM connection manually:**
```bash
# Ollama
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.2:3b",
  "prompt": "Hello"
}'

# OpenAI
curl https://api.openai.com/v1/chat/completions \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

4. **Check temperature isn't too low:**
```env
TEMPERATURE=0.9  # Should be > 0
```

---

## LLM Provider Issues

### Ollama Connection Refused

**Error:**
```
requests.exceptions.ConnectionError: Connection refused
```

**Solutions:**

1. **Start Ollama:**
```bash
ollama serve
```

2. **Check Ollama is running:**
```bash
ps aux | grep ollama
curl http://localhost:11434/api/tags
```

3. **Verify URL in .env:**
```env
OLLAMA_BASE_URL=http://localhost:11434
```

4. **If using Docker, check network:**
```env
# For host Ollama from Docker container
OLLAMA_BASE_URL=http://host.docker.internal:11434
```

### OpenAI Authentication Error

**Error:**
```
openai.AuthenticationError: Incorrect API key provided
```

**Solutions:**

1. **Check API key is set:**
```bash
grep OPENAI_API_KEY .env
```

2. **Verify key is valid:**
```bash
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

3. **Check for trailing spaces:**
```bash
# Remove any whitespace
sed -i 's/[[:space:]]*$//' .env
```

4. **Regenerate key at:** https://platform.openai.com/api-keys

### Model Not Found

**Error (Ollama):**
```
Error: model "mistral-nemo:12b" not found
```

**Solution:**
```bash
# Pull the model
ollama pull mistral-nemo:12b

# Or list available models
ollama list

# Update agent profile to use available model
```

**Error (OpenAI):**
```
Error: The model 'gpt-5' does not exist
```

**Solution:**
Update agent profile to use valid model:
```json
{
  "model": "gpt-4o-mini"
}
```

---

## Memory & Embedding Issues

### ChromaDB Dimension Mismatch

**Error:**
```
chromadb.errors.InvalidDimensionException: Embedding dimension 384 does not match collection dimension 768
```

**Cause:** Embedding model changed after ChromaDB collection was created.

**Solution:**
```bash
# Clear ChromaDB and restart
rm -rf data/chroma/

# Or via API
curl -X POST http://localhost:8000/memory/clear
```

### Embedding Generation Failed

**Error:**
```
Memory query failed: Connection refused
```

**Solutions:**

1. **Check embedding provider is running:**
```bash
# Ollama
curl http://localhost:11434/api/tags

# OpenAI
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

2. **Test embedding manually:**
```bash
# Ollama
curl http://localhost:11434/api/embed -d '{
  "model": "nomic-embed-text",
  "input": "test"
}'
```

3. **Verify configuration:**
```env
EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL=nomic-embed-text
EMBEDDING_BASE_URL=http://localhost:11434
```

### Memory Queries Too Slow

**Symptoms:**
- Slow response generation
- High memory usage

**Solutions:**

1. **Reduce MEMORY_TOP_K:**
```env
MEMORY_TOP_K=3  # Fetch fewer memories
```

2. **Clear old memories:**
```bash
rm -rf data/chroma/
```

3. **Limit conversation history:**
```env
HISTORY_MAX_MESSAGES=10
```

---

## TTS Issues

### TTS Not Generating Audio

**Error:**
```
TTSClient: Failed to generate speech
```

**Solutions:**

1. **Check TTS is enabled:**
```env
TTS_ENABLED=true
```

2. **Verify API key:**
```bash
grep TTS_API_KEY .env
```

3. **Test TTS manually:**
```bash
curl -X POST https://api.openai.com/v1/audio/speech \
  -H "Authorization: Bearer $TTS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "tts-1",
    "input": "Hello world",
    "voice": "alloy"
  }' --output test.mp3
```

4. **Check output directory exists:**
```bash
mkdir -p tts_out
chmod 755 tts_out
```

### Audio Not Playing in Browser

**Solutions:**

1. **Check audio files exist:**
```bash
ls -la tts_out/
```

2. **Verify URL is accessible:**
```bash
curl -I http://localhost:8000/audio/tts_out/filename.mp3
```

3. **Check browser console for errors** (F12)

4. **Verify MIME type:**
```bash
file tts_out/*.mp3
```

5. **Ensure CORS is configured** (should be by default)

### Poor Audio Quality

**Solutions:**

1. **Use HD model:**
```json
{
  "speak_model": {
    "model": "tts-1-hd",
    "voice": "nova"
  }
}
```

2. **Improve text normalization** – Remove special characters from agent responses

3. **Try different voice:**
```
alloy, echo, fable, onyx, nova, shimmer
```

---

## Web UI Issues

### Unified Interface Not Loading

**Symptoms:**
- Blank page
- 404 error

**Solutions:**

1. **Check frontend exists:**
```bash
ls -la frontend/unified.html
```

2. **Verify server is serving static files:**
```bash
curl http://localhost:8000/frontend/unified.html
```

3. **Check browser console** for JavaScript errors (F12)

4. **Hard refresh:** Ctrl+Shift+R (or Cmd+Shift+R on Mac)

### Live Monitor Not Updating

**Solutions:**

1. **Check /status endpoint:**
```bash
curl http://localhost:8000/status
```

2. **Verify polling is working** – Check browser Network tab (F12)

3. **Clear browser cache and reload**

4. **Check for JavaScript errors** in console

### Agent Manager Tab Not Working

**Solutions:**

1. **Check /agents endpoint:**
```bash
curl http://localhost:8000/agents
```

2. **Verify API routes are loaded:**
```bash
curl http://localhost:8000/docs
```

3. **Check browser console for errors**

---

## Performance Issues

### Slow Response Times

**Causes & Solutions:**

1. **Large context window:**
```env
MAX_CONTEXT_TOKENS=16000  # Reduce from 32000
```

2. **Too many memories retrieved:**
```env
MEMORY_TOP_K=3  # Reduce from 5
```

3. **Large conversation history:**
```env
HISTORY_MAX_MESSAGES=10  # Reduce from 20
```

4. **Slow model:**
   - Use smaller model (e.g., `llama3.2:3b` instead of `qwen2.5:14b`)
   - Or use faster API (OpenAI instead of local Ollama)

### High Memory Usage

**Solutions:**

1. **Clear ChromaDB:**
```bash
rm -rf data/chroma/
```

2. **Reduce context:**
```env
MAX_CONTEXT_TOKENS=8000
HISTORY_MAX_MESSAGES=10
```

3. **Restart server periodically:**
```bash
pkill -f web_admin
uvicorn web_admin:app --reload
```

### High Disk Usage

**Solutions:**

1. **Clean audio files:**
```bash
find tts_out -name "*.mp3" -mtime +7 -delete
```

2. **Archive old ChromaDB:**
```bash
tar -czf chroma_backup_$(date +%Y%m%d).tar.gz data/chroma/
rm -rf data/chroma/
```

3. **Clean logs:**
```bash
> backend.log
> uvicorn.log
```

---

## Configuration Issues

### Environment Variables Not Loading

**Solutions:**

1. **Check .env file exists:**
```bash
ls -la .env
```

2. **Verify syntax:**
```bash
cat .env
# No spaces around =
# No quotes unless needed
```

3. **Load manually:**
```bash
export $(cat .env | xargs)
```

4. **Check for typos:**
```bash
grep -i ollama .env
```

### Changes Not Taking Effect

**Solutions:**

1. **Restart server:**
```bash
pkill -f web_admin
uvicorn web_admin:app --reload
```

2. **Clear browser cache**

3. **Stop existing session:**
   - Go to Session Control
   - Click "Stop Session"
   - Start new session

---

## Debugging Tips

### Enable Verbose Logging

```env
VERBOSE=true
```

### Check Application Logs

```bash
tail -f backend.log
tail -f uvicorn.log
```

### Monitor Resource Usage

```bash
# CPU and memory
htop

# Disk usage
df -h
du -sh data/ tts_out/

# Network
netstat -tulpn | grep 8000
```

### Test Individual Components

```python
# Test config loading
python -c "from config import load_settings; s=load_settings(); print(s)"

# Test agent loading
python -c "from agent import ChatAgent; from config import load_settings; a=ChatAgent('test', 'profiles/lawyer.json', load_settings()); print(a.full_name)"

# Test memory
python -c "from memory import MemoryStore; m=MemoryStore('test', './data/chroma'); m.add('test', {}); print(m.count())"
```

---

## Getting Help

### Check Logs

1. Application logs: `backend.log`, `uvicorn.log`
2. Browser console: F12 → Console tab
3. Network requests: F12 → Network tab

### Gather Information

When reporting issues, include:

1. **Error message** (full traceback)
2. **Environment:**
   - OS (Linux, macOS, Windows)
   - Python version: `python --version`
   - ChatMode version/commit
3. **Configuration:**
   - `.env` settings (mask API keys)
   - Agent profiles used
4. **Steps to reproduce**

### Community Support

- GitHub Issues: https://github.com/groxaxo/ChatMode/issues
- Include logs and error messages
- Describe expected vs. actual behavior

---

*See also: [Setup Guide](./SETUP.md) | [Configuration](./CONFIG.md) | [Architecture](./ARCHITECTURE.md)*
