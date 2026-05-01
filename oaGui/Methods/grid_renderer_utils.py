# Methods/grid_renderer_utils.py
# Author: Anthony Peter Kuzub
# Version: 20260501.1000.1
#
# Description: Utility methods for normalized field discovery in grid rendering.

class GridRendererUtils:
    """Utility methods for normalized field discovery in grid rendering."""
    @staticmethod
    def resolve_fields(data):
        """Finds the actual widget fields, descending through 'blocks' or 'fields' containers."""
        fields = data.get("fields", data.get("blocks"))

        # If the level has no 'type', it's an anonymous container
        if fields is None and not data.get("type"):
            fields = data

        # Recursive descend: Handle 'blocks -> fields' redundant nesting
        while isinstance(fields, dict) and len(fields) == 1:
            key = next(iter(fields))
            if key in ["fields", "blocks"]:
                fields = fields[key]
            else:
                break
        return fields

    @staticmethod
    def normalize_item_config(config):
        """Ensures internal OcaBlock/OcaBin fields are discovered for an item."""
        item_config = config
        if not isinstance(item_config, dict):
            return item_config

        while isinstance(item_config, dict) and len(item_config) == 1 and not item_config.get("type"):
            inner_key = next(iter(item_config))
            if inner_key in ["fields", "blocks"]:
                item_config = item_config[inner_key]
            else:
                break
        return item_config
