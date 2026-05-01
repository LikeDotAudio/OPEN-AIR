# oaGui/FileReaders/module_loader.py
# Author: Anthony Peter Kuzub
# Version: 20260218.Optimization.2
#
# Description: Handles dynamic loading of Python modules and instantiation of GUI classes.

import inspect
import os
import pathlib
import tkinter as tk

from oaLogging.Entry import logger, vocal_capture
from oaLogging.Methods.matrix_gate import matrix_log
from oaComProtocols.oaComMQTT.Methods.mqtt_topic_utils import generate_topic_path_from_filepath
from oaGui.FileReaders.gui_from_json import UniversalGuiLoader
from oaOchestration.Core.path_initializer import GLOBAL_PROJECT_ROOT
from oaGui.Methods.python_module_loader import PythonModuleLoader
from oaGui.Managers.widget_instantiator import WidgetInstantiator

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
        self.instantiator = WidgetInstantiator(
            theme_colors=theme_colors,
            state_mirror_engine=state_mirror_engine,
            subscriber_router=subscriber_router,
            app_instance=app_instance
        )

    def get_all_builders(self):
        return [b for b in self.instantiator.builders if b and b.winfo_exists()]

    def load_module_from_path(self, path: pathlib.Path):
        """
        ⚡ SYSTEM ONLY: Dynamically imports a Python module and finds GUI classes.
        """
        return PythonModuleLoader.load(path)

    def instantiate_widget(self, widget_class, parent_widget, path_ref):
        """
        ⚡ UI ONLY: Instantiates a widget class into the parent frame.
        """
        return self.instantiator.instantiate(widget_class, parent_widget)

    def load_and_instantiate_gui(
        self, path: pathlib.Path, parent_widget, class_filter=None
    ):
        """
        Loads a module/JSON from a path and builds the UI.
        """
        python_path = None
        json_path = None

        path_str = str(path)
        if path.is_dir():
            try:
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

        if python_path:
            target_class = self.load_module_from_path(python_path)
            if target_class:
                return self.instantiate_widget(target_class, parent_widget, python_path)
            return None

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
                self.instantiator.builders.append(instance)
                matrix_log("UI", "GUI_MANAGER", inspect.currentframe().f_code.co_name, f"🏗️🪟✨{json_path}!", level="SUCCESS")
                return instance
            except Exception:
                vocal_capture("UI", f"Error instantiating UniversalGuiLoader for '{json_path}'")
                return None

        return None
