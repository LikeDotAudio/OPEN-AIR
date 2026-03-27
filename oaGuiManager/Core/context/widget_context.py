# context/widget_context.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

from dataclasses import dataclass
from typing import Any, Optional, Callable

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
    builder_instance: Any = None # ⚡ ADDED: The DynamicGuiBuilder instance for transparency
    
    on_focus_widget: Optional[Callable[[str], None]] = None
    on_complete: Optional[Callable[[], None]] = None

    def get(self, key: str, default: Any = None) -> Any:
        """
        Safe-access fallback for when a WidgetContext is passed to a method 
        expecting a dictionary (e.g. during refactoring or signature shifts).
        """
        return getattr(self, key, default)
