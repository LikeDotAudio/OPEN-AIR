# managers/Display/factory/widget_registry.py
#
# Centralized Widget Registration and Discovery for OPEN-AIR.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Professional services for customizing and tailoring this software to your specific
# application can be negotiated. There is no charge to use, modify, or fork this software.
#
# Build Log: https://like.audio/category/software/spectrum-scanner/
# Source Code: https://github.com/APKaudio/
# Feature Requests can be emailed to i @ like . audio
#
# Version 20260314.120000.REV01

"""
widget_registry.py - Centralized Registry for Dynamic GUI Widgets.

Purpose:
    Provides a singleton registry to decoupled widget creators from the
    primary builder logic. It replaces the legacy 'GuiWidgetFactoryMixin'
    by allowing widgets to register themselves via decorators during system
    initialization.

Responsibilities:
    - Maintain a mapping of widget type identifiers to their respective
      creator classes.
    - Provide a decorator-based interface for self-registration of widgets.
    - Implement an automated discovery mechanism to scan and import widget
      modules from the 'workers/builder' directory.

Constraints:
    - Discovery relies on the 'workers/initialization.path_initializer' to
      resolve the project root.
    - Assumes that widget modules are structured as importable Python files.
"""

from typing import Dict, Any, Type, Callable, Optional
from loguru import logger

# LOCAL_DEBUG: Toggles verbose tracing for widget discovery and registration.
LOCAL_DEBUG = True

class WidgetRegistry:
    """
    Registry for widget creators, facilitating a pluggable UI architecture.
    """
    _registry: Dict[str, Any] = {}
    _initialized = False

    @classmethod
    def register(cls, *widget_types: str):
        """
        Decorator to register a widget creator class in the global registry.

        Lead with action: Binds one or more widget type strings (e.g., 'Fader')
        to the decorated creator class. This allows the builder to resolve
        creators dynamically by name.

        Inputs:
            *widget_types (str): One or more identifiers that this creator
                                handles in the GUI JSON schema.

        Outputs:
            decorator (Callable): The inner decorator function.
        """
        def decorator(creator_class):
            for w_type in widget_types:
                cls._registry[w_type] = creator_class
            return creator_class
        return decorator

    @classmethod
    def get_creator(cls, widget_type: str) -> Optional[Any]:
        """
        Retrieves the creator class for a specific widget identifier.

        Inputs:
            widget_type (str): The unique string identifier of the widget.

        Outputs:
            Optional[Any]: The creator class if found, otherwise None.
        """
        return cls._registry.get(widget_type)

    @classmethod
    def scan_widgets(cls):
        """
        Auto-discovers widget modules by recursively walking the filesystem.

        Lead with action: Scans the 'workers/builder' directory and attempts
        to import all Python modules that do not start with underscores or
        'create_'. Importing these modules triggers their @register decorators.

        Inputs:
            None.

        Outputs:
            None.

        Side Effects:
            - Dynamically imports multiple Python modules into the process.
            - Populates the '_registry' dictionary.
            - Sets '_initialized' to True upon completion.

        Warning:
            This method should only be called once during the UI bootstrap
            phase to avoid redundant filesystem operations and potential
            import cycle issues.
        """
        if cls._initialized:
            return

        import os
        import importlib
        import sys
        from workers.initialization.path_initializer import GLOBAL_PROJECT_ROOT
        
        # ⚡ OPTIMIZATION: Resolve absolute path to ensure consistent discovery.
        base_path = GLOBAL_PROJECT_ROOT / "workers" / "builder"
        
        if not base_path.exists():
            logger.error(f"❌ WidgetRegistry: Path not found: {base_path}")
            return

        if LOCAL_DEBUG: 
            logger.debug(f"🔍 WidgetRegistry: Scanning {base_path}...")

        count = 0
        base_path_str = str(base_path)
        root_path_str = str(GLOBAL_PROJECT_ROOT)

        # Walk the builder directory to find all eligible widget modules.
        for root, dirs, files in os.walk(base_path_str):
            for file in files:
                # Filter for valid Python modules, excluding non-widget files.
                if (file.endswith(".py") and 
                    not file.startswith("__") and 
                    not file.startswith("create_")):
                    
                    # Calculate the dot-notation module path relative to root.
                    rel_path = os.path.relpath(os.path.join(root, file), 
                                               root_path_str)
                    module_path = rel_path.replace(os.path.sep, ".")[:-3]
                    
                    try:
                        # Importing the module triggers self-registration.
                        importlib.import_module(module_path)
                        count += 1
                    except Exception as e:
                        # Silently skip modules that fail to import.
                        pass
        
        cls._initialized = True
        if LOCAL_DEBUG: 
            logger.debug(f"✅ WidgetRegistry: Discovered {len(cls._registry)} "
                         f"types from {count} modules.")
