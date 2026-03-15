# managers/Display/gui_from_json.py
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

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True    # Set to False in production, True for dev on this file
from workers.logger.logger import initialize_logging, set_log_directory
from loguru import logger

from managers.configini.config_reader import Config

app_constants = Config.get_instance()

# --- Protocol: Integration Layer ---
from workers.builder.builder import DynamicGuiBuilder

# Globals
current_version = "20260111.1510.1"
current_version_hash = 98274115101  # Calculated Hash

class UniversalGuiLoader(tk.Frame):
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
        # Set default background to match theme
        if "bg" not in kwargs and "background" not in kwargs:
            kwargs["bg"] = "#2b2b2b"
        
        super().__init__(parent, **kwargs)

        # 1. Absorb Arguments
        self.json_path = pathlib.Path(json_path)
        self.config_data = config if config else {}
        
        # Extract the module name from the filename for logging (e.g., "frequency" from "gui_frequency.json")
        self.module_name = self.json_path.stem.replace("gui_", "").upper()

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 2. Extract Core Dependencies (Safety Check)
        self.app = self.config_data.get("app_instance")
        
        # 3. Initialize UI (Start the reactor!)
        self._init_ui()

    def _init_ui(self):
        """Skip the loading label and start the build immediately."""
        # Use a minimal delay to ensure the frame is gridded/packed before heavy build
        self.after(1, self._construct_dynamic_gui)

    def _construct_dynamic_gui(self):
        """The Main Event: Handing off to the Builder."""
        try:
            # 1. Verification
            if not self.json_path.exists():
                raise FileNotFoundError(f"Blueprint missing! {self.json_path}")

            if LOCAL_DEBUG: logger.debug(f"🏗️ Constructing '{self.module_name}' via DynamicGuiBuilder...")

            # 2. Execution
            builder_config = self.config_data.copy()
            
            self.dynamic_gui = DynamicGuiBuilder(
                parent=self,
                json_path=str(self.json_path),
                tab_name=self.module_name,
                config=builder_config,
                use_grid=True  # ⚡ Critical: Instruct builder to use grid instead of pack
            )
            self.dynamic_gui.grid(row=0, column=0, sticky="nsew")

            # 3. Success
            if LOCAL_DEBUG: logger.success(f"✅ It works! {self.module_name} is fully operational!")

        except Exception as e:
            # 4. Catastrophic Failure Handling
            tb = traceback.format_exc()
            
            # Log it
            if LOCAL_DEBUG:
                logger.debug(f"💥 The Flux Capacitor cracked while building {self.module_name}! {e}\n{tb}")

            # Show it (Minimal fallback since status_label is gone)
            if self.winfo_exists():
                tk.Label(self, text=f"Error: {e}", fg="red", bg="#2b2b2b").pack(pady=20)

    def _on_tab_selected(self, event):
        """Optional hook for tab selection events."""
        if LOCAL_DEBUG: logger.debug(f"🖥️🔵 Tab '{self.module_name}' focused. Systems nominal.")