# setup/application_initializer.py
#
# This module provides a function to initialize the main components of the application after core setup tasks are complete.
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
import sys
import pathlib

import workers.logger.logger
from managers.configini.config_reader import Config

app_constants = Config.get_instance()  # Get the singleton instance
import workers.setup.path_initializer as path_initializer
import workers.logger.logger_config as logger_config
import managers.configini.console_encoder as console_encoder
import workers.setup.debug_cleaner as debug_cleaner
from workers.logger.log_utils import _get_log_args
from workers.logger.logger import debug_logger  # import  debug_logger


# Initializes the application's core components.
# This function is responsible for orchestrating the startup sequence after paths and
# logging are configured. It performs final setup tasks and logs the completion status.
# Inputs:
#     None.
# Outputs:
#     bool: True if application initialization completes successfully, False otherwise.
def initialize_app():  # Removed console_print_func, debug_log_func, data_dir arguments
    """Initializes the application's components after paths and logger are set up."""
    debug_logger(
        message=f"🚀 Continuing initialization sequence for version {app_constants.CURRENT_VERSION}.",
        **_get_log_args(),
    )

    try:
        # NOTE: Path, logger, debug directory clearing, and console encoding
        # are now handled in main.py before this function is called.
        # Removed redundant calls to debug_cleaner.clear_debug_directory and console_encoder.configure_console_encoding

        debug_logger(
            message="✅ Application initialization completed successfully.",
            **_get_log_args(),
        )
        return True
    except Exception as e:
        debug_logger(
            message=f"❌ Error during application initialization: {e}",
            **_get_log_args(),
        )
        return False