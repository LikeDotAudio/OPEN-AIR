# display/left_50/top_100/0_Spectrum/10_YAK/3_HPE4411A/2_Amplitude/gui_yak_amplitude.py
#
# This file provides a generic GUI wrapper for instrument control, loading its interface from a JSON configuration.
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
# Version 20260108.150000.1

import os
import pathlib
import orjson
import tkinter as tk
from tkinter import ttk
import inspect
import traceback  # Added for detailed forensics
from typing import Dict, Any  # Added for type hinting

# --- Protocol: Integration Layer ---
from workers.builder.dynamic_gui_builder import DynamicGuiBuilder
from workers.logger.logger import debug_logger
from managers.configini.config_reader import Config
from workers.logger.log_utils import _get_log_args

# Globals
app_constants = Config.get_instance()  # Get the singleton instance
current_version = "20251229.1715.1"
current_version_hash = 32806991192

# --- Protocol: Global Variables ---
current_file = f"{os.path.basename(__file__)}"
current_path = pathlib.Path(__file__).resolve()

# Automatically turns 'gui_yak_bandwidth' into 'OPEN-AIR/yak/bandwidth'
module_name = current_path.stem.replace("gui_", "")


class GenericInstrumentGui(ttk.Frame):
    """
    A generic GUI wrapper that loads a JSON configuration to build its interface.
    Now safely handles arguments from ModuleLoader and fails gracefully.
    """

    def __init__(self, parent, json_path=None, config=None, **kwargs):
        """
        Initializes the generic instrument GUI frame.

        This function sets up the main frame for a dynamically generated GUI based on a
        JSON configuration. It establishes the necessary links to core application
        services like state management and data subscription routing. The function is
        designed to be robust, with fallbacks for configuration paths.

        Inputs:
            parent (tk.Widget): The parent tkinter widget that will contain this frame.
            json_path (str, optional): The file path to the JSON file that defines the
                                       GUI layout and widgets. If not provided, it defaults
                                       to a JSON file with the same name as this Python file.
            config (dict, optional): A dictionary containing shared application resources,
                                     primarily the 'state_mirror_engine' for managing
                                     application state and the 'subscriber_router' for
                                     handling data subscriptions.
            **kwargs: Additional keyword arguments that are passed directly to the
                      underlying ttk.Frame constructor.

        Outputs:
            None: This is a constructor and does not have a return value.
        """
        # 1. Initialize Parent Frame (Cleanly!)
        super().__init__(parent, **kwargs)

        # 2. Absorb Arguments (Priority: Passed Args > Global Calculation)
        self.json_path = json_path
        self.config_data = config if config else {}

        # Fallback if json_path wasn't passed (though ModuleLoader should pass it)
        if not self.json_path:
            self.json_path = current_path.with_suffix(".json")

        # Ensure json_path is a Path object
        if isinstance(self.json_path, str):
            self.json_path = pathlib.Path(self.json_path)

        # 3. Extract Core Dependencies
        self.state_mirror_engine = self.config_data.get("state_mirror_engine")
        self.subscriber_router = self.config_data.get("subscriber_router")

        # 4. Initialize UI
        self._init_ui()

    def _init_ui(self):
        """
        Initializes the user interface elements for the frame.

        This function sets up the initial state of the GUI. It displays a temporary
        status message to inform the user that the module is loading. To prevent the
        main application from freezing, it schedules the more intensive task of
        building the full dynamic GUI to run shortly after the initial frame is
        rendered.

        Inputs:
            None

        Outputs:
            None
        """
        current_function_name = inspect.currentframe().f_code.co_name

        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"🧪  Entering '{current_function_name}' for module '{module_name}'! Target JSON: {self.json_path}",
                **_get_log_args(),
            )

        # Create a status label for feedback during loading
        # Make it BIG and clear so we know it's trying to do something
        self.status_label = ttk.Label(
            self,
            text=f"⏳ Initializing {module_name}...\nStand by for temporal insertion...",
            foreground="orange",
            justify="center",
            font=("Consolas", 10, "italic"),
        )
        self.status_label.pack(fill="both", expand=True, pady=20)

        # CRITICAL: Force the GUI to update NOW so the user sees the label
        # BEFORE we risk hanging the thread with the builder!
        self.update_idletasks()

        # Defer construction to allow the frame to render first (avoids UI freezing)
        # This also isolates the builder crash from the main thread loop
        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"⏳ UI Placeholder rendered. Scheduling construction in 50ms...",
                **_get_log_args(),
            )

        self.after(50, self._construct_dynamic_gui)

    def _construct_dynamic_gui(self):
        """
        Constructs the dynamic GUI from the JSON configuration.

        This function is responsible for the main logic of the GUI creation. It reads
        the specified JSON file, which contains the blueprint for the interface, and
        uses the DynamicGuiBuilder to instantiate and arrange all the widgets. It
        includes robust error handling to catch issues like a missing JSON file or
        errors during the building process, displaying a clear error message in the
        GUI if a failure occurs.

        Inputs:
            None

        Outputs:
            None
        """
        try:
            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"🏗️ Starting construction sequence for {module_name}...",
                    **_get_log_args(),
                )

            # 1. Validate File Existence
            if not self.json_path.exists():
                raise FileNotFoundError(
                    f"The Blueprint is missing! Cannot find JSON at: {self.json_path}"
                )

            processed_path = str(self.json_path)

            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"🚀 [Liftoff] Validated path. Passing control to DynamicGuiBuilder...",
                    **_get_log_args(),
                )

            # --- The Main Event: Dynamic Builder ---
            self.dynamic_gui = DynamicGuiBuilder(
                parent=self,
                json_path=processed_path,
                config=self.config_data,  # Pass the full config dictionary here
            )

            # If we reach here, the builder succeeded!
            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"✅ Builder returned success! Destroying status label...",
                    **_get_log_args(),
                )

            self.status_label.destroy()

            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"✅ It works! {module_name} is online and functioning within normal parameters!",
                    **_get_log_args(),
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
                    wraplength=self.winfo_width() - 20,  # Dynamic wrap
                    justify="center",
                )

            # 3. Log the disaster with maximum detail
            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"❌🔴  The wrapper has failed to contain the builder! {e}\n\n🕵️ FORENSIC TRACE:\n{tb}",
                    **_get_log_args(),
                )

    def _on_tab_selected(self, *args, **kwargs):
        """
        Handles the event when the tab containing this frame is selected.

        This function is a callback that gets triggered when the user clicks on the
        tab for this specific GUI module. It is intended to be a placeholder for any
        logic that needs to run upon tab selection, such as refreshing data or
        updating the UI. Currently, it only logs a debug message.

        Inputs:
            *args: Accepts a variable number of positional arguments, which are
                   passed by the event trigger.
            **kwargs: Accepts a variable number of keyword arguments, which are
                      passed by the event trigger.

        Outputs:
            None
        """
        current_function_name = inspect.currentframe().f_code.co_name

        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"🖥️🔵 Tab '{module_name}' activated! Stand back, I'm checking the data flow!",
                **_get_log_args(),
            )
        # Add logic here if specific refresh actions are needed on tab focus
        pass