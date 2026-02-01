"""
Provider Initialization Utility.

Automatically discovers and configures providers from environment variables
and shell configuration files (.bashrc, .zshrc) on application startup.
"""

import asyncio
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from ..models import Provider
from ..services.provider_sync import (
    create_provider_from_config,
    detect_provider_type,
    sync_provider_models,
)

# Default provider configurations from environment
DEFAULT_PROVIDERS = {
    "ollama": {
        "env_url": "OLLAMA_BASE_URL",
        "default_url": "http://localhost:11434",
        "env_key": None,
        "provider_type": "ollama",
    },
    "openai": {
        "env_url": "OPENAI_BASE_URL",
        "default_url": "https://api.openai.com/v1",
        "env_key": "OPENAI_API_KEY",
        "provider_type": "openai",
    },
    "fireworks": {
        "env_url": None,
        "default_url": "https://api.fireworks.ai/inference/v1",
        "env_key": "FIREWORKS_API_KEY",
        "provider_type": "fireworks",
    },
    "deepseek": {
        "env_url": None,
        "default_url": "https://api.deepseek.com/v1",
        "env_key": "DEEPSEEK_API_KEY",
        "provider_type": "deepseek",
    },
    "xai": {
        "env_url": None,
        "default_url": "https://api.x.ai/v1",
        "env_key": "XAI_API_KEY",
        "provider_type": "xai",
    },
    "anthropic": {
        "env_url": None,
        "default_url": "https://api.anthropic.com/v1",
        "env_key": "ANTHROPIC_API_KEY",
        "provider_type": "anthropic",
    },
    "lmstudio": {
        "env_url": "LMSTUDIO_BASE_URL",
        "default_url": "http://localhost:1234/v1",
        "env_key": None,
        "provider_type": "lmstudio",
    },
    "vllm": {
        "env_url": "VLLM_BASE_URL",
        "default_url": "http://localhost:8000/v1",
        "env_key": None,
        "provider_type": "vllm",
    },
}


def discover_providers_from_env() -> List[Dict]:
    """
    Discover provider configurations from environment variables.

    Returns:
        List of provider configuration dictionaries
    """
    providers = []

    for provider_name, config in DEFAULT_PROVIDERS.items():
        # Check if we have a URL or API key for this provider
        base_url = None
        api_key = None

        # Get base URL from environment or use default
        if config["env_url"]:
            base_url = os.getenv(config["env_url"], config["default_url"])
        else:
            # For providers that only need API key, use default URL
            base_url = config["default_url"]

        # Get API key if required
        if config["env_key"]:
            api_key = os.getenv(config["env_key"])

        # Only add provider if we have credentials or it's a local provider
        is_local = provider_name in ["ollama", "lmstudio", "vllm"]
        has_credentials = api_key is not None or is_local

        if has_credentials and base_url:
            providers.append(
                {
                    "name": provider_name,
                    "base_url": base_url,
                    "api_key": api_key,
                    "provider_type": config["provider_type"],
                    "auto_sync": True,
                }
            )

    # Check for custom provider configurations
    custom_providers = discover_custom_providers()
    providers.extend(custom_providers)

    return providers


def discover_custom_providers() -> List[Dict]:
    """
    Discover custom provider configurations from environment.

    Supports:
    - PROVIDER_<NAME>_URL and PROVIDER_<NAME>_KEY format
    - PROVIDER_<NAME>_CONFIG for full JSON config

    Returns:
        List of custom provider configurations
    """
    providers = []

    # Look for PROVIDER_*_URL variables
    for key in os.environ:
        if key.startswith("PROVIDER_") and key.endswith("_URL"):
            provider_name = key[9:-4].lower()  # Extract name from PROVIDER_<NAME>_URL
            base_url = os.getenv(key)
            api_key = os.getenv(f"PROVIDER_{provider_name.upper()}_KEY")

            if base_url:
                providers.append(
                    {
                        "name": provider_name,
                        "base_url": base_url,
                        "api_key": api_key,
                        "provider_type": detect_provider_type(base_url),
                        "auto_sync": True,
                    }
                )

    return providers


