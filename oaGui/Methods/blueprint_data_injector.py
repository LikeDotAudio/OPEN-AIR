# oaGui/Methods/blueprint_data_injector.py
# Author: Anthony Peter Kuzub
# Version: 20260501.1000.1
#
# Description: Handles recursive injection of data and view managers into JSON blueprints.

from typing import Any, Dict, Optional
from oaGui.Managers.view_manager import ViewManager

class BlueprintDataInjector:
    """Handles recursive injection of data and view managers into JSON blueprints."""
    @classmethod
    def inject(cls, config: Any, data: Dict, view_manager: Optional[ViewManager] = None):
        """Recursively injects data context and view manager into the configuration."""
        if isinstance(config, dict):
            cls._inject_into_dict(config, data, view_manager)
        elif isinstance(config, list):
            cls._inject_into_list(config, data, view_manager)

    @classmethod
    def _inject_into_dict(cls, config: Dict, data: Dict, vm: Optional[ViewManager]):
        # Specific injection for collapsible blocks
        if config.get("type") == "OcaCollapsibleBlock" and vm:
            config["_view_manager"] = vm

        for key, value in config.items():
            if isinstance(value, (dict, list)):
                cls.inject(value, data, vm)
            elif isinstance(value, str) and "{{" in value:
                config[key] = cls._resolve_string_placeholders(value, data)

    @classmethod
    def _inject_into_list(cls, config: list, data: dict, vm: Optional[ViewManager]):
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
