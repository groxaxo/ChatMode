# ChatMode Quick Reference

## 🚀 Launch Options

### Option 1: Interactive Launcher (Recommended)
```bash
./launch.sh
```

### Option 2: Direct Commands

**Web Interface:**
```bash
conda run -n base python web_admin.py
# → http://localhost:8000
```

**Agent Profile Manager:**
```bash
conda run -n base python agent_profile_manager.py
# → http://localhost:7860
```

**CLI Commands:**
```bash
conda run -n base python agent_manager.py list-agents
conda run -n base python agent_manager.py start "topic"
conda run -n base python agent_manager.py status
conda run -n base python agent_manager.py stop
```

---

## 📁 What's What

| File/Tool | Purpose | Access |
|-----------|---------|--------|
| **unified.html** | Single-page web interface | http://localhost:8000 |
| **agent_profile_manager.py** | Visual agent editor (Gradio) | http://localhost:7860 |
| **agent_manager.py** | CLI session management | Command line |
| **launch.sh** | Interactive launcher | `./launch.sh` |

---

## 🎯 Common Tasks

### Start a Session
**Web:** Go to Session Control tab → Enter topic → Click Start  
**CLI:** `conda run -n base python agent_manager.py start "your topic"`

### Create an Agent
**Gradio:** Run `agent_profile_manager.py` → Create Agent tab  
**Manual:** Edit `profiles/name.json` + `agent_config.json`

### View Live Chat
**Web:** Live Monitor tab (auto-refreshes every 2s)

### Manage Agents
**Gradio:** All tabs in `agent_profile_manager.py`  
**CLI:** `conda run -n base python agent_manager.py list-agents`

---

## 🔧 Troubleshooting

**Gradio not found:**
```bash
conda run -n base pip install gradio
```

**Port already in use:**
```bash
# Check what's using the port
lsof -i :8000
# Or change port in script
```

**Agents not showing:**
```bash
cat agent_config.json
ls profiles/
```

---

## 📚 Full Documentation

- **UNIFIED_INTERFACE_GUIDE.md** - Complete usage guide
- **UPDATE_SUMMARY.md** - What changed
- **README.md** - Project overview

---

**Quick Start**: Run `./launch.sh` and choose option 1! 🎉
