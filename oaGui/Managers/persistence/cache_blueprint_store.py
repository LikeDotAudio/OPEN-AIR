# oaGui/Managers/cache_blueprint_store.py
# Author: Anthony Peter Kuzub
# Version: 20260501.1000.1
#
# Description: Manages caching for GUI default configurations.

import copy
from typing import Dict, Optional

class CacheBlueprintStore:
    """
    Manages caching for GUI default configurations.
    """
    _DEFAULT_CONFIG_CACHE: Optional[Dict] = None

    @classmethod
    def get_cached_default(cls) -> Optional[Dict]:
        """Retrieves the cached default configuration if available."""
        if cls._DEFAULT_CONFIG_CACHE is not None:
            return copy.deepcopy(cls._DEFAULT_CONFIG_CACHE)
        return None

    @classmethod
    def set_cached_default(cls, config: Dict):
        """Sets the cached default configuration."""
        cls._DEFAULT_CONFIG_CACHE = config

    @classmethod
    def invalidate(cls):
        """Clears the cached default configuration."""
        cls._DEFAULT_CONFIG_CACHE = None
