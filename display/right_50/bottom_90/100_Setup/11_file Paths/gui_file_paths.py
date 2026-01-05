## MQTT_TOPIC_FILTER = "OPEN-AIR/configuration/application/filepaths"
# display/tabs/gui_child_1_pusher.py
#
# A GUI frame for displaying and controlling Presets via MQTT using the modular DynamicGuiBuilder.
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
import tkinter as tk
from tkinter import ttk

# --- Module Imports ---
# It's crucial that this path correctly points to the new modular builder
from workers.builder.dynamic_gui_builder import DynamicGuiBuilder
import pathlib
from typing import Dict, Any # Added for type hinting

# --- Fully Dynamic Resolution ---
current_path = pathlib.Path(__file__).resolve()
# JSON_CONFIG_FILE = current_path.with_suffix('.json') # No longer loading from external JSON

class PresetPusherGui(ttk.Frame):
    """
    A container frame that instantiates the DynamicGuiBuilder for the Presets configuration.
    This replaces the old, monolithic code with a call to the reusable, modular component.
    """
    def __init__(self, parent, json_path=None, config=None, **kwargs):
        """
        Initializes the Presets frame and the dynamic GUI builder.
        """
        config_from_kwargs = kwargs.pop('config', {}) if config is None else config # Store original config to extract necessary parts. If config is passed explicitly, use it.
        super().__init__(parent, **kwargs)
        self.pack(fill=tk.BOTH, expand=True)

        # Extract state_mirror_engine and subscriber_router from the config dictionary
        self.state_mirror_engine = config_from_kwargs.get('state_mirror_engine')
        self.subscriber_router = config_from_kwargs.get('subscriber_router')

        # Define a default internal configuration
        self.config_data = {
            "Generic_Display_Block": {
                "type": "OcaBlock",
                "description": "Dynamic Content for File Paths",
                "fields": {
                    "message": {
                        "type": "_Label",
                        "label_active": f"No specific JSON configuration found for file paths. Displaying default content."
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