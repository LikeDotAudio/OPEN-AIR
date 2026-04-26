import inspect

# 3_Metering/Graphing_Elements.py
# Author: Anthony Peter Kuzub
# Version: 20251229.1715.2
#
# Description: A plug-and-play GUI wrapper that dynamically resolves its config.
import os
import pathlib
import traceback  # Added for detailed forensics
from tkinter import ttk

from loguru import logger

from oaConfigurationManager.FileReaders.config_reader import Config

# --- Protocol: Integration Layer ---
from oaGui.Workers.builder import DynamicGuiBuilder
from oaLogging.Methods.matrix_gate import matrix_log

LOCAL_DEBUG = False



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
        current_function_name = inspect.currentframe().f_code.co_name

        if LOCAL_DEBUG:
            matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"🧪  Entering '{current_function_name}' for module '{module_name}'! Target JSON: {self.json_path}", "DEBUG")

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
        if LOCAL_DEBUG:
            matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "⏳ UI Placeholder rendered. Scheduling construction in 50ms...", "DEBUG")

        self.after(50, self._construct_dynamic_gui)

    def _construct_dynamic_gui(self):
        try:
            if LOCAL_DEBUG:
                matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"🏗️ Starting construction sequence for {module_name}...", "DEBUG")

            # 1. Validate File Existence
            if not self.json_path.exists():
                raise FileNotFoundError(
                    f"The Blueprint is missing! Cannot find JSON at: {self.json_path}"
                )

            processed_path = str(self.json_path)

            if LOCAL_DEBUG:
                matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "🚀 [Liftoff] Validated path. Passing control to DynamicGuiBuilder...", "DEBUG")

            # --- The Main Event: Dynamic Builder ---
            self.dynamic_gui = DynamicGuiBuilder(
                parent=self,
                json_path=processed_path,
                config=self.config_data,  # Pass the full config dictionary here
                use_grid=True,
            )

            # If we reach here, the builder succeeded!
            if LOCAL_DEBUG:
                matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "✅ Builder returned success! Destroying status label...", "SUCCESS")

            self.status_label.destroy()
            self.dynamic_gui.grid(row=0, column=0, sticky="nsew")

            if LOCAL_DEBUG:
                matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"✅ It works! {module_name} is online and functioning within normal parameters!", "SUCCESS")

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
            if LOCAL_DEBUG:
                logger.exception("❌🔴  The wrapper has failed to contain the builder! \n\n🕵️ FORENSIC TRACE:\n{tb}")

    def _on_tab_selected(self, event):
        """
        Called by the grand orchestrator (Application) when this tab is brought to focus.
        """
        current_function_name = inspect.currentframe().f_code.co_name

        if LOCAL_DEBUG:
            matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"🖥️🔵 Tab '{module_name}' activated! Stand back, I'm checking the data flow!", "DEBUG")
        # Add logic here if specific refresh actions are needed on tab focus
        pass
