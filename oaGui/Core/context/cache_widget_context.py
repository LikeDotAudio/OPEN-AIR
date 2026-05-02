# context/cache_cache_cache_widget_context.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class WidgetContext:
    """
    A strictly typed, immutable context object for widget creation.
    Replaces loose **kwargs to improve transparency and debugging.
    """
    state_mirror_engine: Any
    subscriber_router: Any
    base_mqtt_topic_from_path: str
    app_instance: Any
    # Phase 1: Expansion
    asset_cache_manager: Any = None
    style_manager: Any = None
    transparency_manager: Any = None
    builder_instance: Any = None # ⚡ ADDED: The LoaderOrchestrator instance for transparency

    on_focus_widget: Callable[[str], None] | None = None
    on_complete: Callable[[], None] | None = None

    def get(self, key: str, default: Any = None) -> Any:
        """
        Safe-access fallback for when a WidgetContext is passed to a method 
        expecting a dictionary (e.g. during refactoring or signature shifts).
        """
        return getattr(self, key, default)

    @staticmethod
    def sanitize_geometry(geometry: dict[str, Any]) -> dict[str, Any]:
        """
        ⚡ SANITIZATION: Enforce a minimum pixel size of 1x1 for all materialized containers.
        This prevents the 0x0 value from ever reaching the X11 backend (BadValue).
        """
        if not isinstance(geometry, dict):
            return {"width": 1, "height": 1}

        geometry["width"] = max(1, int(geometry.get("width", 1)))
        geometry["height"] = max(1, int(geometry.get("height", 1)))
        return geometry

# Description: Brief summary of purpose


# --- Standard Debug Logging Setup ---
