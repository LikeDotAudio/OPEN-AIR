# managers/yak_manager/yak_command_builder.py
#
# This file (yak_command_builder.py) provides functionality to build SCPI commands by filling placeholders in a template with values from inputs.
# A complete and comprehensive pre-amble that describes the file and the functions within.
# The purpose is to provide clear documentation and versioning.
#
# The hash calculation drops the leading zero from the hour (e.g., 08 -> 8)
# As the current hour is 20, no change is needed.

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


import os
import inspect
import orjson
import pathlib
import tkinter as tk

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True    # Set to False in production, True for dev on this file
from oaLogging.logger import initialize_logging, set_log_directory
from loguru import logger

from oaConfiguration.config_reader import Config

app_constants = Config.get_instance()

from oaOchestration.project_paths import GLOBAL_PROJECT_ROOT
from oaGuiManager.loader.gui_from_json import UniversalGuiLoader


def fill_scpi_placeholders(scpi_command_template: str, Input: dict):
    """
    Takes an SCPI command template and replaces placeholders with values from inputs.
    """
    current_function_name = inspect.currentframe().f_code.co_name
    if LOCAL_DEBUG: logger.debug(f"🔍🔵 Entering {current_function_name} to fill SCPI placeholders.")

    filled_command = scpi_command_template

    if Input:
        for key, details in Input.items():
            placeholder = f"<{key}>"
            value_to_substitute = str(details.get("value", ""))

            # --- NEW FIX: Replace the placeholder value with a single double quote for the path terminator ---
            filled_command = filled_command.replace('"', '"')

            if placeholder == "<path_terminator>" and placeholder in filled_command:
                filled_command = filled_command.replace(placeholder, '"')
                value_to_substitute = '"'

            if placeholder == "<path_starter>" and placeholder in filled_command:
                filled_command = filled_command.replace(placeholder, '"')
                value_to_substitute = '"'

            if placeholder in filled_command:
                filled_command = filled_command.replace(
                    placeholder, value_to_substitute
                )
                if LOCAL_DEBUG: logger.debug(f"🔁 Replaced placeholder '{placeholder}' with value '{value_to_substitute}'.")
    if LOCAL_DEBUG: logger.success(f"✅ Filled SCPI Command: {filled_command}")
    return filled_command


import oaOchestration.project_paths as app_paths

class YakFleetCommandBuilder:
    def __init__(self, mqtt_connection_manager, subscriber_router):
        self.mqtt_manager = mqtt_connection_manager
        self.subscriber_router = subscriber_router
        self.fleet_path = app_paths.STATE_VISA_FLEET_JSON_PATH

    def process_fleet(self):
        """
        Reads the fleet data and loads the command tabs for each found device.
        """
        if not self.fleet_path.exists():
            logger.error(f"❌ Fleet file not found: {self.fleet_path}")
            return

        try:
            with open(self.fleet_path, "rb") as f:
                fleet_data = orjson.loads(f.read())
            
            if LOCAL_DEBUG: logger.debug(f"🚀 YakFleetCommandBuilder: Processing fleet data from {self.fleet_path}...")

            # Iterate categories (e.g., Spectrum, DMM)
            for category, cat_data in fleet_data.items():
                if LOCAL_DEBUG: logger.debug(f"📂 Processing Category: {category}")
                yak_data = cat_data.get("YAK", {})
                
                # Iterate Models (e.g., 34401A, N9340B)
                for model, model_data in yak_data.items():
                    if model == "Unknown": continue
                    
                    if LOCAL_DEBUG: logger.debug(f"🔍 Searching for YAK tabs for Model: {model}...")

                    # Search for the specific device directory
                    # Structure: oaGuiDefinitions/left_50/top_100/<Category>/10_YAK/<Any_Number>_<Model>
                    # We use a glob to be flexible with the Category folder name and the Model prefix
                    search_pattern = f"oaGuiDefinitions/left_50/top_100/*/10_YAK/*_{model}"
                    found_dirs = list(GLOBAL_PROJECT_ROOT.glob(search_pattern))
                    
                    if not found_dirs:
                        if LOCAL_DEBUG: logger.debug(f"⚠️ No YAK directory found for model {model}")
                        continue
                    
                    for device_dir in found_dirs:
                        if LOCAL_DEBUG: logger.success(f"✅ Found device directory: {device_dir}")
                        self._load_tabs_for_device(device_dir, model)
            
            if LOCAL_DEBUG: logger.debug("🏁 YakFleetCommandBuilder: Fleet processing complete.")

        except Exception as e:
            if LOCAL_DEBUG:
                logger.exception("❌ Error processing fleet")

    def _load_tabs_for_device(self, device_dir, model):
        """
        Recursively finds and loads all JSON tabs in the device directory.
        Uses a staggered queue to prevent GUI freeze.
        """
        json_files = sorted(list(device_dir.rglob("*.json")))
        
        if not json_files:
             if LOCAL_DEBUG: logger.debug(f"⚠️ No JSON tabs found in {device_dir}")
             return

        if self.app_instance and hasattr(self.app_instance, 'root'):
            parent = self.app_instance.root
        else:
            if LOCAL_DEBUG: logger.debug("⚠️ No app_instance root found, skipping staggered GUI load.")
            return

        hidden_window = tk.Toplevel(parent)
        hidden_window.withdraw() # Invisible
        hidden_window.title(f"Yak Builder - {model}")

        # Start the staggered loading process
        self._process_staggered_queue(hidden_window, json_files, model)

    def _process_staggered_queue(self, hidden_window, queue, model):
        """Processes the next JSON file in the queue ONLY after the previous one completes."""
        if not queue:
            # All tabs loaded for this device. Schedule cleanup.
            if LOCAL_DEBUG: logger.success(f"✅ Serial load complete for {model}.")
            hidden_window.after(5000, lambda: self._cleanup_window(hidden_window, model))
            return

        json_path = queue.pop(0)
        try:
            if LOCAL_DEBUG: logger.debug(f"🐂 Serial Loading: {json_path.name}")
            
            # Define completion callback to trigger next item in queue
            def on_tab_complete():
                # Schedule next load with a small gap for breathing room
                hidden_window.after(100, lambda: self._process_staggered_queue(hidden_window, queue, model))

            UniversalGuiLoader(
                hidden_window, 
                str(json_path), 
                config={
                    "app_instance": self.app_instance, 
                    "state_mirror_engine": getattr(self.app_instance, 'state_mirror_engine', None),
                    "subscriber_router": getattr(self.app_instance, 'subscriber_router', None),
                    "on_complete": on_tab_complete # PASS THE CALLBACK
                }
            )
        except Exception as e:
            if LOCAL_DEBUG:
                logger.exception("❌ Failed to load tab {json_path.name}")
            # Continue queue on failure
            hidden_window.after(100, lambda: self._process_staggered_queue(hidden_window, queue, model))

    def _cleanup_window(self, window, model):
        window.destroy()
        if LOCAL_DEBUG: logger.debug(f"🧹 Cleaned up builder window for {model}")