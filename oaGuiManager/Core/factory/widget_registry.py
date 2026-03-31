# factory/widget_registry.py
# Author: Anthony Peter Kuzub
# Version: 20260314.120000.REV01
#
# Description: managers/Display/factory/widget_registry.py

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
from oaLogging.Methods.matrix_gate import matrix_log
import inspect
      modules from the 'workers/builder' directory.

Constraints:
    - Discovery relies on the 'workers/initialization.path_initializer' to
      resolve the project root.
    - Assumes that widget modules are structured as importable Python files.
"""

from typing import Dict, Any, Type, Callable, Optional
from loguru import logger

# LOCAL_DEBUG: Toggles verbose tracing for widget discovery and registration.

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
    def get_registry(cls) -> Dict[str, Any]:
        """
        Returns a copy of the current widget registry.
        """
        return cls._registry.copy()

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
        from oaOchestration.Core.path_initializer import GLOBAL_PROJECT_ROOT
        
        # ⚡ AUTO-DISCOVERY: Resolve absolute path to ensure consistent discovery.
        base_path = GLOBAL_PROJECT_ROOT / "oaGuiElements"
        
        if not base_path.exists():
            logger.error(f"❌ WidgetRegistry: Path not found: {base_path}")
            return

        matrix_log("UI", "GUI_MANAGER", inspect.currentframe().f_code.co_name, f"🔍 WidgetRegistry: Scanning {base_path}...", level="DEBUG")

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
        matrix_log("UI", "GUI_MANAGER", inspect.currentframe().f_code.co_name, f"✅ WidgetRegistry: Discovered {len(cls._registry, level="DEBUG")
                     f"types from {count} modules.")
