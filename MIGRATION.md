# ChatMode Migration Guide

This guide explains the streamlining changes made to ChatMode, providing a clear migration path for existing users.

---

## Overview

ChatMode has been refactored to provide a cleaner, more focused experience around a single-session, multi-agent conversation model. The goal is to eliminate duplicate interfaces and documentation while preserving all core functionality.

---

## What Changed

### ✅ Phase 1: Documentation Consolidation (COMPLETED)

**Before:**
- Scattered documentation across 19+ files
- Duplicated information in README, QUICKSTART, UNIFIED_INTERFACE_GUIDE
- Numbered docs (01-09) mixed with topic docs
- Outdated changelog files (UPDATE_SUMMARY, IMPLEMENTATION_SUMMARY, etc.)

**After:**
- Streamlined docs/ directory with 6 focused guides:
  - `docs/ARCHITECTURE.md` – System design and components
  - `docs/SETUP.md` – Installation and deployment
  - `docs/CONFIG.md` – Configuration reference
  - `docs/AGENTS.md` – Agent system and management
  - `docs/VOICE.md` – TTS integration
  - `docs/TROUBLESHOOTING.md` – Common issues and solutions
- Concise root `README.md` with quick start and links
- Comprehensive `.env.example` for configuration

**Deleted Files:**
- `QUICKSTART.md` → Merged into README.md and docs/SETUP.md
- `UNIFIED_INTERFACE_GUIDE.md` → Merged into docs/SETUP.md
- `UPDATE_SUMMARY.md` → Outdated, removed
- `IMPLEMENTATION_SUMMARY.md` → Outdated, removed
- `MIGRATION_MASTERPLAN.md` → Outdated, removed
- `CHATMODE_AUDIT_REPORT.md` → Outdated, removed
- `ACCEPTANCE_CRITERIA.md` → Outdated, removed
- `DOCUMENTATION.md` → Replaced by new README.md
- `FRONTEND_GUIDE.md` → Merged into docs/SETUP.md
- `docs/01-architecture.md` → Replaced by docs/ARCHITECTURE.md
- `docs/02-setup-deployment.md` → Replaced by docs/SETUP.md
- `docs/03-configuration.md` → Replaced by docs/CONFIG.md
- `docs/04-api-reference.md` → Functionality distributed
- `docs/05-agent-system.md` → Replaced by docs/AGENTS.md
- `docs/06-agent-manager.md` → Replaced by docs/AGENTS.md
- `docs/07-chat-voice.md` → Replaced by docs/VOICE.md
- `docs/08-troubleshooting.md` → Replaced by docs/TROUBLESHOOTING.md
- `docs/09-assumptions.md` → Outdated, removed
- `docs/README.md` → Replaced by main README.md

---

### 🔄 Phase 2: Frontend Consolidation (PLANNED)

**Current State:**
- Multiple frontend pages: `index.html`, `chat.html`, `unified.html`
- Separate Gradio-based `agent_profile_manager.py` for agent management
- Some feature duplication between interfaces

**Planned Changes:**
- **Single Interface**: `frontend/unified.html` becomes the only UI
  - Tab 1: Session Control (start/stop/inject)
  - Tab 2: Live Monitor (real-time conversation view)
  - Tab 3: Agent Overview (view all agents)
  - Tab 4: Agent Manager (create/edit/delete agents) **← NEW**
  
- **Remove**:
  - `frontend/index.html` – Functionality merged into unified.html Tab 1
  - `frontend/chat.html` – Functionality merged into unified.html Tab 2
  - `agent_profile_manager.py` – Gradio UI replaced by web UI agent manager
  
- **API Enhancements**:
  - Add POST `/agents` for creating new agents
  - Add DELETE `/agents/{name}` for deleting agents
  - Enhance PUT `/agents/{name}` for full profile updates

---

### 🔄 Phase 3: Backend Consolidation (PLANNED)

**Current State:**
- Multiple entry points: `main.py`, `web_admin.py`, `web_admin_crewai.py`
- Mix of session implementations: `session.py`, `session_crewai.py`
- Experimental/duplicate files scattered in root

**Planned Changes:**
- **Single Entry Point**: Create `chatmode/__main__.py`
  ```bash
  # Start web server
  python -m chatmode serve
  
  # Run CLI
  python -m chatmode cli start "topic"
  ```

