## MQTT_TOPIC_FILTER = "OPEN-AIR/configuration/application/Application_Info"










# display/left_50/top_100/tab_1_instrument/sub_tab_2_settings/sub_tab_1_frequency/gui_frequency_1.py
#
# A GUI frame that uses the DynamicGuiBuilder to create widgets for frequency settings.
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
# Version 20251127.000000.1

import os
import inspect
import traceback # Added for detailed forensics
from typing import Dict, Any # Added for type hinting

# --- Protocol: Integration Layer ---
import tkinter as tk
from tkinter import ttk

# --- Module Imports ---
from workers.builder.dynamic_gui_builder import DynamicGuiBuilder
from workers.logger.logger import  debug_logger
from workers.logger.log_utils import _get_log_args 
import pathlib

# --- Global Scope Variables ---
current_version = "20251226.000000.1"
current_version_hash = (20251127 * 0 * 1)
current_file = f"{os.path.basename(__file__)}"
current_path = pathlib.Path(__file__).resolve()
# JSON_CONFIG_FILE = current_path.with_suffix('.json')


class PresetPusherGui(ttk.Frame):
    """
    A container frame that instantiates the DynamicGuiBuilder for the Frequency configuration.
    """
    def __init__(self, parent, json_path=None, config=None, **kwargs):
        """
        Initializes the Frequency frame and the dynamic GUI builder.
        """
        config_from_kwargs = kwargs.pop('config', {}) if config is None else config # Store original config to extract necessary parts
        
        super().__init__(parent, **kwargs)
        self.pack(fill=tk.BOTH, expand=True)

        # Extract state_mirror_engine and subscriber_router from the config dictionary
        self.state_mirror_engine = config_from_kwargs.get('state_mirror_engine')
        self.subscriber_router = config_from_kwargs.get('subscriber_router')

        # Define a default internal configuration
        self.config_data = {
            "Generic_Display_Block": {
                "type": "OcaBlock",
                "description": "Dynamic Content for Application Configuration",
                "fields": {
                    "message": {
                        "type": "_Label",
                        "label_active": f"No specific JSON configuration found for application configuration. Displaying default content."
                    }
                }
            }
        }
        
        # --- Dynamic GUI Builder ---
        # Create an instance of the new, corrected, and modular builder,
        # passing the specific base topic for this GUI component.
        self.dynamic_gui = DynamicGuiBuilder(
            parent=self,
            json_path=None, # No external JSON file to load for this wrapper
            config=self.config_data # Pass ONLY the serializable config data
        )