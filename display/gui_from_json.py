# display/gui_from_json.py
#
# The Universal GUI Wrapper.
# This module acts as the "Universal Capacitor," capable of loading ANY
# JSON configuration in the system and rendering it via the DynamicGuiBuilder.
# It eliminates the need for individual python wrappers for every instrument.
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
# Version 20260111.1510.1

import os
import pathlib
import tkinter as tk
from tkinter import ttk
import inspect
import traceback
from typing import Dict, Any, Optional

# --- Protocol: Integration Layer ---
from workers.builder.dynamic_gui_builder import DynamicGuiBuilder
from workers.logger.logger import debug_logger
from managers.configini.config_reader import Config
from workers.logger.log_utils import _get_log_args

# Globals
app_constants = Config.get_instance()
current_version = "20260111.1510.1"
current_version_hash = 98274115101  # Calculated Hash

class UniversalGuiLoader(tk.ttk.Frame):
    """
    The Universal Wrapper.
    It takes a JSON path and builds the interface.
    """

    def __init__(self, parent, json_path: str, config: Optional[Dict[str, Any]] = None, **kwargs):
        """
        Initialize the Universal GUI Loader.

        Args:
            parent: The parent widget (usually a Tab or Window).
            json_path (str): THE CRITICAL COMPONENT. The absolute path to the JSON blueprint.
            config (dict, optional): Shared application configuration (app_instance, routers, etc.).
            **kwargs: Standard Tkinter arguments.
        """
        super().__init__(parent, **kwargs)

        # 1. Absorb Arguments
        self.json_path = pathlib.Path(json_path)
        self.config_data = config if config else {}
        
        # Extract the module name from the filename for logging (e.g., "frequency" from "gui_frequency.json")
        self.module_name = self.json_path.stem.replace("gui_", "").upper()

        # 2. Extract Core Dependencies (Safety Check)
        self.app = self.config_data.get("app_instance")
        
        # 3. Initialize UI (Start the reactor!)
        self._init_ui()

    def _init_ui(self):
        """Display the loading state and schedule the build."""
        current_function_name = inspect.currentframe().f_code.co_name

        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"🧪 Great Scott! Universal Loader initializing '{self.module_name}'! Target: {self.json_path}",
                **_get_log_args()
            )

        # Visual Feedback: The Loading Spinner
        self.status_label = ttk.Label(
            self,
            text=f"⏳ Constructing {self.module_name}...\nCalculating temporal vectors...",
            foreground="orange",
            justify="center",
            font=("Consolas", 10, "italic"),
        )
        self.status_label.pack(fill="both", expand=True, pady=20)

        # Force render so the user sees the text
        self.update_idletasks()

        # Defer construction to prevent UI freeze (The temporal gap)
        self.after(50, self._construct_dynamic_gui)

    def _construct_dynamic_gui(self):
        """The Main Event: Handing off to the Builder."""
        try:
            # 1. Verification
            if not self.json_path.exists():
                raise FileNotFoundError(f"Blueprint missing! {self.json_path}")

            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"🏗️ Constructing '{self.module_name}' via DynamicGuiBuilder...",
                    **_get_log_args()
                )

            # 2. Execution
            self.dynamic_gui = DynamicGuiBuilder(
                parent=self,
                json_path=str(self.json_path),
                config=self.config_data,
            )

            # 3. Success
            self.status_label.destroy()
            
            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"✅ It works! {self.module_name} is fully operational!",
                    **_get_log_args()
                )

        except Exception as e:
            # 4. Catastrophic Failure Handling
            tb = traceback.format_exc()
            error_msg = f"❌ CRITICAL FAILURE in {self.module_name}\n\n{e}"
            
            # Log it
            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"💥 The Flux Capacitor cracked while building {self.module_name}! {e}\n{tb}",
                    **_get_log_args()
                )

            # Show it
            if self.winfo_exists():
                self.status_label.config(
                    text=error_msg,
                    foreground="red",
                    font=("Consolas", 10, "bold"),
                    wraplength=self.winfo_width() - 20
                )

    def _on_tab_selected(self, *args, **kwargs):
        """Optional hook for tab selection events."""
        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"🖥️🔵 Tab '{self.module_name}' focused. Systems nominal.",
                **_get_log_args()
            )
