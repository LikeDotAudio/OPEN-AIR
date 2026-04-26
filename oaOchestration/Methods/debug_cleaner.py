
import inspect

from oaLogging.Methods.matrix_gate import matrix_log

# Methods/debug_cleaner.py
# Author: Anthony Peter Kuzub
# Version: 20250821.200641.1
#
# Description: This module provides a function to clear the debug directory of log files.


# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = False
from loguru import logger

from oaConfigurationManager.FileReaders.config_reader import Config

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
    matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "▶️ Entering clear_debug_directory.", "DEBUG")

    if DATA_LOGS_DIR.exists():
        matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"🔍 Log directory found: {DATA_LOGS_DIR}. Proceeding to clear contents.", "DEBUG")
        try:
            for item in DATA_LOGS_DIR.iterdir():
                try:
                    if item.is_file():
                        item.unlink()
                        matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"🗑️ Successfully deleted: {item}", "SUCCESS")
                except Exception as e:
                    if LOCAL_DEBUG: logger.error(f"❌ Failed to delete {item}: {e}")
            matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "🧹 Finished clearing log directory.", "DEBUG")
        except Exception as e:
            if LOCAL_DEBUG: logger.error(f"❌ Error clearing log directory: {e}")
    else:
        matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"⏩ Log directory not found: {DATA_LOGS_DIR}. Skipping clear.", "DEBUG")
