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

import workers.setup.worker_project_paths as app_constants
from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args

current_version = "20251230.230000.1"
current_version_hash = 20251230 * 230000 * 1


# Loads the application state cache from `device_state_snapshot.json` on disk.
# This function attempts to read a JSON file containing the cached device state.
# If the file exists and is readable, its contents are returned as a dictionary;
# otherwise, an empty dictionary is returned, and any errors are logged.
# Inputs:
#     None.
# Outputs:
#     Dict[str, Any]: A dictionary representing the loaded cache data, or an empty dictionary on failure.
def load_cache() -> Dict[str, Any]:
    """
    Reads device_state_snapshot.json from the DATA directory defined in app_constants.
    Returns an empty dict on failure/missing file.
    """
    debug_logger(message="📖  We're attempting to read the Almanac!", **_get_log_args())
    try:
        if app_constants.DEVICE_STATE_SNAPSHOT_PATH.exists():
            debug_logger(
                message="⏳ The Almanac exists! Reading the timeline...",
                **_get_log_args(),
            )
            with open(app_constants.DEVICE_STATE_SNAPSHOT_PATH, "rb") as f:
                data = orjson.loads(f.read())
                debug_logger(
                    message="✅  The timeline has been successfully loaded from the Almanac!",
                    **_get_log_args(),
                )
                return data
        else:
            debug_logger(
                message="📄 The Almanac is blank! No cache file found.",
                **_get_log_args(),
            )
    except Exception as e:
        debug_logger(
            message=f"🆘  The Almanac is unreadable! Could not read the cache file: {e}",
            **_get_log_args(),
        )
    return {}


# Atomically saves the application state cache to `device_state_snapshot.json` on disk.
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
    to prevent corruption during a power loss.
    """
    debug_logger(message="✍️  We're about to write to the Almanac!", **_get_log_args())
    try:
        temp_dir = app_constants.DEVICE_STATE_SNAPSHOT_PATH.parent
        debug_logger(
            message=f"👯 Creating a temporal duplicate in {temp_dir}...",
            **_get_log_args(),
        )
        with tempfile.NamedTemporaryFile(
            mode="wb", dir=temp_dir, delete=False, suffix=".tmp"
        ) as temp_f:
            temp_f.write(orjson.dumps(data))
            temp_path = temp_f.name
        debug_logger(
            message=f"↔️ Temporal duplicate created at {temp_path}. Now, for the switch!",
            **_get_log_args(),
        )

        os.rename(temp_path, app_constants.DEVICE_STATE_SNAPSHOT_PATH)
        debug_logger(
            message="💾  The timeline has been successfully recorded in the Almanac!",
            **_get_log_args(),
        )
        return True
    except Exception as e:
        debug_logger(
            message=f"💥  We've created a paradox! Failed to save the cache: {e}",
            **_get_log_args(),
        )
        if "temp_path" in locals() and os.path.exists(temp_path):
            os.remove(temp_path)
            debug_logger(
                message="🔥 Paradox contained. Temporal duplicate destroyed.",
                **_get_log_args(),
            )
        return False