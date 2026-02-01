"""
CrewAI Agent Factory for ChatMode.

Creates CrewAI Agent instances from ChatMode profile JSON files,
maintaining backward compatibility with the existing profile format.
"""

import json
from typing import Dict, Any, Optional, List
from crewai import Agent, LLM

from chatmode.config import Settings
from chatmode.llm_config import create_llm_from_profile
from chatmode.utils import clean_placeholders


class ChatModeAgent:
    """
    Factory class for creating CrewAI Agents from ChatMode profiles.

    Preserves backward compatibility with existing JSON profile format
    while enabling full CrewAI capabilities.
    """

    @classmethod
    def from_profile(
        cls, profile_path: str, settings: Settings, tools: Optional[List[Any]] = None
    ) -> Agent:
        """
        Create a CrewAI Agent from a ChatMode profile JSON file.

        Args:
            profile_path: Path to the profile JSON file
            settings: Global application settings
            tools: Optional list of tools for the agent

        Returns:
            Configured CrewAI Agent instance
        """
        with open(profile_path, "r") as f:
            profile = json.load(f)

        return cls.from_dict(profile, settings, tools)

    @classmethod
    def from_dict(
        cls,
        profile: Dict[str, Any],
        settings: Settings,
        tools: Optional[List[Any]] = None,
    ) -> Agent:
        """
        Create a CrewAI Agent from a profile dictionary.

        Args:
            profile: Profile dictionary (from JSON)
            settings: Global application settings
            tools: Optional list of tools for the agent

        Returns:
            Configured CrewAI Agent instance
        """
        # Extract basic profile info
        name = profile.get("name", "Agent")
        conversing = profile.get("conversing", "")

        # Clean Minecraft-related placeholders from old profiles
        backstory = clean_placeholders(conversing)

        # Add debate context to backstory
        backstory += (
            "\nYou are in a meeting room engaging in a philosophical debate. "
            "Express your views clearly and engage with others' arguments."
        )

        # Extract CrewAI-specific config if present
        crewai_config = profile.get("crewai", {})

        # Determine role and goal
        role = crewai_config.get("role", name)
        goal = crewai_config.get(
            "goal", cls._derive_goal_from_backstory(name, backstory)
        )

        # Create LLM from profile
        llm = create_llm_from_profile(profile, settings)

        # Create and return Agent
        return Agent(
            role=role,
            goal=goal,
            backstory=backstory,
            llm=llm,
            tools=tools or [],
            verbose=crewai_config.get(
                "verbose", settings.verbose if hasattr(settings, "verbose") else False
            ),
            allow_delegation=crewai_config.get("allow_delegation", False),
            memory=crewai_config.get("memory", False),
            max_iter=crewai_config.get("max_iter", 1),
            max_rpm=crewai_config.get("max_rpm"),
            respect_context_window=False,
        )

    @staticmethod
    def _derive_goal_from_backstory(name: str, backstory: str) -> str:
        """
        Derive a reasonable goal from the agent's name and backstory.

        Args:
            name: Agent's display name
            backstory: Agent's backstory/persona

        Returns:
            A derived goal string
        """
        # Default goal based on agent's name/role
        return (
            f"Engage thoughtfully in debates as {name}, "
            f"presenting compelling arguments and perspectives based on your unique viewpoint."
        )

    @classmethod
    def get_profile_metadata(cls, profile_path: str) -> Dict[str, Any]:
        """
        Extract metadata from a profile without creating an agent.

        Useful for displaying profile info in UI.

        Args:
            profile_path: Path to the profile JSON file

        Returns:
            Dictionary with profile metadata
        """
        with open(profile_path, "r") as f:
            profile = json.load(f)

        return {
            "name": profile.get("name", "Unknown"),
            "model": profile.get("model", "default"),
            "api": profile.get("api", "openai"),
            "has_tts": "speak_model" in profile,
            "tts_voice": profile.get("speak_model", {}).get("voice"),
        }


def load_agents_from_config(
    config_path: str, settings: Settings, tools: Optional[List[Any]] = None
) -> List[Agent]:
    """
    Load all agents from the agent configuration file.

    Args:
        config_path: Path to agent_config.json
        settings: Global application settings
        tools: Optional list of tools shared by all agents

    Returns:
        List of CrewAI Agent instances
    """
    with open(config_path, "r") as f:
        config = json.load(f)

    agents = []
    for agent_conf in config.get("agents", []):
        try:
            agent = ChatModeAgent.from_profile(
                profile_path=agent_conf["file"], settings=settings, tools=tools
            )
            agents.append(agent)
            print(f"✓ Loaded agent: {agent.role}")
        except Exception as e:
            print(f"✗ Failed to load agent {agent_conf.get('name', 'unknown')}: {e}")

    return agents
