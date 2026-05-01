# oaGui/Methods/blueprint_merger.py
# Author: Anthony Peter Kuzub
# Version: 20260501.1000.1
#
# Description: Handles recursive merging of GUI blueprint configurations.

import copy
from typing import Dict

class BlueprintMerger:
    """
    Handles recursive merging of GUI blueprint configurations.
    """

    @staticmethod
    def merge(base: Dict, overrides: Dict) -> Dict:
        """
        Recursively merges an override dictionary into a base dictionary.

        Inputs:
            base (dict): The underlying configuration (typically defaults).
            overrides (dict): The specific configuration to apply on top.

        Outputs:
            dict: The combined result of the merge.
        """
        # Ensure the base is cloned to prevent accidental mutation of the cache.
        result = copy.deepcopy(base)
        for key, value in overrides.items():
            if (isinstance(value, dict) and key in result and
                isinstance(result[key], dict)):
                result[key] = BlueprintMerger.merge(result[key], value)
            else:
                result[key] = copy.deepcopy(value)
        return result
