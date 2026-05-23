# oaGui/Methods/json_integrity_validator.py
# Author: Anthony Peter Kuzub
# Version: 20260501.1000.1
#
# Description: Serves as the final integrity check for GUI blueprints before rendering begins.

import json
import pathlib
from typing import Any

from oaLogging.Methods.matrix_gate import matrix_log


class JsonIntegrityValidator:
    """
    Handles pre-flight inspection and validation of GUI blueprint JSON files.
    """
    @staticmethod
    def validate(json_path: pathlib.Path) -> dict[str, Any]:
        """
        Inspects JSON for behavior flags and validates structure before rendering.
        """
        behavior_overrides = {}
        try:
            if not json_path.exists():
                return behavior_overrides

            with open(json_path) as f:
                raw_data = json.load(f)

                # Find the root object (often named after the module or generic)
                root_obj = {}
                if isinstance(raw_data, dict) and raw_data:
                    first_val = next(iter(raw_data.values()))
                    if isinstance(first_val, dict):
                        root_obj = first_val
                    else:
                        # Fallback: Maybe the whole file is the root object
                        root_obj = raw_data

                # Check for behavior overrides
                behavior = root_obj.get("behavior", {}) if isinstance(root_obj, dict) else {}
                if "allow_scrolling" in behavior:
                    behavior_overrides["allow_scrolling"] = behavior["allow_scrolling"]
                if "transparent" in behavior:
                    behavior_overrides["transparent"] = behavior["transparent"]

                # ⚡ AUTOMATIC OVERLAY: If the root type is OcaBin, it handles its own scrolling.
                if root_obj.get("type") == "OcaBin" and "allow_scrolling" not in behavior:
                    behavior_overrides["allow_scrolling"] = False
                    behavior_overrides["transparent"] = True

        except Exception as e:
            matrix_log("UI", "GUI_MANAGER", "JsonIntegrityValidator.validate", f"⚠️ Integrity check failed for JSON flags: {e}", level="DEBUG")

        return behavior_overrides
