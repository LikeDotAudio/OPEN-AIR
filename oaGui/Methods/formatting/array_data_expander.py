# oaGui/Methods/array_data_expander.py
# Author: Anthony Peter Kuzub
# Version: 20260501.1000.1
#
# Description: Orchestrates the expansion of a blueprint into a data-mapped item set.

from typing import Any

import orjson
from loguru import logger

from oaGui.Managers.interaction.interaction_view_states import InteractionViewStates
from oaGui.Methods.processing.blueprint_data_injector import BlueprintDataInjector


class ArrayDataExpander:
    """Orchestrates the expansion of a blueprint into a data-mapped item set."""
    @staticmethod
    def expand_blueprint(blueprint: dict, data_array: list[dict], interaction_view_states: InteractionViewStates) -> dict[str, Any]:
        """Creates a collection of item configurations by mapping data to a blueprint."""
        synthetic_fields = {}
        blueprint_template = orjson.dumps(blueprint).decode()

        for idx, item in enumerate(data_array):
            item_id = str(item.get("id", f"item_{idx}"))
            try:
                item_config = orjson.loads(blueprint_template)
                BlueprintDataInjector.inject(item_config, item, interaction_view_states)
                synthetic_fields[item_id] = item_config
            except Exception as e:
                logger.error(f"ArrayExpander: Failed to materialize element {idx}: {e}")

        return synthetic_fields
