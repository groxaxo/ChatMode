"""
ChatMode Services Package.

This module contains business logic services for the application.
"""

from .provider_sync import (
    sync_provider_models,
    sync_all_providers,
    create_provider_from_config,
    detect_provider_type,
    get_all_available_models,
    fetch_models_from_provider,
    get_provider_display_name,
    PROVIDER_DISPLAY_NAMES,
    PROVIDER_PATTERNS,
)

from .provider_init import (
    initialize_providers,
    initialize_providers_legacy,
    discover_providers_from_env,
    discover_providers_from_shell_configs,
    parse_shell_config_file,
    merge_provider_sources,
    get_provider_status,
    test_provider_connection,
    DEFAULT_PROVIDERS,
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
