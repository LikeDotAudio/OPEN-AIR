# oaGui/Methods/blueprint_merger.py
# Author: Anthony Peter Kuzub
# Version: 1.0.1
#
# Description: Handles recursive merging of GUI blueprint configurations.

import copy


class BlueprintMerger:
    """
    Handles recursive merging of GUI blueprint configurations.
    """

    @staticmethod
    def merge_blueprints(base: dict, overrides: dict) -> dict:
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
                result[key] = BlueprintMerger.merge_blueprints(result[key], value)
            else:
                result[key] = copy.deepcopy(value)
        return result

    # Legacy Alias
    @staticmethod
    def merge(base: dict, overrides: dict) -> dict:
        return BlueprintMerger.merge_blueprints(base, overrides)
