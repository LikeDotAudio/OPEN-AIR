# Core/factory/Core/widget_discovery_engine.py
#
# Handles merging auto-discovered widgets from the Registry into the Factory.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Professional services for customizing and tailoring this software to your 
# specific application can be negotiated. There is no charge to use, modify, 
# or fork this software.
#
# Build Log: https://like.audio/category/software/spectrum-scanner/
# Source Code: https://github.com/APKaudio/
# Feature Requests can be emailed to i @ like . audio
#
# Version 20260501.1010.1
#
# The Discovery Engine is a critical component of the "Partitioned Architecture" 
# and "Widget Registry" systems. It allows for decoupled development of new UI 
# components. By decorating a class with @RegistryWidgetStore.register, any new 
# widget is automatically discovered and wrapped by this engine, making it 
# instantly available to the Dynamic GUI Builder.

import inspect
import tkinter as tk

from loguru import logger

from oaGui.Hooks.registry.registry_widget_store import RegistryWidgetStore
from oaLogging.Methods.matrix_gate import matrix_log

class WidgetDiscoveryEngine:
    """
    Service for integrating registered widgets into the central widget factory.
    """

    @staticmethod
    def merge_registry(factory, builder_instance):
        """
        Merges all registered widget types into the provided factory dictionary.
        
        This method iterates over the global RegistryWidgetStore, wrapping each 
        registered class in a factory-compatible creator function.
        
        Inputs:
            factory (dict): The target dictionary to populate with creator 
                            functions.
            builder_instance (object): The active GUI builder instance to be 
                                       passed as context to created widgets.
        
        Returns:
            dict: The updated factory dictionary.
            
        Side Effects:
            - Logs the number of merged widgets.
            - Modifies the 'factory' dictionary in-place.
        """
        registry_items = RegistryWidgetStore._registry
        if not registry_items: return factory

        matrix_log("UI", "GUI_MANAGER", inspect.currentframe().f_code.co_name, f"🧩 Merging {len(registry_items)} widgets from Registry into Factory.", level="DEBUG")
        for widget_type, creator_class in registry_items.items():
            factory[widget_type] = WidgetDiscoveryEngine._make_wrapper(creator_class, builder_instance)
        return factory

    @staticmethod
    def _make_wrapper(cls_ref, builder_instance):
        """
        Creates a closure that acts as a factory creator for a registered class.
        
        The wrapper ensures that the registered class's static 'make' method is 
        called with the correct parent, configuration, and context. It also 
        provides a fallback UI element if instantiation fails.
        
        Inputs:
            cls_ref (class): The widget class to wrap.
            builder_instance (object): The builder to inject into the widget 
                                       context.
        
        Returns:
            function: A creator function compatible with the factory pattern.
            
        Error Handling:
            - Validates the existence of a 'make' method.
            - Catches all instantiation exceptions and returns a red 
              tk.Label as a visual error indicator in the UI.
        """
        def wrapper(parent_widget, configuration, context=None, **kwargs):
            try:
                # Every registered widget MUST implement a static 'make' method
                if not hasattr(cls_ref, 'make'):
                    logger.warning(f"⚠️ Registry class {cls_ref} missing static 'make' method.")
                    return None

                # Ensure builder instance is passed if missing from context 
                # to maintain the service chain.
                if context and not hasattr(context, 'builder_instance'):
                    kwargs['builder_instance'] = builder_instance
                elif not context:
                    kwargs['builder_instance'] = builder_instance

                # Registry widgets use static make(parent, config, context, **kwargs)
                # to allow for flexible instantiation patterns.
                return cls_ref.make(parent_widget, configuration, context, **kwargs)
            except Exception as e:
                logger.exception(f"❌ Failed to instantiate widget of type {cls_ref} at {configuration.get('path', 'unknown')}: {e}")
                # Visual forensic: Return a failure indicator directly to the UI
                return tk.Label(parent_widget, text=f"Error: {e}", fg="red", bg="#2b2b2b")
        return wrapper
