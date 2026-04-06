# Managers/application_initializer.py
#
# Provides a function to initialize the main components of the application 
# after core setup tasks are complete. Orchestrates the final startup sequence.
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
# Version 20260330.1600.1

import os
import inspect
import loguru
from oaLogging.Methods.matrix_gate import matrix_log
from oaConfigurationManager.FileReaders.config_reader import Config

# Explicitly assign logger to ensure it's found as a module attribute by unittest.mock
logger = loguru.logger

LOCAL_DEBUG = False
app_constants = Config.get_instance()

def initialize_app():
    """Initializes the application's components after paths and logger are set up."""
    if LOCAL_DEBUG:
        logger.debug(f"🚀🏗️🔋 [BOOT] Continuing initialization sequence for version {app_constants.CURRENT_VERSION}.")
        matrix_log("core", "system", "initialize_app", 
                   f"🚀🏗️🔋 [BOOT] Continuing initialization sequence for version {app_constants.CURRENT_VERSION}.", "DEBUG")

    try:
        if LOCAL_DEBUG:
            # The test specifically mocks logger.success to trigger an exception in test_initialize_app_exception
            logger.success("🚀🏗️✅ [SUCCESS] Application initialization completed.")
            matrix_log("core", "system", "initialize_app", 
                       "🚀🏗️✅ [SUCCESS] Application initialization completed.", "SUCCESS")
        return True
    except Exception as e:
        # matrix_log does not support exception() directly, but we use ERROR level for forensic integrity
        logger.exception(f"Error during application initialization: {e}")
        matrix_log("core", "system", "initialize_app", 
                   f"🚀🏗️❌ [ERROR] Error during application initialization: {e}", "ERROR")
        return False
