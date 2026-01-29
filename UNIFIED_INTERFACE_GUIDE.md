# ChatMode - Unified Interface Guide

## 🎯 Overview

ChatMode now features a **unified web interface** and **dual agent management tools** for better usability.

---

## 🌐 Unified Web Interface

The frontend has been consolidated into a single page with three tabs:

### Access
```bash
# Start the web server
python web_admin.py
# Then open: http://localhost:8000
```

### Tabs

1. **Session Control** - Start/stop sessions, inject messages, manage topics
2. **Live Monitor** - Real-time feed of agent conversations
3. **Agent Overview** - View configured agents at a glance

### Features
- ✅ Single-page experience with tab navigation
- ✅ Real-time status updates (2-second polling)
- ✅ Unified controls across all tabs
- ✅ Audio playback support for TTS
- ✅ Responsive design for mobile/desktop

---

## 🤖 Agent Management Tools

You now have **two ways** to manage agent profiles:

### Option 1: CLI Tool (Quick Tasks)

Perfect for quick operations and scripting.

```bash
# List all agents
python agent_manager.py list-agents

# Start a session
python agent_manager.py start "Is consciousness computable?"

# Check status
python agent_manager.py status

# Stop session
python agent_manager.py stop

# Resume session
python agent_manager.py resume

# Inject a message
python agent_manager.py inject "Admin" "Consider the ethical implications"

# Clear memory
python agent_manager.py clear-memory
```

### Option 2: Gradio UI (Profile Management)

Perfect for creating and editing agent profiles with a visual interface.

```bash
# Launch the Gradio agent profile manager
python agent_profile_manager.py
# Then open: http://localhost:7860
```

#### Gradio Features:
- 📋 **List Agents** - View all configured agents with details
- ✏️ **Edit Agent** - Modify existing agent profiles
- ➕ **Create Agent** - Add new agent profiles
- 🗑️ **Delete Agent** - Remove agents from config
- 📄 **View Raw JSON** - Inspect raw profile data

#### Creating a New Agent via Gradio:

1. Go to "Create Agent" tab
2. Fill in:
   - **Agent ID**: Internal identifier (e.g., `scientist`)
   - **Display Name**: Human-readable name (e.g., `Dr. Sarah Chen`)
   - **Model**: LLM model (e.g., `gpt-4`, `llama-3.1`)
   - **API Type**: `openai`, `ollama`, `anthropic`, etc.
   - **API URL**: Optional custom endpoint
   - **System Prompt**: Agent personality and behavior
3. Click "Create Agent"

#### Editing an Agent:

1. Go to "Edit Agent" tab
2. Select agent from dropdown
3. Modify fields
4. Click "Save Changes"

---

## 📁 File Structure

```
ChatMode/
├── frontend/
│   ├── unified.html        # NEW: Single-page unified interface
│   ├── index.html          # Legacy: Admin console
│   └── chat.html           # Legacy: Live monitor
├── agent_manager.py        # CLI tool for sessions
├── agent_profile_manager.py # NEW: Gradio UI for profiles
├── web_admin.py            # Web server (serves unified.html)
├── agent_config.json       # Agent configuration
└── profiles/               # Agent profile JSON files
    ├── lawyer.json
    ├── crook.json
    ├── prostitute.json
    └── church_woman.json
```

---

## 🚀 Quick Start

### 1. Launch Web Interface
```bash
python web_admin.py
# Open http://localhost:8000
```

### 2. Manage Agents (Choose One)

**CLI approach:**
```bash
python agent_manager.py list-agents
```

**GUI approach:**
```bash
python agent_profile_manager.py
# Open http://localhost:7860
```

### 3. Start a Session

**Via Web UI:**
- Go to "Session Control" tab
- Enter topic
- Click "Start"

**Via CLI:**
```bash
python agent_manager.py start "Your topic here"
```

---

## 🎨 Customization

### Add a New Agent Profile

**Method 1: Gradio UI**
1. Run `python agent_profile_manager.py`
2. Use "Create Agent" tab

**Method 2: Manual**
1. Create `profiles/my_agent.json`:
```json
{
    "name": "My Agent",
    "model": "gpt-4",
    "api": "openai",
    "url": "http://localhost:11434",
    "conversing": "You are My Agent. Your role is..."
}
```

2. Add to `agent_config.json`:
```json
{
  "agents": [
    {
      "name": "my_agent",
      "file": "profiles/my_agent.json"
    }
  ]
}
```

---

## 💡 Tips

- **Use unified.html** for day-to-day operations - it has everything in one place
- **Use CLI tool** for automation and scripting
- **Use Gradio UI** for creating/editing agent personalities
- Legacy `index.html` and `chat.html` are kept for backward compatibility
- The Gradio interface runs on port 7860 by default
- Web admin runs on port 8000 by default

---

## 🐛 Troubleshooting

**Gradio not found:**
```bash
pip install gradio
```

**Port already in use:**
```bash
# Change port in agent_profile_manager.py
demo.launch(server_port=7861)  # Use different port
```

**Agents not showing:**
```bash
# Verify config
cat agent_config.json
# Check profiles exist
ls profiles/
```

---

## 📝 Migration Notes

- Old `index.html` → Now **"Session Control"** tab in unified.html
- Old `chat.html` → Now **"Live Monitor"** tab in unified.html
- New **"Agent Overview"** tab shows all agents
- CLI tool (`agent_manager.py`) remains unchanged
- New Gradio UI (`agent_profile_manager.py`) for profile management

Enjoy the streamlined ChatMode experience! 🎉