- **Organize into Package**:
  ```
  chatmode/
  ├── __init__.py
  ├── __main__.py          # Entry point
  ├── core/
  │   ├── agent.py
  │   ├── session.py
  │   ├── memory.py
  │   └── providers.py
  ├── api/
  │   ├── server.py        # FastAPI app
  │   └── routes/
  ├── cli/
  │   └── manager.py       # CLI commands
  └── config.py
  ```

- **Remove Experimental Files**:
  - `session_crewai.py` – If CrewAI integration not actively used
  - `web_admin_crewai.py` – Consolidate into main web_admin
  - `crewai_agent.py` – Consolidate or remove
  - `debate_crew.py` – Example code, can be removed
  - `switch_backend.py` – Utility, can be removed
  - `bootstrap.py`, `demo_setup.py` – One-time scripts
  - `audit.py` – Move to chatmode/audit.py if needed

- **Consolidate Launch Scripts**:
  - Keep: `launch.sh` (updated to use `python -m chatmode`)
  - Remove: `uvicorn_start.sh` (redundant)

---

### 🔄 Phase 4: Configuration & Deployment (PLANNED)

**Current State:**
- Environment variables documented in multiple places
- Docker setup works but could be simplified

**Planned Changes:**
- ✅ **Unified Configuration**: `.env.example` created with all options
- **Conda Environment**: Create `environment.yml` for reproducible setup
  ```yaml
  name: ChatMode
  channels:
    - conda-forge
  dependencies:
    - python=3.11
    - pip
    - pip:
      - -r requirements.txt
  ```

- **Docker Compose**: Enhanced with better defaults
- **Systemd Service**: Template in `docs/SETUP.md`

---

## Migration Steps

### For Existing Users

If you're currently using ChatMode, here's how to migrate:

#### 1. Update Documentation References

Old documentation paths are now consolidated:

| Old Path | New Path |
|----------|----------|
| `QUICKSTART.md` | `README.md` (Quick Start section) |
| `docs/02-setup-deployment.md` | `docs/SETUP.md` |
| `docs/03-configuration.md` | `docs/CONFIG.md` |
| `docs/05-agent-system.md` | `docs/AGENTS.md` |
| `docs/06-agent-manager.md` | `docs/AGENTS.md` |
| `docs/07-chat-voice.md` | `docs/VOICE.md` |
| `docs/08-troubleshooting.md` | `docs/TROUBLESHOOTING.md` |

#### 2. Use .env.example as Template

The new `.env.example` provides a comprehensive configuration template:

```bash
cp .env.example .env
nano .env  # Update with your settings
```

#### 3. Access Points (Current - Phase 1)

**Web Interface:**
```bash
uvicorn web_admin:app --host 0.0.0.0 --port 8000
# Access: http://localhost:8000
```

**CLI Tool:**
```bash
python agent_manager.py list-agents
python agent_manager.py start "topic"
```

**Agent Profile Manager (Gradio):**
```bash
python agent_profile_manager.py
# Access: http://localhost:7860
```

#### 4. After Future Phases (Post Phase 3)

**Unified Entry Point:**
```bash
# Start web server
python -m chatmode serve --port 8000

# CLI operations
python -m chatmode cli list-agents
python -m chatmode cli start "topic"
```

#### 5. Agent Management

**Current (Phase 1):**
- Use Gradio UI (`agent_profile_manager.py`) OR
- Edit JSON files in `profiles/` manually

**After Phase 2:**
- Use Agent Manager tab in unified web interface at http://localhost:8000

---

## API Changes

### Current API Endpoints (Phase 1)

All endpoints unchanged:

```
GET  /status              # Session status
POST /start               # Start session
POST /stop                # Stop session
POST /resume              # Resume session
POST /messages            # Inject message
POST /memory/clear        # Clear memory

GET  /agents              # List all agents
GET  /agents/{name}       # Get agent profile
POST /agents/{name}       # Update agent profile
```

### Planned API Additions (Phase 2)

New endpoints for full CRUD:

```
POST   /agents            # Create new agent
DELETE /agents/{name}     # Delete agent
PUT    /agents/{name}     # Full profile update
```

---

## File Structure Changes

### Current Structure (Phase 1)

```
ChatMode/
├── README.md              # ✅ Updated - concise overview
├── .env.example           # ✅ New - comprehensive config template
├── docs/                  # ✅ Updated - streamlined guides
│   ├── ARCHITECTURE.md    # ✅ New
│   ├── SETUP.md           # ✅ New
│   ├── CONFIG.md          # ✅ New
│   ├── AGENTS.md          # ✅ New
│   ├── VOICE.md           # ✅ New
│   └── TROUBLESHOOTING.md # ✅ New
├── frontend/
│   ├── unified.html       # Current main interface
│   ├── index.html         # Legacy (to be removed)
│   └── chat.html          # Legacy (to be removed)
├── agent_manager.py       # CLI tool (current)
├── agent_profile_manager.py  # Gradio UI (to be removed)
├── web_admin.py           # API server (current)
└── [other core files]
```

