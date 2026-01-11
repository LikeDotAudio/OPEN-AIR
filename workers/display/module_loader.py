# display/module_loader.py
#
# Handles dynamic loading of Python modules and instantiation of GUI classes.
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
# Version 20250821.200641.1

import os
import inspect
import sys
import importlib.util
import pathlib
import tkinter as tk  # Explicitly import tkinter as tk
from tkinter import ttk, Frame
from managers.configini.config_reader import Config
from workers.mqtt.mqtt_topic_utils import generate_topic_path_from_filepath
from display.gui_from_json import UniversalGuiLoader
from workers.setup.worker_project_paths import GLOBAL_PROJECT_ROOT

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

    # Initializes the ModuleLoader.
    # This constructor stores references to theme colors, the state mirror engine,
    # and the subscriber router, which are necessary for dynamically loaded GUI components.
    # Inputs:
    #     theme_colors: A dictionary of theme-specific colors.
    #     state_mirror_engine: The engine for MQTT state synchronization.
    #     subscriber_router: The MQTT subscriber router.
    # Outputs:
    #     None.
    def __init__(self, theme_colors, state_mirror_engine=None, subscriber_router=None, app_instance=None):
        self.theme_colors = theme_colors
        self.state_mirror_engine = state_mirror_engine
        self.subscriber_router = subscriber_router
        self.app_instance = app_instance


    def load_and_instantiate_gui(
        self, path: pathlib.Path, parent_widget, class_filter=None
    ):
        """
        Loads a module from a given path and instantiates the GUI class.
        """
        current_function_name = inspect.currentframe().f_code.co_name

        json_path = None

        if path.is_dir():
            gui_files_in_dir = sorted(
                [
                    f
                    for f in path.iterdir()
                    if f.is_file() and f.name.startswith("gui_") and f.suffix == ".json"
                ]
            )
            if gui_files_in_dir:
                json_path = gui_files_in_dir[0]
            else:
                return None
        elif path.is_file() and path.name.startswith("gui_") and path.suffix == ".json":
            json_path = path
        else:
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

                # Generate and add the base MQTT topic from the module's path
                base_topic = generate_topic_path_from_filepath(
                    json_path, GLOBAL_PROJECT_ROOT
                )
                config_dict["base_mqtt_topic_from_path"] = base_topic
                
                instance = UniversalGuiLoader(
                    parent=parent_widget,
                    json_path=str(json_path),
                    config=config_dict,
                )

                if app_constants.global_settings["debug_enabled"]:
                    debug_logger(
                        message=f"✨ UniversalGuiLoader materialized successfully for {json_path}!",
                        **_get_log_args(),
                    )
                return instance
            except Exception as e:
                if app_constants.global_settings["debug_enabled"]:
                    debug_logger(
                        message=f"❌ The magic falters! Error instantiating UniversalGuiLoader for '{json_path}': {e}.",
                        **_get_log_args(),
                    )
                return None

        return None