async def initialize_providers(db: Session, auto_sync: bool = True) -> List[Dict]:
    """
    Initialize providers from environment variables.

    Args:
        db: Database session
        auto_sync: Whether to automatically sync models after creation

    Returns:
        List of initialization results
    """
    discovered = discover_providers_from_env()
    results = []

    for config in discovered:
        try:
            # Check if provider already exists
            existing = (
                db.query(Provider).filter(Provider.name == config["name"]).first()
            )

            if existing:
                # Update existing provider
                existing.base_url = config["base_url"]
                if config["api_key"]:
                    existing.api_key_encrypted = config["api_key"]
                existing.auto_sync_enabled = config["auto_sync"]
                db.commit()

                result = {
                    "name": config["name"],
                    "action": "updated",
                    "provider_id": existing.id,
                }

                # Sync models if enabled
                if auto_sync and config["auto_sync"]:
                    sync_result = await sync_provider_models(db, existing)
                    result["sync"] = sync_result

                results.append(result)
            else:
                # Create new provider
                provider = create_provider_from_config(
                    db=db,
                    name=config["name"],
                    base_url=config["base_url"],
                    api_key=config["api_key"],
                    provider_type=config["provider_type"],
                    auto_sync=config["auto_sync"],
                )

                result = {
                    "name": config["name"],
                    "action": "created",
                    "provider_id": provider.id,
                }

                # Sync models if enabled
                if auto_sync and config["auto_sync"]:
                    sync_result = await sync_provider_models(db, provider)
                    result["sync"] = sync_result

                results.append(result)

        except Exception as e:
            results.append(
                {
                    "name": config["name"],
                    "action": "error",
                    "error": str(e),
                }
            )

    return results


def get_provider_status(db: Session) -> List[Dict]:
    """
    Get status of all configured providers.

    Args:
        db: Database session

    Returns:
        List of provider status dictionaries
    """
    providers = db.query(Provider).all()

    return [
        {
            "id": p.id,
            "name": p.name,
            "display_name": p.display_name,
            "provider_type": p.provider_type,
            "base_url": p.base_url,
            "enabled": p.enabled,
            "is_default": p.is_default,
            "auto_sync_enabled": p.auto_sync_enabled,
            "sync_status": p.sync_status,
            "last_sync_at": p.last_sync_at.isoformat() if p.last_sync_at else None,
            "sync_error": p.sync_error,
        }
        for p in providers
    ]


