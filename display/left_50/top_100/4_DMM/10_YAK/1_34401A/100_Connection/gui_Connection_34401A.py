#A plug-and-play GUI wrapper that dynamically resolves its config. 
# Decoupled from MQTT requirements for initial render to prevent stalling.
# Includes robust error handling, forced rendering, and graceful failure modes.
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
# Version 20251229.1715.2

import os
import pathlib
import orjson
import tkinter as tk
from tkinter import ttk
import inspect
import traceback # Added for detailed forensics
from typing import Dict, Any # Added for type hinting

# --- Protocol: Integration Layer ---
from workers.builder.dynamic_gui_builder import DynamicGuiBuilder
from workers.logger.logger import debug_logger
from workers.setup.config_reader import Config # Import the Config class
from workers.logger.log_utils import _get_log_args 

# Globals
app_constants = Config.get_instance() # Get the singleton instance
current_version = "20251229.1715.1"
current_version_hash = 32806991192 

# --- Protocol: Global Variables ---
current_file = f"{os.path.basename(__file__)}"
current_path = pathlib.Path(__file__).resolve()

# Automatically turns 'gui_yak_bandwidth' into 'OPEN-AIR/yak/bandwidth'
module_name = current_path.stem.replace('gui_', '')

class GenericInstrumentGui(tk.ttk.Frame):
    """
    A generic GUI wrapper that loads a JSON configuration to build its interface.
    Now safely handles arguments from ModuleLoader and fails gracefully.
    """
    def __init__(self, parent, json_path=None, config=None, **kwargs):
        """
        Initialize the Generic Instrument GUI.

        Args:
            parent: The parent widget.
            json_path (str, optional): Path to the JSON config file.
            config (dict, optional): Configuration dictionary.
            **kwargs: Additional arguments for the Frame.
        """
        # 1. Initialize Parent Frame (Cleanly!)
        super().__init__(parent, **kwargs)

        # 2. Absorb Arguments (Priority: Passed Args > Global Calculation)
        self.json_path = json_path
        self.config_data = config if config else {}

        # Fallback if json_path wasn't passed (though ModuleLoader should pass it)
        if not self.json_path:
             self.json_path = current_path.with_suffix('.json')
        
        # Ensure json_path is a Path object
        if isinstance(self.json_path, str):
            self.json_path = pathlib.Path(self.json_path)

        # 3. Extract Core Dependencies
        self.state_mirror_engine = self.config_data.get('state_mirror_engine')
        self.subscriber_router = self.config_data.get('subscriber_router')
        
        # 4. Initialize UI
        self._init_ui()

    def _init_ui(self):
        current_function_name = inspect.currentframe().f_code.co_name
        
        if app_constants.global_settings['debug_enabled']:
            debug_logger(
                message=f"🧪  Entering '{current_function_name}' for module '{module_name}'! Target JSON: {self.json_path}",
                **_get_log_args()
            )

        # Create a status label for feedback during loading
        # Make it BIG and clear so we know it's trying to do something
        self.status_label = ttk.Label(
            self, 
            text=f"⏳ Initializing {module_name}...\nStand by for temporal insertion...", 
            foreground="orange",
            justify="center",
            font=("Consolas", 10, "italic")
        )
        self.status_label.pack(fill="both", expand=True, pady=20)

        # CRITICAL: Force the GUI to update NOW so the user sees the label 
        # BEFORE we risk hanging the thread with the builder!
        self.update_idletasks()

        # Defer construction to allow the frame to render first (avoids UI freezing)
        # This also isolates the builder crash from the main thread loop
        if app_constants.global_settings['debug_enabled']:
            debug_logger(
                message=f"⏳ UI Placeholder rendered. Scheduling construction in 50ms...",
                **_get_log_args()
            )
            
        self.after(50, self._construct_dynamic_gui)

    def _construct_dynamic_gui(self):
        try:
            if app_constants.global_settings['debug_enabled']:
                debug_logger(
                    message=f"🏗️ Starting construction sequence for {module_name}...",
                    **_get_log_args()
                )

            # 1. Validate File Existence
            if not self.json_path.exists():
                raise FileNotFoundError(f"The Blueprint is missing! Cannot find JSON at: {self.json_path}")

            processed_path = str(self.json_path)
            
            if app_constants.global_settings['debug_enabled']:
                debug_logger(
                    message=f"🚀 [Liftoff] Validated path. Passing control to DynamicGuiBuilder...",
                    **_get_log_args()
                )
            
            # --- The Main Event: Dynamic Builder ---
            self.dynamic_gui = DynamicGuiBuilder(
                parent=self,
                json_path=processed_path,
                config=self.config_data # Pass the full config dictionary here
            )
            
            # If we reach here, the builder succeeded!
            if app_constants.global_settings['debug_enabled']:
                debug_logger(
                    message=f"✅ Builder returned success! Destroying status label...",
                    **_get_log_args()
                )
                
            self.status_label.destroy()
            
            if app_constants.global_settings['debug_enabled']:
                 debug_logger(
                    message=f"✅ It works! {module_name} is online and functioning within normal parameters!",
                    **_get_log_args()
                )

        except Exception as e:
            # --- GRACEFUL FAILURE PROTOCOL ---
            # 1. Capture the full forensic report (Traceback)
            tb = traceback.format_exc()
            
            # 2. Display the error visually on the GUI (Red Screen of Warning)
            error_header = f"❌ CRITICAL FAILURE in {module_name}"
            error_body = f"{e}"
            
            if self.winfo_exists():
                self.status_label.config(
                    text=f"{error_header}\n\n{error_body}", 
                    foreground="red", 
                    font=("Consolas", 10, "bold"),
                    wraplength=self.winfo_width() - 20, # Dynamic wrap
                    justify="center"
                )
            
            # 3. Log the disaster with maximum detail
            if app_constants.global_settings['debug_enabled']:
                debug_logger(
                    message=f"❌🔴  The wrapper has failed to contain the builder! {e}\n\n🕵️ FORENSIC TRACE:\n{tb}",
                    **_get_log_args()
                )

    def _on_tab_selected(self, *args, **kwargs):
        """
        Called by the grand orchestrator (Application) when this tab is brought to focus.
        Using *args to swallow any positional events or data passed by the orchestrator.
        """
        current_function_name = inspect.currentframe().f_code.co_name
        
        if app_constants.global_settings['debug_enabled']:
            debug_logger(
                message=f"🖥️🔵 Tab '{module_name}' activated! Stand back, I'm checking the data flow!",
                **_get_log_args()
            )
        # Add logic here if specific refresh actions are needed on tab focus
        pass