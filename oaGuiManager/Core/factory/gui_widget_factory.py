# core/gui_widget_factory.py
# Modularized GUI Widget Factory.
# Version 20260315.Modular.1

import importlib
from loguru import logger
from oaGuiManager.Core.context.widget_context import WidgetContext
from oaGuiManager.Core.factory.Core.factory_mapping import get_core_factory_mapping
from oaGuiManager.Core.factory.Core.widget_discovery_engine import WidgetDiscoveryEngine
from oaGuiManager.Core.factory.widget_registry import WidgetRegistry

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

        logger.debug("🔬 Initializing GuiWidgetFactory...")
        
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
        def wrapper(parent_widget, config_data, context: WidgetContext = None, **kwargs):
            module = importlib.import_module(module_path)
            method = getattr(getattr(module, class_name), method_name)
            return method(self, parent_widget, config_data, context=context, **kwargs)
        return wrapper
