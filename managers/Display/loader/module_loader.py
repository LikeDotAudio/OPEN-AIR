# display/module_loader.py
#
# Handles dynamic loading of Python modules and instantiation of GUI classes.
# Refactored for Modular SRP: Separates Dynamic Importing from UI Instantiation.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
# Version 20260218.Optimization.2

import os
import inspect
import sys
import importlib.util
import pathlib
import tkinter as tk
from tkinter import ttk

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True    # Set to False in production, True for dev on this file
from workers.logger.logger import initialize_logging, set_log_directory
from loguru import logger

from managers.configini.config_reader import Config

app_constants = Config.get_instance()

from workers.Command_Router.mqtt.mqtt_topic_utils import generate_topic_path_from_filepath
from managers.Display.loader.gui_from_json import UniversalGuiLoader
from workers.initialization.project_paths import GLOBAL_PROJECT_ROOT
from workers.builder.builder import DynamicGuiBuilder

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

    def load_module_from_path(self, path: pathlib.Path):
        """
        ⚡ SYSTEM ONLY: Dynamically imports a Python module and finds GUI classes.
        Returns:
            type: The first suitable class reference found, or None.
        """
        try:
            module_name = path.stem
            spec = importlib.util.spec_from_file_location(module_name, path)
            if not spec or not spec.loader:
                return None
                
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            # Find a suitable class (inherits from Frame)
            for name, obj in inspect.getmembers(module):
                if (
                    inspect.isclass(obj)
                    and (issubclass(obj, tk.Frame) or issubclass(obj, ttk.Frame))
                    and obj is not tk.Frame
                    and obj is not ttk.Frame
                ):
                    return obj
            return None
        except Exception as e:
            if LOCAL_DEBUG:
                logger.error(f"❌ [IMPORT] Failed to load module {path}: {e}")
            return None

    def instantiate_widget(self, widget_class, parent_widget, path_ref):
        """
        ⚡ UI ONLY: Instantiates a widget class into the parent frame.
        """
        config_dict = {
            "theme_colors": self.theme_colors,
            "state_mirror_engine": self.state_mirror_engine,
            "subscriber_router": self.subscriber_router,
            "app_instance": self.app_instance,
        }
        
        # ⚡ OPTIMIZATION: Wrap pure Python modules in a DynamicGuiBuilder
        builder = DynamicGuiBuilder(parent_widget, json_path=None, config=config_dict)
        config_dict["builder_instance"] = builder
        
        # Instantiate the actual Python GUI
        instance = widget_class(builder.scroll_frame, config=config_dict, json_path=path_ref)
        
        # Pack the instance into the builder's scrollable area
        if hasattr(instance, "pack"):
            instance.pack(fill=tk.BOTH, expand=True)
        elif hasattr(instance, "grid"):
            instance.grid(row=0, column=0, sticky="nsew")
            
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
                        if entry.is_file() and entry.name.startswith("gui_"):
                            if entry.name.endswith(".json"):
                                found_json.append(pathlib.Path(entry.path))
                            elif entry.name.endswith(".py"):
                                found_py.append(pathlib.Path(entry.path))
                
                if found_json: json_path = sorted(found_json)[0]
                elif found_py: python_path = sorted(found_py)[0]
                else: return None
            except (FileNotFoundError, PermissionError): return None

        elif path.is_file() and path.name.startswith("gui_"):
            if path.suffix == ".json": json_path = path
            elif path.suffix == ".py": python_path = path
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
                if LOCAL_DEBUG: logger.success(f"🏗️🪟✨{json_path}!")
                return instance
            except Exception as e:
                if LOCAL_DEBUG: logger.exception(f"❌ Error instantiating UniversalGuiLoader for '{json_path}'")
                return None

        return None
