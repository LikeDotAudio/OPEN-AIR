# Hooks/gui_widget_factory.py
# Author: Anthony Peter Kuzub
# Version: 20260315.Modular.1
#
# Description: Modularized GUI Widget Factory.

import importlib
import inspect

from oaGui.Core.context.widget_context import WidgetContext
from oaGui.Core.factory.Core.factory_mapping import get_core_factory_mapping
from oaGui.Core.factory.Core.widget_discovery_engine import WidgetDiscoveryEngine
from oaGui.Hooks.widget_registry import WidgetRegistry

# --- Standard Debug Logging Setup ---
from oaLogging.Methods.matrix_gate import matrix_log


class GuiWidgetFactoryMixin:
    """
    The Registry that maps JSON keys to Creator Methods.
    Refactored to eliminate 'Dependency Magnet' anti-pattern.
    Relies entirely on WidgetRegistry and dynamic discovery.
    """

    _WIDGET_FACTORY_CACHE = None

    def _initialize_widget_factory(self):
        if GuiWidgetFactoryMixin._WIDGET_FACTORY_CACHE is not None:
            self.widget_factory = GuiWidgetFactoryMixin._WIDGET_FACTORY_CACHE
            return

        matrix_log("UI", "GUI_MANAGER", inspect.currentframe().f_code.co_name, "Initializing GuiWidgetFactory...", level="DEBUG")

        # Pull the dynamically built registry instead of hardcoding 40 imports
        factory = WidgetRegistry.get_registry()

        # Merge any core/legacy mappings if absolutely necessary
        core_mapping = get_core_factory_mapping(self)
        factory.update(core_mapping)

        # Merge dynamically discovered widgets (plugin pattern)
        factory = WidgetDiscoveryEngine.merge_registry(factory, self)

        GuiWidgetFactoryMixin._WIDGET_FACTORY_CACHE = factory
        self.widget_factory = factory

    def _lazy_wrap(self, module_path, class_name, method_name):
        # Capture the builder instance (self) for context injection
        builder_instance = self

        def wrapper(parent_widget, config_data, context: WidgetContext = None, **kwargs):
            module = importlib.import_module(module_path)
            cls_ref = getattr(module, class_name)

            # Ensure context isn't passed twice if it's already in kwargs
            kwargs.pop("context", None)

            # ⚡ CONTEXT INJECTION: Pass builder instance if missing
            if context and not hasattr(context, 'builder_instance'):
                kwargs['builder_instance'] = builder_instance
            elif not context:
                kwargs['builder_instance'] = builder_instance

            # ⚡ STANDARDIZED FACTORY PATTERN: Prefer static 'make' if available.
            # This avoids 'Data Trampolining' and ensures correct 'self' handling.
            if hasattr(cls_ref, 'make'):
                return cls_ref.make(parent_widget, config_data, context=context, **kwargs)

            # ⚡ FALLBACK: Call the specified method directly.
            # Note: We pass builder_instance as the first argument (self) to support Mixin-style creators.
            method = getattr(cls_ref, method_name)
            return method(builder_instance, parent_widget, config_data, context=context, **kwargs)

        return wrapper
