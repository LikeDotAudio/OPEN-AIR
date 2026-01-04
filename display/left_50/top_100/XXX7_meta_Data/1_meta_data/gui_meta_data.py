## MQTT_TOPIC_FILTER = "OPEN-AIR/configuration/report"

# display/left_50/top_100/XXX7_meta_Data/1_meta_data/gui_meta_data.py
#
# A GUI frame that uses the DynamicGuiBuilder to create widgets for meta-data settings.
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
#
# Version 20251226.000000.1

import os
import inspect
import tkinter as tk
from tkinter import ttk

# --- Module Imports ---
from workers.builder.dynamic_gui_builder import DynamicGuiBuilder
from workers.logger.logger import  debug_logger
from workers.logger.log_utils import _get_log_args 
import pathlib
from managers.configini.config_reader import Config
app_constants = Config.get_instance() # Get the singleton instance

# --- Global Scope Variables ---
current_file_path = pathlib.Path(__file__).resolve()
project_root = current_file_path.parent.parent.parent
current_file = str(current_file_path.relative_to(project_root)).replace("\\", "/")
JSON_CONFIG_FILE = current_file_path.with_suffix('.json')

current_version = "20251226.000000.1"


class MetaDataGui(ttk.Frame):
    """
    A container frame that instantiates the DynamicGuiBuilder for the Frequency configuration.
    """
    def __init__(self, parent, *args, **kwargs):
        """
        Initializes the Frequency frame and the dynamic GUI builder.
        """
        config_data = kwargs.pop('config', None)
        super().__init__(parent, *args, **kwargs)
        self.pack(fill=tk.BOTH, expand=True)

        # --- Dynamic GUI Builder ---
        current_function_name = "__init__"
        debug_logger(
            message=f"🟢️️️🟢 ➡️➡️ {current_function_name} to initialize the MetaDataGui.",
            **_get_log_args()
        )
        try:
            config = {
                ## "base_topic": MQTT_TOPIC_FILTER,
                "log_to_gui_console": None, 
                "log_to_gui_treeview": None  # Assuming no treeview for this component
            }

            self.dynamic_gui = DynamicGuiBuilder(
                parent=self,
                json_path=JSON_CONFIG_FILE,
                config=config
            )
            
        except Exception as e:
            debug_logger(message=f"❌ Error in {current_function_name}: {e}",
                        **_get_log_args()
                        )
            debug_logger(
                message=f"❌🔴 Arrr, the code be capsized! The error be: {e}",
                **_get_log_args()
            )