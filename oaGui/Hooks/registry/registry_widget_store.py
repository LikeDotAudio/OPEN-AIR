# Hooks/registry_widget_store.py
# Author: Anthony Peter Kuzub
# Version: 20260314.120000.REV01
#
# Description: Centralized Registry for Dynamic GUI Widgets.

import importlib
import inspect
import os
from typing import Any

from loguru import logger

from oaLogging.Methods.matrix_gate import matrix_log
from oaOchestration.Core.path_initializer import GLOBAL_PROJECT_ROOT


class RegistryWidgetStore:
    """
    Registry for widget creators, facilitating a pluggable UI architecture.
    """
    _registry: dict[str, Any] = {}
    _initialized = False

    @classmethod
    def register(cls, *widget_types: str):
        """
        Decorator to register a widget creator class in the global registry.
        """
        def decorator(creator_class):
            for w_type in widget_types:
                cls._registry[w_type] = creator_class
            return creator_class
        return decorator

    @classmethod
    def get_registry(cls) -> dict[str, Any]:
        """
        Returns a copy of the current widget registry.
        """
        return cls._registry.copy()

    @classmethod
    def get_creator(cls, widget_type: str) -> Any | None:
        """
        Retrieves the creator class for a specific widget identifier.
        """
        return cls._registry.get(widget_type)

    @classmethod
    def scan_widgets(cls):
        """
        Auto-discovers widget modules by recursively walking the filesystem.
        """
        if cls._initialized:
            return

        # ⚡ AUTO-DISCOVERY: Resolve absolute path to ensure consistent discovery.
        base_path = GLOBAL_PROJECT_ROOT / "oaGuiElements"

        if not base_path.exists():
            logger.error(f"❌ RegistryWidgetStore: Path not found: {base_path}")
            return

        matrix_log("UI", "GUI_MANAGER", inspect.currentframe().f_code.co_name, f"🔍 RegistryWidgetStore: Scanning {base_path}...", level="DEBUG")

        count = 0
        base_path_str = str(base_path)
        root_path_str = str(GLOBAL_PROJECT_ROOT)

        from oaGui.FileReaders.scanner.folder_fast_io_utility import FastScanner
        scanner = FastScanner()

        # High-performance recursive scan
        files = scanner.scan_directory(base_path_str, ".py")

        for file_path in files:
            file = os.path.basename(file_path)
            # Filter for valid Python modules, excluding non-widget files.
            if not file.startswith("__") and not file.startswith("create_"):
                # Calculate the dot-notation module path relative to root.
                rel_path = os.path.relpath(file_path, root_path_str)
                module_path = rel_path.replace(os.path.sep, ".")[:-3]

                try:
                    # Importing the module triggers self-registration.
                    importlib.import_module(module_path)
                    count += 1
                except Exception:
                    # Silently skip modules that fail to import.
                    pass

        cls._initialized = True
        matrix_log("UI", "GUI_MANAGER", inspect.currentframe().f_code.co_name, f"✅ RegistryWidgetStore: Discovered {len(cls._registry)} types from {count} modules.", level="DEBUG")
