# Proxy/yak_manager/yak_trigger_handler.py
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
from managers.configini.config_reader import Config

app_constants = Config.get_instance()  # Get the singleton instance
# import orjson # Not needed in deprecated stub

from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args

# from managers.yak_manager.yak_repository_parser import get_command_node, lookup_scpi_command, lookup_inputs, lookup_outputs # Not needed
# from managers.yak_manager.yak_command_builder import fill_scpi_placeholders # Not needed
# from managers.yak_manager.manager_yak_tx import YakTxManager # Not needed
# from managers.yak_manager.manager_yak_rx import YakRxManager # Not needed
from workers.setup.worker_project_paths import YAKETY_YAK_REPO_PATH


def handle_yak_trigger(*args, **kwargs):
    """
    DEPRECATED: This function is no longer active. Its functionality has been migrated to YakTranslator.
    """
    current_function_name = inspect.currentframe().f_code.co_name
    debug_logger(
        message=f"❌❌❌ WARNING: handle_yak_trigger is being called. Use YakTranslator._on_yak_trigger_message instead!",
        **_get_log_args(),
    )
    raise DeprecationWarning(
        "handle_yak_trigger is deprecated. Use YakTranslator._on_yak_trigger_message for YAK command translation."
    )
