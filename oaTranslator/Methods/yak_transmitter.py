# oaTranslator/Methods/yak_transmitter.py
# Author: Anthony Peter Kuzub
# Version: 20260413.0010.1
#
# Description: This file (yak_transmitter.py) is responsible for transmitting the final SCPI command to the device via the ScpiDispatcher.

import os
from oaLogging.Methods.matrix_gate import matrix_log
import inspect
import inspect
from oaLogging.Core.logger import initialize_logging, set_log_directory
from loguru import logger

from oaConfigurationManager.FileReaders.config_reader import Config

app_constants = Config.get_instance()

class YakTransmitterManager:
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
            matrix_log("UI", "TRANSLATOR", inspect.currentframe().f_code.co_name, f"🐐🐐🐐🚀 Engaging the '{command_type}' API! Dispatching query command now!", level="DEBUG")
            return self.dispatcher.query_safe(cleaned_command)
        else:
            matrix_log("UI", "TRANSLATOR", inspect.currentframe().f_code.co_name, f"🐐🐐🐐🚀 Engaging the '{command_type}' API! Dispatching write command now!", level="DEBUG")
            return self.dispatcher.write_safe(cleaned_command)
