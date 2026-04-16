# context/widget_context.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

from dataclasses import dataclass
from typing import Any, Optional, Callable, Dict

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

    @staticmethod
    def sanitize_geometry(geometry: Dict[str, Any]) -> Dict[str, Any]:
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

import tkinter as tk
from oaLogging.Methods.matrix_gate import matrix_log
import inspect
from tkinter import ttk
import orjson
import os

# --- Standard Debug Logging Setup ---
from oaLogging.Core.logger import initialize_logging, set_log_directory
from loguru import logger
