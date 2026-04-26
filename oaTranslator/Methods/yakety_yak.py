# Methods/yakety_yak.py
# Author: Anthony Peter Kuzub
# Version: 20251225.000000.1
#
# Description: Proxy/yak_manager/manager_yakety_yak.py

import inspect

# --- Standard Debug Logging Setup ---
from loguru import logger

from oaConfigurationManager.FileReaders.config_reader import Config

app_constants = Config.get_instance()


# DELETED: YAKETY_YAK_REPO_PATH is now imported from worker_project_paths.py
# repo_topic_filter = "OPEN-AIR/yak/#" # Not needed in deprecated stub
# save_action_topic = "OPEN-AIR/actions/yak/save/trigger" # Not needed in deprecated stub


class DeprecatedYaketyYakManager:  # Renamed class
    """
    DEPRECATED: This class is no longer active. Its functionality has been migrated to YakTranslator.
    """

    def __init__(self, *args, **kwargs):
        current_function_name = inspect.currentframe().f_code.co_name
        logger.error("❌❌❌ WARNING: DeprecatedYaketyYakManager is being instantiated. Use YakTranslator instead!")
        raise DeprecationWarning(
            "YaketyYakManager is deprecated. Use YakTranslator for YAK command translation."
        )

    # All other methods will be removed or commented out.
    # Leaving minimal stub to prevent import errors initially.
