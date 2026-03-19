# State_Cache/cache_io_handler.py
#
# Handles all disk I/O operations for the application's state cache, including loading and atomic saving of snapshots.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Professional services for customizing and tailoring this software to your specific
# application can be negotiated. There is no charge to use, modify, or fork this software.
#
# Build Log: https://like.audio/category/software/spectrum-scanner/
# Source Code: https://github.com/APKaudio/
# Feature Requests can be emailed to i @ like . audio
#
# Version 20250821.200641.1

import os
import orjson
import pathlib
import tempfile
import inspect
from typing import Dict, Any

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True    # Set to False in production, True for dev on this file
from oaLogging.Core.logger import initialize_logging, set_log_directory
from loguru import logger

from oaConfiguration.FileReaders.config_reader import Config

app_config = Config.get_instance()

import oaOchestration.Constants.project_paths as app_constants

current_version = "20251230.230000.1"
current_version_hash = 20251230 * 230000 * 1


# Loads the application state cache from `device_state_cache.json` on disk.
# This function attempts to read a JSON file containing the cached device state.
# If the file exists and is readable, its contents are returned as a dictionary;
# otherwise, an empty dictionary is returned, and any errors are logged.
# Inputs:
#     None.
# Outputs:
#     Dict[str, Any]: A dictionary representing the loaded cache data, or an empty dictionary on failure.
class CacheLoadError(Exception):
    """Raised when the cache file exists but cannot be parsed."""
    pass

def load_cache() -> Dict[str, Any]:
    """
    Reads device_state_cache.json from the DATA directory defined in app_constants.
    Raises FileNotFoundError if the file doesn't exist, and CacheLoadError if it's corrupted.
    """
    if LOCAL_DEBUG and app_config.global_settings["debug_enabled"]:
        if LOCAL_DEBUG: logger.debug("💾📖 Reading Cache.")
        
    if not app_constants.DEVICE_STATE_CACHE_PATH.exists():
        if LOCAL_DEBUG and app_config.global_settings["debug_enabled"]:
            if LOCAL_DEBUG: logger.debug("💾📄 No cache file found.")
        raise FileNotFoundError(f"Cache file missing: {app_constants.DEVICE_STATE_CACHE_PATH}")

    try:
        if LOCAL_DEBUG and app_config.global_settings["debug_enabled"]:
            if LOCAL_DEBUG: logger.debug("💾⏳ Cache file exists. Reading...")
        with open(app_constants.DEVICE_STATE_CACHE_PATH, "rb") as f:
            data = orjson.loads(f.read())
            if LOCAL_DEBUG and app_config.global_settings["debug_enabled"]:
                if LOCAL_DEBUG: logger.success("💾✅ Cache loaded successfully.")
            return data
    except Exception as e:
        from ..Core.cache_recovery_handler import recover_corrupted_cache
        return recover_corrupted_cache(app_constants.DEVICE_STATE_CACHE_PATH, e)


# Atomically saves the application state cache to `device_state_cache.json` on disk.
# This function writes the provided dictionary to a temporary file and then
# renames it to the target filename. This atomic operation prevents data corruption
# in case of unexpected interruptions (e.g., power loss).
# Inputs:
#     data (Dict[str, Any]): The dictionary containing the state cache data to be saved.
# Outputs:
#     bool: True if the cache was saved successfully, False otherwise.
def save_cache(data: Dict[str, Any]) -> bool:
    """
    Writes the dictionary to disk. Use a temp file + rename (atomic write)
    """
    try:
        temp_dir = app_constants.DEVICE_STATE_CACHE_PATH.parent
        # Ensure the DATA directory exists
        if not temp_dir.exists():
            temp_dir.mkdir(parents=True, exist_ok=True)
            if LOCAL_DEBUG and app_config.global_settings["debug_enabled"]:
                if LOCAL_DEBUG: logger.debug(f"📁 Created missing directory: {temp_dir}")

        with tempfile.NamedTemporaryFile(
            mode="wb", dir=temp_dir, delete=False, suffix=".tmp"
        ) as temp_f:
            # Safely handle any stray bytes objects by decoding them
            json_data = orjson.dumps(
                data, 
                default=lambda x: x.decode("utf-8") if isinstance(x, bytes) else str(x)
            )
            temp_f.write(json_data)
            temp_path = temp_f.name

        os.rename(temp_path, app_constants.DEVICE_STATE_CACHE_PATH)
        # if LOCAL_DEBUG and app_config.global_settings["debug_enabled"]:
        #     logger.success("💾✅ Cache saved.")
        return True
    except Exception as e:
        if LOCAL_DEBUG and app_config.global_settings["debug_enabled"]:
            logger.exception("💾❌ Error saving cache")
        if "temp_path" in locals() and os.path.exists(temp_path):
            os.remove(temp_path)
        return False