def parse_shell_config_file(filepath: str) -> Dict[str, str]:
    """
    Parse a shell configuration file (e.g., .bashrc, .zshrc) for environment variables.

    Args:
        filepath: Path to the shell config file

    Returns:
        Dictionary of environment variable names and values
    """
    env_vars = {}

    if not os.path.exists(filepath):
        return env_vars

    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        # Match export VAR=value or export VAR="value" patterns
        # Also match VAR=value (without export) for common patterns
        patterns = [
            r'^export\s+([A-Z_][A-Z0-9_]*)\s*=\s*["\']?([^"\'\n;]+)["\']?',
            r'^([A-Z_][A-Z0-9_]*)\s*=\s*["\']?([^"\'\n;]+)["\']?',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            for var_name, var_value in matches:
                # Only capture API keys and provider-related variables
                if any(
                    keyword in var_name
                    for keyword in [
                        "API_KEY",
                        "BASE_URL",
                        "OLLAMA",
                        "OPENAI",
                        "FIREWORKS",
                        "DEEPSEEK",
                        "XAI",
                        "ANTHROPIC",
                        "LMSTUDIO",
                        "VLLM",
                        "PROVIDER",
                    ]
                ):
                    env_vars[var_name] = var_value.strip()

    except Exception as e:
        print(f"Warning: Could not parse {filepath}: {e}")

    return env_vars


def discover_providers_from_shell_configs() -> Tuple[List[Dict], List[str]]:
    """
    Discover provider configurations from shell config files (.bashrc, .zshrc, etc.).

    Returns:
        Tuple of (providers list, list of files that were scanned)
    """
    providers = []
    scanned_files = []

    # Common shell config file locations
    home = Path.home()
    config_files = [
        home / ".bashrc",
        home / ".zshrc",
        home / ".bash_profile",
        home / ".zprofile",
        home / ".profile",
        home / ".config" / "fish" / "config.fish",
    ]

    # Collect all environment variables from shell configs
    all_env_vars = {}

    for config_file in config_files:
        if config_file.exists():
            env_vars = parse_shell_config_file(str(config_file))
            if env_vars:
                all_env_vars.update(env_vars)
                scanned_files.append(str(config_file))

    # Now check for providers using the collected env vars
    for provider_name, config in DEFAULT_PROVIDERS.items():
        base_url = None
        api_key = None

        # Get base URL from shell config or use default
        if config["env_url"]:
            base_url = all_env_vars.get(config["env_url"], config["default_url"])
        else:
            base_url = config["default_url"]

        # Get API key if required
        if config["env_key"]:
            api_key = all_env_vars.get(config["env_key"])

        # Only add provider if we have credentials or it's a local provider
        is_local = provider_name in ["ollama", "lmstudio", "vllm"]
        has_credentials = api_key is not None or is_local

        if has_credentials and base_url:
            providers.append(
                {
                    "name": provider_name,
                    "base_url": base_url,
                    "api_key": api_key,
                    "provider_type": config["provider_type"],
                    "auto_sync": True,
                    "source": "shell_config",  # Mark the source
                }
            )

    # Check for custom provider configurations in shell configs
    for key, value in all_env_vars.items():
        if key.startswith("PROVIDER_") and key.endswith("_URL"):
            provider_name = key[9:-4].lower()
            api_key_var = f"PROVIDER_{provider_name.upper()}_KEY"
            api_key = all_env_vars.get(api_key_var)

            providers.append(
                {
                    "name": provider_name,
                    "base_url": value,
                    "api_key": api_key,
                    "provider_type": detect_provider_type(value),
                    "auto_sync": True,
                    "source": "shell_config",
                }
            )

    return providers, scanned_files


def merge_provider_sources(
    env_providers: List[Dict], shell_providers: List[Dict]
) -> List[Dict]:
    """
    Merge providers from environment and shell configs.
    Environment variables take precedence over shell configs.

    Args:
        env_providers: Providers discovered from environment
        shell_providers: Providers discovered from shell configs

    Returns:
        Merged list of providers
    """
    # Create a dict keyed by provider name for easy lookup
    merged = {p["name"]: p for p in env_providers}

    # Add shell providers only if not already in env
    for provider in shell_providers:
        if provider["name"] not in merged:
            merged[provider["name"]] = provider

    return list(merged.values())


async def initialize_providers(
    db: Session, auto_sync: bool = True, scan_shell_configs: bool = False
) -> Dict:
    """
    Initialize providers from environment variables and optionally shell configs.

    Args:
        db: Database session
        auto_sync: Whether to automatically sync models after creation
        scan_shell_configs: Whether to scan .bashrc, .zshrc, etc. for API keys

    Returns:
        Dictionary with initialization results and metadata
    """
    results = {
        "providers": [],
        "scanned_files": [],
        "total_discovered": 0,
        "successful": 0,
        "failed": 0,
    }

    # Discover from environment variables
    env_providers = discover_providers_from_env()

    # Discover from shell configs if requested
    shell_providers = []
    if scan_shell_configs:
        shell_providers, scanned_files = discover_providers_from_shell_configs()
        results["scanned_files"] = scanned_files

    # Merge sources (env takes precedence)
    all_providers = merge_provider_sources(env_providers, shell_providers)
    results["total_discovered"] = len(all_providers)

    # Initialize each provider
    for config in all_providers:
        try:
            # Check if provider already exists
            existing = (
                db.query(Provider).filter(Provider.name == config["name"]).first()
            )

            if existing:
                # Update existing provider
                existing.base_url = config["base_url"]
                if config["api_key"]:
                    existing.api_key_encrypted = config["api_key"]
                existing.auto_sync_enabled = config["auto_sync"]
                db.commit()

                result = {
                    "name": config["name"],
                    "action": "updated",
                    "provider_id": existing.id,
                    "source": config.get("source", "environment"),
                }

                # Sync models if enabled
                if auto_sync and config["auto_sync"]:
                    sync_result = await sync_provider_models(db, existing)
                    result["sync"] = sync_result
                    if sync_result.get("success"):
                        results["successful"] += 1
                    else:
                        results["failed"] += 1

                results["providers"].append(result)
            else:
                # Create new provider
                provider = create_provider_from_config(
                    db=db,
                    name=config["name"],
                    base_url=config["base_url"],
                    api_key=config["api_key"],
                    provider_type=config["provider_type"],
                    auto_sync=config["auto_sync"],
                )

                result = {
                    "name": config["name"],
                    "action": "created",
                    "provider_id": provider.id,
                    "source": config.get("source", "environment"),
                }

                # Sync models if enabled
                if auto_sync and config["auto_sync"]:
                    sync_result = await sync_provider_models(db, provider)
                    result["sync"] = sync_result
                    if sync_result.get("success"):
                        results["successful"] += 1
                    else:
                        results["failed"] += 1

                results["providers"].append(result)

        except Exception as e:
            results["failed"] += 1
            results["providers"].append(
                {
                    "name": config["name"],
                    "action": "error",
                    "error": str(e),
                    "source": config.get("source", "environment"),
                }
            )

    return results


# Keep the old function for backward compatibility
async def initialize_providers_legacy(
    db: Session, auto_sync: bool = True
) -> List[Dict]:
    """
    Legacy initialization function for backward compatibility.

    Args:
        db: Database session
        auto_sync: Whether to automatically sync models after creation

    Returns:
        List of initialization results
    """
    result = await initialize_providers(db, auto_sync, scan_shell_configs=False)
    return result["providers"]


async def test_provider_connection(
    base_url: str, api_key: Optional[str] = None, timeout: int = 10
) -> Dict:
    """
    Test connection to a provider.

    Args:
        base_url: Provider base URL
        api_key: Optional API key
        timeout: Connection timeout in seconds

    Returns:
        Dictionary with test results
    """
    try:
        from ..services.provider_sync import fetch_models_from_provider

        models = await fetch_models_from_provider(base_url, api_key)

        return {
            "success": True,
            "models_found": len(models),
            "provider_type": detect_provider_type(base_url),
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }
