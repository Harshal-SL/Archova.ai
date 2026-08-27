"""Centralized Configuration Package for AI Engine.

Re-exports settings and model configuration singletons and handles backward compatibility module aliases.
"""

import sys

from app.config import model_config
from app.config.app_config import settings, reload_settings, print_startup_env_diagnostics
from app.config.model_config import (
    MODEL_CONFIG,
    MODEL_MAP,
    get_model_for_capability,
    validate_model_config,
)

# Register module aliases for backward compatibility
sys.modules["config"] = sys.modules[__name__]
sys.modules["config.model_config"] = model_config

__all__ = [
    "settings",
    "reload_settings",
    "print_startup_env_diagnostics",
    "MODEL_CONFIG",
    "MODEL_MAP",
    "get_model_for_capability",
    "validate_model_config",
]
