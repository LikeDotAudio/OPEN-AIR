# Proxy/yak_manager/manager_yakety_yak.py
#
# THIS FILE IS DEPRECATED. Its functionality has been migrated to Proxy/yak_manager/yak_translator.py.
# This stub remains to prevent import errors and to provide a clear deprecation warning.
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
#
# Version 20251225.000000.1 (DEPRECATED)

import os
import inspect

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True    # Set to False in production, True for dev on this file
from oaLogging.Core.logger import initialize_logging, set_log_directory
from loguru import logger

from oaConfiguration.FileReaders.config_reader import Config

app_constants = Config.get_instance()

from oaOchestration.Constants.project_paths import YAKETY_YAK_REPO_PATH

# DELETED: YAKETY_YAK_REPO_PATH is now imported from worker_project_paths.py
# repo_topic_filter = "OPEN-AIR/yak/#" # Not needed in deprecated stub
# save_action_topic = "OPEN-AIR/actions/yak/save/trigger" # Not needed in deprecated stub


class DeprecatedYaketyYakManager:  # Renamed class
    """
    DEPRECATED: This class is no longer active. Its functionality has been migrated to YakTranslator.
    """

    def __init__(self, *args, **kwargs):
        current_function_name = inspect.currentframe().f_code.co_name
        logger.error(f"❌❌❌ WARNING: DeprecatedYaketyYakManager is being instantiated. Use YakTranslator instead!")
        raise DeprecationWarning(
            "YaketyYakManager is deprecated. Use YakTranslator for YAK command translation."
        )

    # All other methods will be removed or commented out.
    # Leaving minimal stub to prevent import errors initially.
    # def _load_repo_from_file(self): ...
    # def _save_repo_to_file(self): ...
    # def YAK_LISTEN_TO_MQTT(self, topic, payload): ...
    # def YAK_SAVE_REPOSITORY(self, topic, payload): ...