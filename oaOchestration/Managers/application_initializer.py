# Managers/application_initializer.py
# Author: Anthony Peter Kuzub
# Version: 20250821.200641.1
#
# Description: This module provides a function to initialize the main components of the application after core setup tasks are complete.

import os

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True    # Set to False in production, True for dev on this file
from oaLogging.Core.logger import initialize_logging, set_log_directory
from loguru import logger

from oaConfiguration.FileReaders.config_reader import Config

app_constants = Config.get_instance()  # Get the singleton instance


# Initializes the application's core components.
# This function is responsible for orchestrating the startup sequence after paths and
# logging are configured. It performs final setup tasks and logs the completion status.
# Inputs:
#     None.
# Outputs:
#     bool: True if application initialization completes successfully, False otherwise.
def initialize_app():  # Removed console_print_func, debug_log_func, data_dir arguments
    """Initializes the application's components after paths and logger are set up."""
    if LOCAL_DEBUG:
        logger.debug(
            f"🚀🏗️🔋 [BOOT] Continuing initialization sequence for version "
            f"{app_constants.CURRENT_VERSION}."
        )

    try:
        # NOTE: Path, logger, debug directory clearing, and console encoding
        # are now handled in main.py before this function is called.
        # Removed redundant calls to debug_cleaner.clear_debug_directory and console_encoder.configure_console_encoding

        if LOCAL_DEBUG:
            logger.success(
                "🚀🏗️✅ [SUCCESS] Application initialization completed."
            )
        return True
    except Exception as e:
        logger.exception(
            f"🚀🏗️❌ [ERROR] Error during application initialization: {e}"
        )
        return False
