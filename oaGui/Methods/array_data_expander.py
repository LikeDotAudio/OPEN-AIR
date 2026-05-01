# oaGui/Methods/array_data_expander.py
# Author: Anthony Peter Kuzub
# Version: 20260501.1000.1
#
# Description: Orchestrates the expansion of a blueprint into a data-mapped item set.

import orjson
from typing import List, Dict, Any
from loguru import logger
from oaGui.Managers.view_manager import ViewManager
from oaGui.Methods.blueprint_data_injector import BlueprintDataInjector

class ArrayDataExpander:
    """Orchestrates the expansion of a blueprint into a data-mapped item set."""
    @staticmethod
    def expand_blueprint(blueprint: Dict, data_array: List[Dict], view_manager: ViewManager) -> Dict[str, Any]:
        """Creates a collection of item configurations by mapping data to a blueprint."""
        synthetic_fields = {}
        blueprint_template = orjson.dumps(blueprint).decode()

        for idx, item in enumerate(data_array):
            item_id = str(item.get("id", f"item_{idx}"))
            try:
                item_config = orjson.loads(blueprint_template)
                BlueprintDataInjector.inject(item_config, item, view_manager)
                synthetic_fields[item_id] = item_config
            except Exception as e:
                logger.error(f"ArrayExpander: Failed to materialize element {idx}: {e}")

        return synthetic_fields