### Planned Final Structure (After All Phases)

```
ChatMode/
├── README.md
├── .env.example
├── environment.yml        # New - Conda environment
├── docs/
│   ├── ARCHITECTURE.md
│   ├── SETUP.md
│   ├── CONFIG.md
│   ├── AGENTS.md
│   ├── VOICE.md
│   └── TROUBLESHOOTING.md
├── frontend/
│   └── unified.html       # Only frontend interface
├── chatmode/              # New - Package structure
│   ├── __init__.py
│   ├── __main__.py        # Entry point
│   ├── core/
│   ├── api/
│   └── cli/
├── profiles/              # Agent JSON files
├── data/                  # ChromaDB, database
└── tts_out/              # Generated audio
```

---

## Breaking Changes

### Phase 1 (COMPLETED)
- **None** – Only documentation reorganization, no functional changes

### Phase 2 (PLANNED)
- `frontend/index.html` removed → Use `frontend/unified.html`
- `frontend/chat.html` removed → Use `frontend/unified.html`
- `agent_profile_manager.py` removed → Use unified web UI Agent Manager tab

### Phase 3 (PLANNED)
- Entry point changes: `python main.py` → `python -m chatmode serve`
- CLI changes: `python agent_manager.py` → `python -m chatmode cli`
- Import paths change: `from agent import ChatAgent` → `from chatmode.core.agent import ChatAgent`

---

## Compatibility Notes

### Backward Compatibility

**Configuration:**
- All environment variables remain the same
- `.env` file format unchanged
- Agent profile JSON format unchanged

**Agent Profiles:**
- Existing `profiles/*.json` files work without modification
- `agent_config.json` format unchanged

**Memory:**
- ChromaDB data persists across updates
- No migration needed for existing memory stores

### What Stays the Same

- **Core functionality**: Multi-agent conversations, memory, TTS
- **Session model**: Single active conversation at a time
- **Provider support**: OpenAI and Ollama integration unchanged
- **Audio**: TTS configuration and output format unchanged
- **Database**: SQLite schema unchanged (if using database features)

---

## Rollback Plan

If you need to rollback to the pre-refactoring state:

### Phase 1 Rollback (Documentation Only)

```bash
# Checkout previous commit before Phase 1
git checkout <commit-before-phase-1>

# Or cherry-pick old docs
git checkout <commit> -- docs/01-architecture.md docs/02-setup-deployment.md
```

**Note**: Phase 1 changes are documentation-only, so rollback is not required for functionality.

### Future Phase Rollback

Rollback procedures will be documented when those phases are implemented.

---

## Testing Your Migration

After migrating, verify functionality:

### 1. Basic Operations

```bash
# Start server
uvicorn web_admin:app --port 8000

# Test API
curl http://localhost:8000/status
curl http://localhost:8000/agents
```

### 2. Web Interface

1. Open http://localhost:8000
2. Navigate through all tabs
3. Start a test session
4. Verify agents appear in Agent Overview

### 3. Agent Management

**Current (Phase 1):**
```bash
python agent_profile_manager.py
```

**After Phase 2:**
- Use Agent Manager tab in web interface

### 4. CLI Operations

```bash
python agent_manager.py list-agents
python agent_manager.py start "Test topic"
python agent_manager.py status
python agent_manager.py stop
```

---

## Getting Help

If you encounter issues during migration:

1. Check **[TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)**
2. Review **[SETUP.md](docs/SETUP.md)** for configuration
3. Open a GitHub issue with:
   - Error messages
   - Steps to reproduce
   - Your environment (OS, Python version)
   - Config files (redact sensitive data)

---

## Timeline

| Phase | Status | Completion |
|-------|--------|------------|
| Phase 1: Documentation | ✅ Complete | 2024-01-30 |
| Phase 2: Frontend | 🔄 Planned | TBD |
| Phase 3: Backend | 🔄 Planned | TBD |
| Phase 4: Deployment | 🔄 Planned | TBD |

---

**Current State**: Phase 1 complete. All documentation has been streamlined and consolidated. Core functionality remains unchanged and fully operational.

For the latest information, see the [README.md](README.md) and [docs/](docs/) directory.
