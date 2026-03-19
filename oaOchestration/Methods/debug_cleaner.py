# setup/debug_cleaner.py
#
# This module provides a function to clear the debug directory of log files.
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

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True    # Set to False in production, True for dev on this file
from oaLogging.Core.logger import initialize_logging, set_log_directory
from loguru import logger

from oaConfiguration.FileReaders.config_reader import Config

app_constants = Config.get_instance()  # Get the singleton instance


# Clears all files within the debug log directory.
# This function is used to remove old log files and ensure a clean slate for debugging
# purposes. It attempts to delete all files in the specified debug directory.
# Inputs:
#     data_dir (str): The base data directory where the 'debug' subdirectory is located.
# Outputs:
def clear_debug_directory():
    """Clears all files within the refactored log directory."""
    from ..Core.path_initializer import DATA_LOGS_DIR
    if LOCAL_DEBUG: logger.debug("▶️ Entering clear_debug_directory.")

    if DATA_LOGS_DIR.exists():
        if LOCAL_DEBUG: logger.debug(f"🔍 Log directory found: {DATA_LOGS_DIR}. Proceeding to clear contents.")
        try:
            for item in DATA_LOGS_DIR.iterdir():
                try:
                    if item.is_file():
                        item.unlink()
                        if LOCAL_DEBUG: logger.success(f"🗑️ Successfully deleted: {item}")
                except Exception as e:
                    if LOCAL_DEBUG: logger.error(f"❌ Failed to delete {item}: {e}")
            if LOCAL_DEBUG: logger.debug("🧹 Finished clearing log directory.")
        except Exception as e:
            if LOCAL_DEBUG: logger.error(f"❌ Error clearing log directory: {e}")
    else:
        if LOCAL_DEBUG: logger.debug(f"⏩ Log directory not found: {DATA_LOGS_DIR}. Skipping clear.")

