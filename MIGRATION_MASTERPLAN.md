# ChatMode → CrewAI Migration Masterplan

## Executive Summary

This document outlines the comprehensive plan to migrate ChatMode from a custom multi-agent implementation to the CrewAI framework. The migration will preserve existing functionality while gaining access to CrewAI's powerful features including structured task execution, advanced memory systems, and agent collaboration capabilities.

---

## Migration Goals

### Primary Objectives
1. **Replace custom agent system** with CrewAI's `Agent` and `Crew` classes
2. **Leverage CrewAI memory** (short-term, long-term, entity memory)
3. **Maintain backward compatibility** with existing profile format
4. **Preserve web admin functionality** for session control
5. **Keep TTS integration** as an optional feature

### Secondary Objectives
- Enable agent delegation and collaboration
- Support structured task definitions
- Add Flow support for complex workflows
- Improve observability and debugging

---

## Architecture Comparison

### Current Architecture
```
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│   ChatAgent   │────▶│ ChatProvider  │────▶│   OpenAI API  │
│   (Custom)    │     │   (Custom)    │     │   Ollama API  │
└───────┬───────┘     └───────────────┘     └───────────────┘
        │
        ▼
┌───────────────┐
│  MemoryStore  │────▶ ChromaDB
│   (Custom)    │
└───────────────┘
```

### Target Architecture with CrewAI
```
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│  CrewAI Agent │────▶│   CrewAI LLM  │────▶│   OpenAI API  │
│  (Framework)  │     │   (Built-in)  │     │   Ollama API  │
└───────┬───────┘     └───────────────┘     └───────────────┘
        │
        ▼
┌───────────────┐     ┌───────────────┐
│  CrewAI Crew  │────▶│ CrewAI Memory │────▶ ChromaDB/SQLite
│  (Orchestrate)│     │   (Built-in)  │
└───────────────┘     └───────────────┘
```

---

## Migration Phases

### Phase 1: Foundation Setup (Priority: Critical)

#### 1.1 Update Dependencies
**File: `requirements.txt`**

```diff
- openai>=1.40.0
- langchain>=0.2.0
+ crewai>=0.121.0
+ crewai-tools>=0.36.0
  requests>=2.31.0
  python-dotenv>=1.0.1
- chromadb>=0.5.0
  fastapi>=0.110.0
  uvicorn[standard]>=0.27.0
  jinja2>=3.1.3
  python-multipart>=0.0.9
```

#### 1.2 Create LLM Configuration Module
**New File: `llm_config.py`**

Purpose: Centralized LLM configuration compatible with CrewAI's LLM class

```python
# Supports:
# - OpenAI (default)
# - Ollama (local)
# - Azure OpenAI
# - Anthropic Claude
# - Custom providers via base_url
```

---

### Phase 2: Agent Migration (Priority: Critical)

#### 2.1 Create CrewAI Agent Wrapper
**New File: `crewai_agent.py`**

```python
from crewai import Agent, LLM

class ChatModeAgent:
    """
    Wrapper that creates CrewAI Agents from ChatMode profiles.
    Preserves backward compatibility with existing JSON format.
    """
    
    @classmethod
    def from_profile(cls, profile_path: str, settings: Settings) -> Agent:
        """Load profile JSON and create CrewAI Agent"""
        pass
```

**Mapping: Old Profile → CrewAI Agent**

| Old Profile Field | CrewAI Agent Attribute |
|-------------------|------------------------|
| `name` | `role` (display name) |
| `conversing` | `backstory` |
| `model` | `llm` (LLM instance) |
| `api` / `url` | `llm.base_url` |
| `params` | LLM configuration |
| - | `goal` (new, derived) |

#### 2.2 Profile Format Extension

Extend existing profile format to support CrewAI features:

```json
{
  "name": "Lawyer",
  "model": "gpt-4o-mini",
  "api": "openai",
  "url": "https://api.openai.com/v1",
  "conversing": "You are a sharp-witted lawyer...",
  
  "crewai": {
    "role": "Legal Expert",
    "goal": "Provide compelling legal arguments and perspectives",
    "allow_delegation": false,
    "verbose": true,
    "memory": true
  }
}
```

---

### Phase 3: Crew Implementation (Priority: Critical)

#### 3.1 Create Debate Crew
**New File: `debate_crew.py`**

```python
from crewai import Crew, Task, Process

class DebateCrew:
    """
    Orchestrates multi-agent debates using CrewAI.
    Replaces the custom conversation loop in main.py.
    """
    
    def __init__(self, agents: List[Agent], settings: Settings):
        self.crew = Crew(
            agents=agents,
            tasks=self._create_debate_tasks(),
            process=Process.sequential,
            memory=True,
            verbose=settings.verbose
        )
    
    def _create_debate_tasks(self) -> List[Task]:
        """Create debate response tasks for each agent"""
        pass
    
    def run_round(self, topic: str, history: List[dict]) -> List[dict]:
        """Execute one round of debate"""
        pass
```

#### 3.2 Task Definition Strategy

**Option A: Single Response Task per Agent**
```python
Task(
    description="Respond to the debate on {topic}. Previous: {history}",
    expected_output="A thoughtful response as {agent_name}",
    agent=agent
)
```

**Option B: Continuous Debate Task (Recommended)**
```python
Task(
    description="Engage in a philosophical debate about {topic}",
    expected_output="Series of responses maintaining character",
    agent=agent,
    async_execution=False
)
```

---

### Phase 4: Memory Migration (Priority: High)

#### 4.1 CrewAI Memory Configuration

