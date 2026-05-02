# oaGui/Methods/json_schema_normalizer.py
# Author: Anthony Peter Kuzub
# Version: 20260501.1000.1
#
# Description: Handles recursive schema normalization for GUI blueprints.

from typing import Any, Dict, Optional

class JsonSchemaNormalizer:
    """
    Recursively applies schema normalization to a configuration tree.
    """

    @staticmethod
    def normalize(config: Any, root: Optional[Dict] = None) -> Any:
        """
        Recursively applies schema normalization to a configuration tree.

        Inputs:
            config (dict): The configuration branch to normalize.
            root (dict): The root of the entire tree (for cross-references).
        """
        from oaGui.FileReaders.standardizers.widget_schema_normalizer import WidgetSchemaNormalizer
        
        if root is None:
            root = config if isinstance(config, dict) else {}

        if not isinstance(config, dict):
            return config

        # 1. Normalize the current level (flattens geometry/cosmetics).
        config = WidgetSchemaNormalizer.normalize(config, root_config=root)

        # 2. Optimized recursion: Only descend into logical widget containers.
        if "fields" in config:
            fields = config["fields"]
            if isinstance(fields, dict):
                for key, field in fields.items():
                    fields[key] = JsonSchemaNormalizer.normalize(field, root)
            elif isinstance(fields, list):
                for i, field in enumerate(fields):
                    fields[i] = JsonSchemaNormalizer.normalize(field, root)

        elif "blocks" in config:
            blocks = config["blocks"]
            if isinstance(blocks, dict):
                for key, block in blocks.items():
                    blocks[key] = JsonSchemaNormalizer.normalize(block, root)
            elif isinstance(blocks, list):
                for i, block in enumerate(blocks):
                    blocks[i] = JsonSchemaNormalizer.normalize(block, root)

        elif not config.get("type"):
            # If the current level has no 'type', it is a structural container.
            for key, value in config.items():
                if isinstance(value, dict):
                    # Skip known metadata keys to avoid redundant processing.
                    if key not in ["background", "styles", "style", "behavior",
                                   "metadata", "geometry", "cosmetics", "domain",
                                   "dynamics", "readout", "interaction", "layout"]:
                        config[key] = (
                            JsonSchemaNormalizer.normalize(value, root)
                        )
                elif isinstance(value, list) and key in ["items", "blocks", "fields"]:
                     for i, item in enumerate(value):
                         value[i] = JsonSchemaNormalizer.normalize(item, root)

        return config
