# oaGui/Methods/blueprint_preflight.py
# Author: Anthony Peter Kuzub
# Version: 20260501.1000.1
#
# Description: Handles pre-flight inspection of GUI blueprint JSON files.

import json
import pathlib
from typing import Dict, Any

from oaLogging.Methods.matrix_gate import matrix_log

class BlueprintPreflight:
    """
    Handles pre-flight inspection of GUI blueprint JSON files to extract behavior flags.
    """
    @staticmethod
    def inspect(json_path: pathlib.Path) -> Dict[str, Any]:
        """
        Inspects JSON for behavior flags before scaffolding.
        """
        behavior_overrides = {}
        try:
            if not json_path.exists():
                return behavior_overrides

            with open(json_path, 'r') as f:
                raw_data = json.load(f)
                
                # Find the root object (often named after the module or generic)
                root_obj = next(iter(raw_data.values())) if isinstance(raw_data, dict) and raw_data else {}
                
                # Check for behavior overrides
                behavior = root_obj.get("behavior", {})
                if "allow_scrolling" in behavior:
                    behavior_overrides["allow_scrolling"] = behavior["allow_scrolling"]
                if "transparent" in behavior:
                    behavior_overrides["transparent"] = behavior["transparent"]
                
                # ⚡ AUTOMATIC OVERLAY: If the root type is OcaBin, it handles its own scrolling.
                if root_obj.get("type") == "OcaBin" and "allow_scrolling" not in behavior:
                    behavior_overrides["allow_scrolling"] = False
                    behavior_overrides["transparent"] = True

        except Exception as e:
            matrix_log("UI", "GUI_MANAGER", "BlueprintPreflight.inspect", f"⚠️ Failed to pre-read JSON flags: {e}", level="DEBUG")
            
        return behavior_overrides