```python
from crewai import Crew
from crewai.memory import ShortTermMemory, LongTermMemory, EntityMemory

crew = Crew(
    agents=[...],
    tasks=[...],
    memory=True,  # Enable all memory types
    
    # Optional: Custom memory configuration
    embedder={
        "provider": "openai",  # or "ollama"
        "config": {
            "model": "text-embedding-3-small"
        }
    }
)
```

#### 4.2 Memory Migration Path

| Current | CrewAI Equivalent |
|---------|-------------------|
| `MemoryStore.add()` | Auto-handled by Crew |
| `MemoryStore.query()` | Contextual memory retrieval |
| ChromaDB collections | CrewAI's ChromaDB + SQLite |
| Per-agent memory | Shared crew memory with agent tags |

#### 4.3 Data Migration (Optional)

Script to migrate existing ChromaDB data:
```python
# migrate_memory.py
# Exports old format → Imports to CrewAI memory
```

---

### Phase 5: Session & Web Admin Updates (Priority: High)

#### 5.1 Update Session Manager
**File: `session.py`**

```python
class ChatSession:
    def __init__(self, settings: Settings):
        self.debate_crew: Optional[DebateCrew] = None
        # ... rest of initialization
    
    def start(self, topic: str) -> bool:
        agents = self._load_crewai_agents()
        self.debate_crew = DebateCrew(agents, self.settings)
        # Start crew execution in background thread
        pass
```

#### 5.2 Update Web Admin Endpoints
**File: `web_admin.py`**

No significant changes needed - session interface remains the same.

---

### Phase 6: TTS Integration (Priority: Medium)

#### 6.1 Create TTS Tool for CrewAI

```python
from crewai.tools import tool

@tool("speak_response")
def speak_response(text: str, voice: str = "alloy") -> str:
    """
    Converts text to speech using TTS API.
    Returns path to generated audio file.
    """
    pass
```

#### 6.2 Agent with TTS Capability

```python
agent = Agent(
    role="Debater",
    goal="Engage in debate",
    backstory="...",
    tools=[speak_response]  # TTS as optional tool
)
```

---

### Phase 7: CLI & Entry Point Updates (Priority: Medium)

#### 7.1 Update main.py

```python
from debate_crew import DebateCrew
from crewai_agent import ChatModeAgent

def main():
    settings = load_settings()
    
    # Load agents using new CrewAI wrapper
    agents = [
        ChatModeAgent.from_profile(conf["file"], settings)
        for conf in config["agents"]
    ]
    
    # Create and run debate crew
    crew = DebateCrew(agents, settings)
    crew.run_continuous(topic)
```

---

## File Changes Summary

### New Files
| File | Purpose |
|------|---------|
| `crewai_agent.py` | CrewAI Agent wrapper for profiles |
| `debate_crew.py` | Crew orchestration for debates |
| `llm_config.py` | LLM configuration utilities |
| `tools/tts_tool.py` | TTS as CrewAI tool |
| `migrate_memory.py` | Memory migration script |

### Modified Files
| File | Changes |
|------|---------|
| `requirements.txt` | Add crewai, remove chromadb |
| `config.py` | Add CrewAI-specific settings |
| `session.py` | Use DebateCrew instead of ChatAgent |
| `main.py` | Update to use CrewAI components |
| `web_admin.py` | Minor updates for new session API |

### Deprecated/Removed Files
| File | Reason |
|------|--------|
| `agent.py` | Replaced by `crewai_agent.py` |
| `memory.py` | Replaced by CrewAI memory |
| `providers.py` | Replaced by CrewAI LLM |

### Preserved Files (No Changes)
| File | Reason |
|------|--------|
| `admin.py` | Still useful for topic generation |
| `tts.py` | Wrapped as CrewAI tool |
| `utils.py` | Utility functions still needed |
| `profiles/*.json` | Extended, not replaced |

---

## Implementation Order

```
Week 1: Foundation
├── Day 1-2: Update requirements.txt, create llm_config.py
├── Day 3-4: Create crewai_agent.py with profile loading
└── Day 5: Test agent creation from existing profiles

Week 2: Core Migration
├── Day 1-2: Create debate_crew.py
├── Day 3-4: Update session.py to use DebateCrew
└── Day 5: Test conversation loop with CrewAI

Week 3: Integration & Polish
├── Day 1-2: Update main.py, web_admin.py
├── Day 3: TTS tool integration
├── Day 4: Memory migration (if needed)
└── Day 5: End-to-end testing
```

---

## Risk Mitigation

### Risk 1: Breaking Changes in CrewAI
**Mitigation**: Pin specific crewai version, monitor releases

### Risk 2: Memory Data Loss
**Mitigation**: Backup existing ChromaDB before migration

### Risk 3: Performance Regression
**Mitigation**: Benchmark before/after, optimize as needed

### Risk 4: Profile Compatibility
**Mitigation**: Maintain backward compatibility, graceful fallbacks

---

## Testing Strategy

### Unit Tests
- Profile loading → CrewAI Agent
- LLM configuration
- Memory integration

### Integration Tests
- Full debate round with multiple agents
- Web admin session control
- TTS generation

### End-to-End Tests
- CLI debate simulation
- Web UI interaction
- Long-running sessions

---

## Rollback Plan

1. Keep original files as `*.backup`
2. Feature flag for CrewAI vs legacy mode
3. Environment variable: `USE_CREWAI=true|false`

---

## Success Criteria

1. ✅ All existing profiles work without modification
2. ✅ Web admin functions as before
3. ✅ Conversation quality maintained or improved
4. ✅ Memory persists across sessions
5. ✅ TTS works for all agents
6. ✅ No performance regression

---

## Next Steps

1. **Approve this masterplan**
2. **Begin Phase 1**: Update dependencies
3. **Create feature branch**: `feature/crewai-migration`
4. **Implement incrementally** with testing at each phase

