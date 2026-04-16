# FileReaders/module_loader.py
# Author: Anthony Peter Kuzub
# Version: 20260218.Optimization.2
#
# Description: Handles dynamic loading of Python modules and instantiation of GUI classes.

import os
from oaLogging.Methods.matrix_gate import matrix_log
import inspect
import inspect
import sys
import importlib.util
import pathlib
import tkinter as tk
from tkinter import ttk

# --- Standard Debug Logging Setup ---
from oaLogging.Entry import logger, vocal_capture, set_log_directory

from oaConfigurationManager.FileReaders.config_reader import Config

app_constants = Config.get_instance()

from oaComProtocols.oaComMQTT.Methods.mqtt_topic_utils import generate_topic_path_from_filepath
from oaGuiManager.Core.loader.gui_from_json import UniversalGuiLoader
from oaOchestration.Core.path_initializer import GLOBAL_PROJECT_ROOT
from oaGuiBuilder.Workers.builder import DynamicGuiBuilder

# Globals for Versioning
current_version = "20260218.1755.1"

class ModuleLoader:
    """
    Handles dynamic loading of Python modules and instantiation of GUI classes.
    """

    def __init__(self, theme_colors, state_mirror_engine=None, subscriber_router=None, app_instance=None):
        self.theme_colors = theme_colors
        self.state_mirror_engine = state_mirror_engine
        self.subscriber_router = subscriber_router
        self.app_instance = app_instance
        self.builders = []

    def get_all_builders(self):
        return [b for b in self.builders if b and b.winfo_exists()]

    def load_module_from_path(self, path: pathlib.Path):
        """
        ⚡ SYSTEM ONLY: Dynamically imports a Python module and finds GUI classes.
        Returns:
            type: The first suitable class reference found, or None.
        """
        # 핫픽스 (Hotfix): Ensure project root is in sys.path for reliable imports.
        if str(GLOBAL_PROJECT_ROOT) not in sys.path:
            sys.path.insert(0, str(GLOBAL_PROJECT_ROOT))

        try:
            matrix_log("ui", "gui_builder", "load_module_from_path", f"📂 Loading GUI module from: {path.name}", "DEBUG")
            # ⚡ OPTIMIZATION: Derive package name to support relative imports
            # Example: 'oaGui/Assets.Assets.right_50.bottom_90.2_monitors.1588_PTP_Monitor.ptp_monitor'
            try:
                rel_path = path.resolve().relative_to(GLOBAL_PROJECT_ROOT)
                package_parts = list(rel_path.with_suffix("").parts)
                module_full_name = ".".join(package_parts)
            except ValueError:
                # Fallback if path is outside project root
                module_full_name = path.stem

            spec = importlib.util.spec_from_file_location(module_full_name, path)
            if not spec or not spec.loader:
                matrix_log("ui", "gui_builder", "load_module_from_path", f"❌ Failed to create spec for {path.name}", "ERROR")
                return None
                
            module = importlib.util.module_from_spec(spec)
            # ⚡ ESSENTIAL: Register the full module name so relative imports work
            sys.modules[module_full_name] = module
            spec.loader.exec_module(module)

            # ⚡ ENHANCEMENT: Prioritize explicit factory function
            if hasattr(module, "get_gui_class"):
                matrix_log("ui", "gui_builder", "load_module_from_path", f"✅ Found get_gui_class() in {path.name}", "SUCCESS")
                return getattr(module, "get_gui_class")()

            # Fallback: Find a suitable class (inherits from Frame)
            for name, obj in inspect.getmembers(module):
                if (
                    inspect.isclass(obj)
                    and (issubclass(obj, tk.Frame) or issubclass(obj, ttk.Frame))
                    and obj is not tk.Frame
                    and obj is not ttk.Frame
                    and obj.__module__ == module_full_name  # Ensure it's defined in THIS module
                ):
                    matrix_log("ui", "gui_builder", "load_module_from_path", f"✅ Found class {name} in {path.name}", "SUCCESS")
                    return obj
            
            if path.name not in ["Entry.py", "__init__.py"] and not path.name.startswith("test_"):
                matrix_log("ui", "gui_builder", "load_module_from_path", f"⚠️ No suitable GUI class found in {path.name}", "WARNING")
            return None
        except Exception as e:
            vocal_capture("BUILDER", f"Failed to load module from {path}")
            return None

    def instantiate_widget(self, widget_class, parent_widget, path_ref):
        """
        ⚡ UI ONLY: Instantiates a widget class into the parent frame.
        """
        config_dict = {
            "theme_colors": self.theme_colors,
            "state_mirror_engine": self.state_mirror_engine,
            "subscriber_router": self.subscriber_router,
            "mqtt_connection_manager": getattr(self.app_instance, 'mqtt_connection_manager', None),
            "app_instance": self.app_instance,
        }
        
        # ⚡ OPTIMIZATION: Wrap pure Python modules in a DynamicGuiBuilder
        builder = DynamicGuiBuilder(parent_widget, json_path=None, config=config_dict)
        self.builders.append(builder)
        
        # ⚡ ATTACHMENT: Manually attach based on parent's geometry manager
        try:
            if parent_widget.grid_slaves():
                 builder.grid(row=0, column=0, sticky="nsew")
            else:
                 builder.pack(fill=tk.BOTH, expand=True)
        except tk.TclError:
             # Fallback if both fail or parent is in a weird state
             builder.pack(fill=tk.BOTH, expand=True)

        builder.start()
        config_dict["builder_instance"] = builder
        
        # Instantiate the actual Python GUI
        try:
            # 🔍 FORENSIC: Log instantiation attempt for debugging
            matrix_log("ui", "gui_builder", "instantiate_widget", 
                       f"🔨 Instantiating {widget_class.__name__} (Parent: {parent_widget})", "DEBUG")

            instance = widget_class(builder.scroll_frame, config=config_dict, json_path=None)

            # Pack the instance into the builder's scrollable area
            if hasattr(instance, "pack"):
                instance.pack(fill=tk.BOTH, expand=True)
            elif hasattr(instance, "grid"):
                instance.grid(row=0, column=0, sticky="nsew")
        except Exception as e:
            matrix_log("ui", "gui_builder", "instantiate_widget", 
                       f"🛑 [ERROR] Failed to instantiate {widget_class.__name__}: {e}", "ERROR")
            # We return the builder even on failure so the UI skeleton remains intact
        
        return builder

    def load_and_instantiate_gui(
        self, path: pathlib.Path, parent_widget, class_filter=None
    ):
        """
        Loads a module/JSON from a path and builds the UI.
        Refactored for Modular SRP.
        """
        python_path = None
        json_path = None

        path_str = str(path)
        if path.is_dir():
            try:
                # ⚡ OPTIMIZATION: Single os.scandir pass
                found_json = []
                found_py = []
                with os.scandir(path_str) as it:
                    for entry in it:
                        if entry.is_file() and not entry.name.startswith("__") and entry.name != "layout.json":
                            if entry.name.endswith(".json"):
                                found_json.append(pathlib.Path(entry.path))
                            elif entry.name.endswith(".py"):
                                found_py.append(pathlib.Path(entry.path))
                
                if found_json: json_path = sorted(found_json)[0]
                elif found_py: python_path = sorted(found_py)[0]
                else: return None
            except (FileNotFoundError, PermissionError) as e: 
                logger.warning(f"ModuleLoader: Cannot access directory {path_str}: {e}")
                return None

        elif path.is_file():
            if path.suffix == ".json" and path.name != "layout.json": json_path = path
            elif path.suffix == ".py" and not path.name.startswith("__"): python_path = path
            else: return None
        else: return None

        # --- SRP REFACTOR: Handle Python Path ---
        if python_path:
            # Step 1: Load module references
            target_class = self.load_module_from_path(python_path)
            
            if target_class:
                # Step 2: Instantiate UI tree
                return self.instantiate_widget(target_class, parent_widget, python_path)
            return None

        # --- Handle JSON Path ---
        if json_path:
            try:
                config_dict = {
                    "theme_colors": self.theme_colors,
                    "state_mirror_engine": self.state_mirror_engine,
                    "subscriber_router": self.subscriber_router,
                    "app_instance": self.app_instance,
                    "json_path": str(json_path),
                }
                base_topic = generate_topic_path_from_filepath(json_path, GLOBAL_PROJECT_ROOT)
                config_dict["base_mqtt_topic_from_path"] = base_topic
                
                instance = UniversalGuiLoader(parent=parent_widget, json_path=str(json_path), config=config_dict)
                self.builders.append(instance)
                matrix_log("UI", "GUI_MANAGER", inspect.currentframe().f_code.co_name, f"🏗️🪟✨{json_path}!", level="SUCCESS")
                return instance
            except Exception as e:
                vocal_capture("UI", f"Error instantiating UniversalGuiLoader for '{json_path}'")
                return None

        return None
