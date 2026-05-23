# oaGui/Methods/blueprint_data_injector.py
# Author: Anthony Peter Kuzub
# Version: 20260501.1000.1
#
# Description: Handles recursive injection of data and view managers into JSON blueprints.

from typing import Any

from oaGui.Managers.interaction.interaction_view_states import InteractionViewStates


class BlueprintDataInjector:
    """Handles recursive injection of data and view managers into JSON blueprints."""
    @classmethod
    def inject(cls, config: Any, data: dict, interaction_view_states: InteractionViewStates | None = None):
        """Recursively injects data context and view manager into the configuration."""
        if isinstance(config, dict):
            cls._inject_into_dict(config, data, interaction_view_states)
        elif isinstance(config, list):
            cls._inject_into_list(config, data, interaction_view_states)

    @classmethod
    def _inject_into_dict(cls, config: dict, data: dict, vm: InteractionViewStates | None):
        # Specific injection for collapsible blocks
        if config.get("type") == "OcaCollapsibleBlock" and vm:
            config["_view_manager"] = vm

        for key, value in config.items():
            if isinstance(value, (dict, list)):
                cls.inject(value, data, vm)
            elif isinstance(value, str) and "{{" in value:
                config[key] = cls._resolve_string_placeholders(value, data)

    @classmethod
    def _inject_into_list(cls, config: list, data: dict, vm: InteractionViewStates | None):
        for i, value in enumerate(config):
            if isinstance(value, (dict, list)):
                cls.inject(value, data, vm)
            elif isinstance(value, str) and "{{" in value:
                config[i] = cls._resolve_string_placeholders(value, data)

    @staticmethod
    def _resolve_string_placeholders(text: str, data: dict) -> Any:
        """Replaces {{key}} placeholders with values from the data context."""
        for key, val in data.items():
            placeholder = f"{{{{{key}}}}}"
            if text == placeholder:
                return val
            if placeholder in text:
                text = text.replace(placeholder, str(val))
        return text
