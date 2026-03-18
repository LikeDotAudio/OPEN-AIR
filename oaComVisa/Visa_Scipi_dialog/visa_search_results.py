# managers/VisaScipi/manager_visa_search.py
#
# This manager handles VISA device discovery and validation against yak_config.
#
# Author: Anthony Peter Kuzub
#
import orjson
import pathlib
import re

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True    # Set to False in production, True for dev on this file
from oaLogging.logger import initialize_logging, set_log_directory
from loguru import logger

from oaConfiguration.config_reader import Config

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
        if LOCAL_DEBUG: logger.debug(f"💳 GUI command received: initiating VISA resource search.")
        all_resources = list_visa_resources()
        validated_resources = []

        expected_devices = self.yak_config.get("expected_devices", [])
        if not expected_devices:
            if LOCAL_DEBUG: logger.debug("💳 🟡 No expected devices configured in connection_yak.json. Returning all found resources.")
            self.last_search_results = all_resources  # Store results
            return all_resources

        if LOCAL_DEBUG: logger.debug(f"💳 🔍 Validating {len(all_resources)} resources against {len(expected_devices)} expected device patterns.")

        for resource_name in all_resources:
            is_valid = False
            for device_spec in expected_devices:
                pattern = device_spec.get("resource_pattern")
                if pattern and re.match(pattern, resource_name):
                    if LOCAL_DEBUG: logger.success(f"💳 ✅ Resource '{resource_name}' matched expected device pattern: '{pattern}'.")
                    validated_resources.append(resource_name)
                    is_valid = True
                    break
            if not is_valid:
                logger.error(f"💳 ❌ Resource '{resource_name}' did not match any expected device pattern.")

        if not validated_resources:
            if LOCAL_DEBUG: logger.debug("💳 🟡 No valid resources found matching any expected device patterns.")

        self.last_search_results = validated_resources  # Store results
        return validated_resources

    def get_last_search_results(self):
        """
        Returns the results from the most recent call to search_resources.
        """
        return self.last_search_results