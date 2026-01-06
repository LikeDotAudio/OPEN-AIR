# managers/VisaScipi/manager_visa_search.py
#
# This manager handles VISA device discovery and validation against yak_config.
#
# Author: Anthony Peter Kuzub
#
import orjson
import pathlib
import re
from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args
from .manager_visa_list_visa_resources import list_visa_resources


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
        debug_logger(
            message=f"💳 GUI command received: initiating VISA resource search.",
            **_get_log_args(),
        )
        all_resources = list_visa_resources()
        validated_resources = []

        expected_devices = self.yak_config.get("expected_devices", [])
        if not expected_devices:
            debug_logger(
                message="💳 🟡 No expected devices configured in connection_yak.json. Returning all found resources.",
                **_get_log_args(),
            )
            self.last_search_results = all_resources  # Store results
            return all_resources

        debug_logger(
            message=f"💳 🔍 Validating {len(all_resources)} resources against {len(expected_devices)} expected device patterns.",
            **_get_log_args(),
        )

        for resource_name in all_resources:
            is_valid = False
            for device_spec in expected_devices:
                pattern = device_spec.get("resource_pattern")
                if pattern and re.match(pattern, resource_name):
                    debug_logger(
                        message=f"💳 ✅ Resource '{resource_name}' matched expected device pattern: '{pattern}'.",
                        **_get_log_args(),
                    )
                    validated_resources.append(resource_name)
                    is_valid = True
                    break
            if not is_valid:
                debug_logger(
                    message=f"💳 ❌ Resource '{resource_name}' did not match any expected device pattern.",
                    **_get_log_args(),
                )

        if not validated_resources:
            debug_logger(
                message="💳 🟡 No valid resources found matching any expected device patterns.",
                **_get_log_args(),
            )

        self.last_search_results = validated_resources  # Store results
        return validated_resources

    def get_last_search_results(self):
        """
        Returns the results from the most recent call to search_resources.
        """
        return self.last_search_results
