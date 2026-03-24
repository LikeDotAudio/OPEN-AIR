# Core/layout_cache.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import pathlib
import orjson
from loguru import logger

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = False    # Set to False in production, True for dev on this file

class LayoutCacheManager:
    """
    Manages loading and saving the layout cache to disk.
    Handles path serialization and restoration.
    """

    def __init__(self, cache_file: pathlib.Path):
        self._cache_file = cache_file

    def load(self):
        """Loads the layout cache from disk."""
        if self._cache_file.exists():
            try:
                with open(self._cache_file, "rb") as f:
                    data = orjson.loads(f.read())
                return self._restore_cache_paths(data)
            except Exception as e:
                if LOCAL_DEBUG:
                    logger.exception("⚠️ Failed to load layout cache")
        return {}

    def save(self, layout_cache):
        """Saves the layout cache to disk."""
        try:
            self._cache_file.parent.mkdir(parents=True, exist_ok=True)
            serializable_cache = self._make_cache_serializable(layout_cache)
            with open(self._cache_file, "wb") as f:
                f.write(orjson.dumps(serializable_cache))
        except Exception as e:
             if LOCAL_DEBUG:
                 logger.exception("⚠️ Failed to save layout cache")

    def _make_cache_serializable(self, data):
        """Recursively converts Path objects to strings for JSON serialization."""
        if isinstance(data, dict):
            return {k: self._make_cache_serializable(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._make_cache_serializable(v) for v in data]
        elif isinstance(data, pathlib.Path):
            return str(data)
        return data

    def _restore_cache_paths(self, data):
        """Recursively restores Path objects from strings."""
        if isinstance(data, dict):
            new_dict = {}
            for k, v in data.items():
                if k in ["path", "build_path"] and isinstance(v, str):
                    new_dict[k] = pathlib.Path(v)
                elif k in ["gui_files", "child_containers"] and isinstance(v, list):
                    new_dict[k] = [pathlib.Path(item) if isinstance(item, str) else item for item in v]
                elif k in ["panels", "tabs"] and isinstance(v, list):
                    new_dict[k] = [self._restore_cache_paths(item) for item in v]
                else:
                    new_dict[k] = self._restore_cache_paths(v)
            return new_dict
        elif isinstance(data, list):
            return [self._restore_cache_paths(v) for v in data]
        return data
