# Core/widget_discovery_engine.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import inspect
import tkinter as tk

from loguru import logger

from oaGuiManager.Core.factory.widget_registry import WidgetRegistry
from oaLogging.Methods.matrix_gate import matrix_log

# --- Standard Debug Logging Setup ---

class WidgetDiscoveryEngine:
    """Handles merging auto-discovered widgets from the Registry into the Factory."""

    @staticmethod
    def merge_registry(factory, builder_instance):
        registry_items = WidgetRegistry._registry
        if not registry_items: return factory

        matrix_log("UI", "GUI_MANAGER", inspect.currentframe().f_code.co_name, f"🧩 Merging {len(registry_items)} widgets from Registry into Factory.", level="DEBUG")
        for widget_type, creator_class in registry_items.items():
            factory[widget_type] = WidgetDiscoveryEngine._make_wrapper(creator_class, builder_instance)
        return factory

    @staticmethod
    def _make_wrapper(cls_ref, builder_instance):
        def wrapper(parent_widget, config_data, context=None, **kwargs):
            try:
                if not hasattr(cls_ref, 'make'):
                    logger.warning(f"⚠️ Registry class {cls_ref} missing static 'make' method.")
                    return None

                # Ensure builder instance is passed if missing from context
                if context and not hasattr(context, 'builder_instance'):
                    kwargs['builder_instance'] = builder_instance
                elif not context:
                    kwargs['builder_instance'] = builder_instance

                # Registry widgets use static make(parent, config, context, **kwargs)
                return cls_ref.make(parent_widget, config_data, context, **kwargs)
            except Exception as e:
                logger.exception(f"❌ Failed to instantiate widget of type {cls_ref} at {config_data.get('path', 'unknown')}: {e}")
                # Create a fallback error label in the UI
                return tk.Label(parent_widget, text=f"Error: {e}", fg="red", bg="#2b2b2b")
        return wrapper
