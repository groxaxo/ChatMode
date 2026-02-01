"""
State synchronization utilities for agent runtime configuration.

Keeps database-configured agents aligned with profile JSON files and
agent_config.json used by the runtime session loader.
"""

import json
import os
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from .models import Agent


def get_project_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load_profile(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def _write_profile(path: str, data: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=4)


def sync_profiles_from_db(
    db: Session,
    include_disabled: bool = False,
) -> Dict[str, Any]:
    """Sync agent profiles and agent_config.json from database records."""
    project_root = get_project_root()
    profiles_dir = os.path.join(project_root, "profiles")
    os.makedirs(profiles_dir, exist_ok=True)

    query = db.query(Agent)
    if not include_disabled:
        query = query.filter(Agent.enabled == True)
    agents: List[Agent] = query.all()

    synced_agents: List[Dict[str, str]] = []

    for agent in agents:
        profile_path = os.path.join(profiles_dir, f"{agent.name}.json")
        existing = _load_profile(profile_path)

        profile: Dict[str, Any] = dict(existing)
        profile["name"] = agent.display_name or existing.get("name") or agent.name
        profile["model"] = agent.model
        profile["api"] = agent.provider
        if agent.api_url:
            profile["url"] = agent.api_url

        if agent.system_prompt:
            profile["conversing"] = agent.system_prompt
        elif "conversing" not in profile:
            profile["conversing"] = ""

        profile["temperature"] = agent.temperature
        profile["max_output_tokens"] = agent.max_tokens
        profile["top_p"] = agent.top_p
        profile["sleep_seconds"] = agent.sleep_seconds

        if agent.memory_settings and agent.memory_settings.top_k:
            profile["memory_top_k"] = agent.memory_settings.top_k

        if agent.permissions and agent.permissions.tool_permissions is not None:
            profile["allowed_tools"] = agent.permissions.tool_permissions

        _write_profile(profile_path, profile)
        synced_agents.append(
            {
                "name": agent.name,
                "file": profile_path,
            }
        )

    config_path = os.path.join(project_root, "agent_config.json")
    with open(config_path, "w") as f:
        json.dump({"agents": synced_agents}, f, indent=2)

    return {
        "agents_synced": len(synced_agents),
        "agent_config_path": config_path,
        "profiles_dir": profiles_dir,
    }
