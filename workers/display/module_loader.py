# workers/display/module_loader.py
#
# Handles dynamic loading of Python modules and instantiation of GUI classes.
# FIXED: Now correctly passes the JSON path (not the Python path) to the GUI classes.
#
# Author: Anthony Peter Kuzub
# Version: 20251229.1755.1

import os
import inspect
import sys
import importlib.util
import pathlib
import tkinter as tk  # Explicitly import tkinter as tk
from tkinter import ttk, Frame
from managers.configini.config_reader import Config

# Globals
app_constants = Config.get_instance()  # Get the singleton instance
from workers.logger.logger import debug_logger  # Import the global debug_log
from workers.logger.log_utils import _get_log_args

# Globals for Versioning
current_version = "20251229.1755.1"
current_version_hash = 95217822164

# Attempt to import PIL/ImageTk, setting a flag if successful.
try:
    from PIL import ImageTk, Image

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

    class ImageTk:
        pass

    class Image:
        pass


class ModuleLoader:
    """
    Handles dynamic loading of Python modules and instantiation of GUI classes.
    """

    def __init__(self, theme_colors, state_mirror_engine=None, subscriber_router=None):
        self.theme_colors = theme_colors
        self.state_mirror_engine = state_mirror_engine
        self.subscriber_router = subscriber_router

    def _load_module(self, module_path: pathlib.Path, module_name: str):
        """
        Dynamically loads a Python module from a given path.
        """
        current_function_name = inspect.currentframe().f_code.co_name
        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"🔬🟢 Preparing to awaken a module! Loading from '{module_path}' with name '{module_name}'.",
                **_get_log_args(),
            )

        try:
            # Using spec_from_file_location for robust loading
            spec = importlib.util.spec_from_file_location(module_name, str(module_path))
            if spec is None:
                if app_constants.global_settings["debug_enabled"]:
                    debug_logger(
                        message=f"❌ Catastrophic failure! Could not forge a module spec for '{module_path}'. Aborting mission!",
                        **_get_log_args(),
                    )
                return None

            module = importlib.util.module_from_spec(spec)

            # Ensure 'tk' and 'ttk' are available in the module's global namespace
            # This is a more robust approach than attempting to modify __builtins__
            # or relying on its presence as a dict or the builtins module itself.
            module.tk = tk
            module.ttk = ttk
            module.os = os

            spec.loader.exec_module(module)

            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"🔬✅ Module '{module_name}' from '{module_path}' has sprung to life!",
                    **_get_log_args(),
                )
            return module
        except Exception as e:
            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"❌ The module, it resists! Error loading module '{module_path}': {e}.",
                    **_get_log_args(),
                )
            return None

    def instantiate_gui_class(
        self,
        module,
        parent_widget,
        class_filter=None,
        module_file_path: pathlib.Path = None,
    ):
        """
        Finds and instantiates the first suitable GUI class.
        """
        current_function_name = inspect.currentframe().f_code.co_name

        target_class = None
        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj) and (
                issubclass(obj, (ttk.Frame, Frame))
                and obj.__module__ == module.__name__
            ):

                if class_filter is None:
                    target_class = obj
                    break
                elif name == class_filter:
                    target_class = obj
                    break

        if target_class:
            try:
                config_dict = {
                    "theme_colors": self.theme_colors,
                    "state_mirror_engine": self.state_mirror_engine,
                    "subscriber_router": self.subscriber_router,
                }

                json_config_path_str = None
                if module_file_path:
                    # ✅ CRITICAL FIX: Ensure we point to the .json file, not the .py file!
                    json_config_path = module_file_path.with_suffix(".json")
                    json_config_path_str = str(json_config_path)
                    config_dict["json_path"] = json_config_path_str

                # Instantiate the class
                # ✅ CRITICAL FIX: Pass 'json_config_path_str' as the second argument!
                instance = target_class(
                    parent_widget, json_config_path_str, config_dict
                )

                if app_constants.global_settings["debug_enabled"]:
                    debug_logger(
                        message=f"✨ Class '{target_class.__name__}' materialized successfully!",
                        **_get_log_args(),
                    )
                return instance
            except Exception as e:
                if app_constants.global_settings["debug_enabled"]:
                    debug_logger(
                        message=f"❌ The magic falters! Error instantiating class '{target_class.__name__}': {e}.",
                        **_get_log_args(),
                    )
                return None
        return None

    def load_and_instantiate_gui(
        self, path: pathlib.Path, parent_widget, class_filter=None
    ):
        """
        Loads a module from a given path and instantiates the GUI class.
        """
        current_function_name = inspect.currentframe().f_code.co_name

        module_path = None
        module_name = None

        if path.is_dir():
            gui_files_in_dir = sorted(
                [
                    f
                    for f in path.iterdir()
                    if f.is_file() and f.name.startswith("gui_") and f.suffix == ".py"
                ]
            )
            if gui_files_in_dir:
                module_path = gui_files_in_dir[0]
                module_name = module_path.stem
            else:
                return None
        elif path.is_file() and path.name.startswith("gui_") and path.suffix == ".py":
            module_path = path
            module_name = path.stem
        else:
            return None

        if module_path and module_name:
            module = self._load_module(module_path, module_name)
            if module:
                instance = self.instantiate_gui_class(
                    module,
                    parent_widget,
                    class_filter=class_filter,
                    module_file_path=module_path,
                )
                return instance

        return None
