# Methods/yak_tx.py
# Author: Anthony Peter Kuzub
# Version: 20260218.1
#
# Description: This file (manager_yak_tx.py) is responsible for transmitting the final SCPI command to the device via the ScpiDispatcher.

import os
import inspect
from oaLogging.Core.logger import initialize_logging, set_log_directory
from loguru import logger

from oaConfiguration.FileReaders.config_reader import Config

app_constants = Config.get_instance()
LOCAL_DEBUG = True   

class YakTxManager:
    """
    Transmits SCPI commands to the instrument using the ScpiDispatcher.
    """
    def __init__(self, dispatcher_instance):
        self.dispatcher = dispatcher_instance

    def execute_command(self, command_type, command_string):
        """
        Executes a command based on the presence of a '?' to determine if it is a query.
        """
        current_function_name = inspect.currentframe().f_code.co_name
        
        # --- FIX: Clean the command string before sending ---
        cleaned_command = command_string.strip()
        
        # Check if the command string contains a '?' to identify it as a query
        if '?' in cleaned_command:
            if LOCAL_DEBUG:
                logger.debug(f"🐐🐐🐐🚀 Engaging the '{command_type}' API! Dispatching query command now!")
            return self.dispatcher.query_safe(cleaned_command)
        else:
            if LOCAL_DEBUG:
                logger.debug(f"🐐🐐🐐🚀 Engaging the '{command_type}' API! Dispatching write command now!")
            return self.dispatcher.write_safe(cleaned_command)
