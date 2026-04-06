from oaLogging.Methods.matrix_gate import matrix_log
# FileReaders/cache_io_handler.py
# Author: Anthony Peter Kuzub
# Version: 20250821.200641.1
#
# Description: State_Cache/cache_io_handler.py

import os
import orjson
import pathlib
import tempfile
import inspect
from typing import Dict, Any

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = False
from oaLogging.Core.logger import initialize_logging, set_log_directory
from loguru import logger

from oaConfigurationManager.FileReaders.config_reader import Config

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
        matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "💾📖 Reading Cache.", "DEBUG")
        
    if not app_constants.DEVICE_STATE_CACHE_PATH.exists():
        if LOCAL_DEBUG and app_config.global_settings["debug_enabled"]:
            matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "💾📄 No cache file found.", "DEBUG")
        raise FileNotFoundError(f"Cache file missing: {app_constants.DEVICE_STATE_CACHE_PATH}")

    try:
        if LOCAL_DEBUG and app_config.global_settings["debug_enabled"]:
            matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "💾⏳ Cache file exists. Reading...", "DEBUG")
        with open(app_constants.DEVICE_STATE_CACHE_PATH, "rb") as f:
            data = orjson.loads(f.read())
            if LOCAL_DEBUG and app_config.global_settings["debug_enabled"]:
                matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "💾✅ Cache loaded successfully.", "SUCCESS")
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
def save_cache(data: Any) -> bool:
    """
    Writes the dictionary to disk. Use a temp file + rename (atomic write)
    """
    try:
        # If it's the Rust core, we need to convert to dict first
        if hasattr(data, "to_dict"):
            data = data.to_dict()

        temp_dir = app_constants.DEVICE_STATE_CACHE_PATH.parent
        # Ensure the DATA directory exists
        if not temp_dir.exists():
            temp_dir.mkdir(parents=True, exist_ok=True)
            if LOCAL_DEBUG and app_config.global_settings["debug_enabled"]:
                matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"📁 Created missing directory: {temp_dir}", "DEBUG")

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
        #     logger.success("💾✅ Cache saved.")
        return True
    except Exception as e:
        if LOCAL_DEBUG and app_config.global_settings["debug_enabled"]:
            logger.exception("💾❌ Error saving cache")
        if "temp_path" in locals() and os.path.exists(temp_path):
            os.remove(temp_path)
        return False
