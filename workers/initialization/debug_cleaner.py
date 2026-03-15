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
from workers.logger.logger import initialize_logging, set_log_directory
from loguru import logger

from managers.configini.config_reader import Config

app_constants = Config.get_instance()  # Get the singleton instance


# Clears all files within the debug log directory.
# This function is used to remove old log files and ensure a clean slate for debugging
# purposes. It attempts to delete all files in the specified debug directory.
# Inputs:
#     data_dir (str): The base data directory where the 'debug' subdirectory is located.
# Outputs:
#     None.
def clear_debug_directory(data_dir):  # Removed _func argument
    if LOCAL_DEBUG: logger.debug("▶️ Entering clear_debug_directory.")
    # Clear debug directory
    debug_dir = os.path.join(data_dir, "debug")
    if os.path.exists(debug_dir):
        if LOCAL_DEBUG: logger.debug(f"🔍 Debug directory found: {debug_dir}. Proceeding to clear contents.")
        try:
            filenames = os.listdir(debug_dir)  # Get list of files before deletion
            if LOCAL_DEBUG: logger.debug(f"🔍 Found {len(filenames)} items in debug directory.")
            for filename in filenames:
                file_path = os.path.join(debug_dir, filename)
                try:
                    if LOCAL_DEBUG: logger.debug(f"🗑️ Attempting to delete: {file_path}")
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                        if LOCAL_DEBUG: logger.success(f"🗑️ Successfully deleted: {file_path}")
                except Exception as e:
                    if LOCAL_DEBUG:
                        logger.exception("❌ Failed to delete {file_path}. Reason")
            if LOCAL_DEBUG: logger.debug("🧹 Finished clearing debug directory.")
        except Exception as e:
            if LOCAL_DEBUG:
                logger.exception("❌ Error listing or deleting files in {debug_dir}. Reason")

    else:
        if LOCAL_DEBUG: logger.debug(f"⏩ Debug directory not found: {debug_dir}. Skipping clear.")
