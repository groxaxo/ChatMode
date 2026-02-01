"""
ChatMode Services Package.

This module contains business logic services for the application.
"""

from .provider_init import (
    DEFAULT_PROVIDERS,
    discover_providers_from_env,
    discover_providers_from_shell_configs,
    get_provider_status,
    initialize_providers,
    initialize_providers_legacy,
    merge_provider_sources,
    parse_shell_config_file,
    test_provider_connection,
)
from .provider_sync import (
    PROVIDER_DISPLAY_NAMES,
    PROVIDER_PATTERNS,
    create_provider_from_config,
    detect_provider_type,
    fetch_models_from_provider,
    get_all_available_models,
    get_provider_display_name,
    sync_all_providers,
    sync_provider_models,
)

__all__ = [
    "sync_provider_models",
    "sync_all_providers",
    "create_provider_from_config",
    "detect_provider_type",
    "get_all_available_models",
    "fetch_models_from_provider",
    "get_provider_display_name",
    "PROVIDER_DISPLAY_NAMES",
    "PROVIDER_PATTERNS",
    "initialize_providers",
    "initialize_providers_legacy",
    "discover_providers_from_env",
    "discover_providers_from_shell_configs",
    "parse_shell_config_file",
    "merge_provider_sources",
    "get_provider_status",
    "test_provider_connection",
    "DEFAULT_PROVIDERS",
]
