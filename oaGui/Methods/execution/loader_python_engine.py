# oaGui/Methods/python_loader_facade.py
# Author: Anthony Peter Kuzub
# Version: 20260501.1000.1
#
# Description: Handles dynamic loading of Python modules.

import importlib.util
import inspect
import pathlib
import sys
import tkinter as tk
from tkinter import ttk

from oaLogging.Entry import vocal_capture
from oaLogging.Methods.matrix_gate import matrix_log
from oaOchestration.Core.path_initializer import GLOBAL_PROJECT_ROOT


class LoaderPythonEngine:
    """
    Handles dynamic loading of Python modules and identification of GUI classes.
    """

    @staticmethod
    def load(path: pathlib.Path) -> type | None:
        """
        Dynamically imports a Python module and finds GUI classes.
        """
        # Ensure project root is in sys.path for reliable imports.
        if str(GLOBAL_PROJECT_ROOT) not in sys.path:
            sys.path.insert(0, str(GLOBAL_PROJECT_ROOT))

        try:
            matrix_log("ui", "gui_builder", "load_module_from_path", f"📂 Loading GUI module from: {path.name}", "DEBUG")

            try:
                rel_path = path.resolve().relative_to(GLOBAL_PROJECT_ROOT)
                package_parts = list(rel_path.with_suffix("").parts)
                module_full_name = ".".join(package_parts)
            except ValueError:
                module_full_name = path.stem

            spec = importlib.util.spec_from_file_location(module_full_name, path)
            if not spec or not spec.loader:
                matrix_log("ui", "gui_builder", "load_module_from_path", f"❌ Failed to create spec for {path.name}", "ERROR")
                return None

            module = importlib.util.module_from_spec(spec)
            sys.modules[module_full_name] = module
            spec.loader.exec_module(module)

            # Prioritize explicit factory function
            if hasattr(module, "get_gui_class"):
                matrix_log("ui", "gui_builder", "load_module_from_path", f"✅ Found get_gui_class() in {path.name}", "SUCCESS")
                return module.get_gui_class()

            # Fallback: Find a suitable class (inherits from Frame)
            for name, obj in inspect.getmembers(module):
                if (
                    inspect.isclass(obj)
                    and (issubclass(obj, tk.Frame) or issubclass(obj, ttk.Frame))
                    and obj is not tk.Frame
                    and obj is not ttk.Frame
                    and obj.__module__ == module_full_name
                ):
                    matrix_log("ui", "gui_builder", "load_module_from_path", f"✅ Found class {name} in {path.name}", "SUCCESS")
                    return obj

            if path.name not in ["Entry.py", "__init__.py"] and not path.name.startswith("test_"):
                matrix_log("ui", "gui_builder", "load_module_from_path", f"⚠️ No suitable GUI class found in {path.name}", "WARNING")
            return None
        except Exception:
            vocal_capture("BUILDER", f"Failed to load module from {path}")
            return None
