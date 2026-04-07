import pathlib

import inspect
from oaLogging.Methods.matrix_gate import matrix_log
# Methods/visa_search_results.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: This manager handles VISA device discovery and validation against yak_config.

import orjson
import re

# --- Standard Debug Logging Setup ---
from oaLogging.Core.logger import initialize_logging, set_log_directory
from loguru import logger

from oaConfigurationManager.FileReaders.config_reader import Config

app_constants = Config.get_instance()

from .visa_list_visa_resources import list_visa_resources


class VisaDeviceSearcher:
    def __init__(self):
        self.yak_config = self._load_yak_config()
        self.last_search_results = []  # New instance variable to store search results

    def _load_yak_config(self):
        # The content of connection_yak.json is embedded directly as requested by the user.
        return {
            "expected_devices": [
                {
                    "name": "Generic USB Instrument",
                    "resource_pattern": "USB[0-9]*::[0-9a-fA-F]+::[0-9a-fA-F]+::.*::INSTR",
                },
                {
                    "name": "Generic ASRL Instrument",
                    "resource_pattern": "ASRL/dev/tty(S|USB)[0-9]+::INSTR",
                },
                {"name": "Any other INSTR device", "resource_pattern": ".*::INSTR"},
            ]
        }

    def search_resources(self):
        matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"💳 GUI command received: initiating VISA resource search.", "DEBUG")
        all_resources = list_visa_resources()
        validated_resources = []

        expected_devices = self.yak_config.get("expected_devices", [])
        if not expected_devices:
            matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "💳 🟡 No expected devices configured in connection_yak.json. Returning all found resources.", "DEBUG")
            self.last_search_results = all_resources  # Store results
            return all_resources

        matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"💳 🔍 Validating {len(all_resources)} resources against {len(expected_devices)} expected device patterns.", "DEBUG")

        for resource_name in all_resources:
            is_valid = False
            for device_spec in expected_devices:
                pattern = device_spec.get("resource_pattern")
                if pattern and re.match(pattern, resource_name):
                    matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"💳 ✅ Resource '{resource_name}' matched expected device pattern: '{pattern}'.", "SUCCESS")
                    validated_resources.append(resource_name)
                    is_valid = True
                    break
            if not is_valid:
                logger.error(f"💳 ❌ Resource '{resource_name}' did not match any expected device pattern.")

        if not validated_resources:
            matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "💳 🟡 No valid resources found matching any expected device patterns.", "DEBUG")

        self.last_search_results = validated_resources  # Store results
        return validated_resources

    def get_last_search_results(self):
        """
        Returns the results from the most recent call to search_resources.
        """
        return self.last_search_results