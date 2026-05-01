# loader/gui_from_json.py
# Author: Anthony Peter Kuzub
# Version: 20260111.1510.1
#
# Description: Universal GUI Loader - Host for Dynamic GUI components.

import inspect
import pathlib
import tkinter as tk
from typing import Any

from loguru import logger

from oaGui.Workers.builder import DynamicGuiBuilder
from oaGui.Core.context.widget_context import WidgetContext
from oaLogging.Methods.matrix_gate import matrix_log

# Globals
current_version = "20260111.1510.1"
current_version_hash = 98274115101  # Calculated Hash

class UniversalGuiLoader(tk.Frame):
    """
    The Universal Wrapper.
    It takes a JSON path and builds the interface.
    """

    def __init__(self, parent, json_path: str, config: dict[str, Any] | None = None, **kwargs):
        """
        Initialize the Universal GUI Loader.
        """
        # Set default background to match theme
        if "bg" not in kwargs and "background" not in kwargs:
            kwargs["bg"] = "#2b2b2b"

        super().__init__(parent, **kwargs)

        # 1. Absorb Arguments
        self.json_path = pathlib.Path(json_path)
        self.config_data = config if config else {}

        # Extract the module name from the filename
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

            matrix_log("UI", "GUI_MANAGER", inspect.currentframe().f_code.co_name,
                       f"🏗️🏗️🏗️ [BUILDER] Constructing '{self.module_name}' via DynamicGuiBuilder...",
                       level="DEBUG")

            # 2. Execution
            self._instantiate_builder()

            # 3. Success
            matrix_log("UI", "GUI_MANAGER", inspect.currentframe().f_code.co_name,
                       f"✅✅✅ [SUCCESS] It works! {self.module_name} is fully operational!",
                       level="SUCCESS")

        except FileNotFoundError as e:
            # 4a. Expected Validation Failure - No noisy traceback
            matrix_log("UI", "GUI_MANAGER", "_construct_dynamic_gui",
                       f"⚠️⚠️⚠️ [VALIDATION] Blueprint missing! Module: {self.module_name} | Path: {self.json_path}",
                       level="WARNING")
            self._handle_build_error(e)

        except Exception as e:
            # 4b. Catastrophic Failure Handling - Full traceback for unexpected errors
            logger.exception(f"💥💥💥 [CATASTROPHIC] The Flux Capacitocracked while building {self.module_name}! Error: {e}")
            self._handle_build_error(e)

    def _instantiate_builder(self):
        """Creates the DynamicGuiBuilder instance."""
        import json
        builder_config = self.config_data.copy()

        # ⚡ PRE-FLIGHT: Inspect JSON for behavior flags before scaffolding
        try:
            with open(self.json_path, 'r') as f:
                raw_data = json.load(f)
                # Find the root object (often named after the module or generic)
                root_obj = next(iter(raw_data.values())) if isinstance(raw_data, dict) and raw_data else {}
                
                # Check for behavior overrides
                behavior = root_obj.get("behavior", {})
                if "allow_scrolling" in behavior:
                    builder_config["allow_scrolling"] = behavior["allow_scrolling"]
                if "transparent" in behavior:
                    builder_config["transparent"] = behavior["transparent"]
                
                # ⚡ AUTOMATIC OVERLAY: If the root type is OcaBin, it handles its own scrolling.
                # The builder should default to overlay mode (allow_scrolling=False) to avoid 
                # nested scrollbars, UNLESS explicitly requested otherwise.
                if root_obj.get("type") == "OcaBin" and "allow_scrolling" not in behavior:
                    builder_config["allow_scrolling"] = False
                    builder_config["transparent"] = True

        except Exception as e:
            matrix_log("UI", "GUI_MANAGER", "_instantiate_builder", f"⚠️ Failed to pre-read JSON flags: {e}", level="DEBUG")

        # ⚡ SANITIZATION: Enforce 1x1 minimum to prevent X11 BadValue crashes
        # during the initial geometry configuration of the top-level container.
        if "geometry" in builder_config:
            builder_config["geometry"] = WidgetContext.sanitize_geometry(builder_config["geometry"])

        try:
            self.dynamic_gui = DynamicGuiBuilder(
                parent=self,
                json_path=str(self.json_path),
                tab_name=self.module_name,
                config=builder_config,
                use_grid=True
            )
            self.grid_rowconfigure(0, weight=1)
            self.grid_columnconfigure(0, weight=1)
            self.dynamic_gui.grid(row=0, column=0, sticky="nsew")
            self.dynamic_gui.start()
        except tk.TclError as e:
            # 🛡️ RECURSION GUARD EXPANSION: Catch TclErrors during initial configuration
            # to prevent a hard crash if X11 rejects transient 0x0 geometries.
            logger.error(f"🖥️🎨 [UI] TclError during builder instantiation for {self.module_name}: {e}")
            matrix_log("UI", "GUI_MANAGER", "_instantiate_builder", f"⚠️ Geometry initialization failed for {self.module_name}. Proceeding with fallback.", level="WARNING")

    def _handle_build_error(self, e):
        """Cleanly displays an error state in the UI."""
        if self.winfo_exists():
            for child in self.winfo_children():
                child.destroy()
            tk.Label(
                self, text=f"Error: {e}", fg="red", bg="#2b2b2b",
                font=("Arial", 12, "bold")
            ).pack(pady=20)

    def _on_tab_selected(self, event):
        """Optional hook for tab selection events."""
        matrix_log("UI", "GUI_MANAGER", inspect.currentframe().f_code.co_name, f"🖥️🔵 Tab '{self.module_name}' focused. Systems nominal.", level="DEBUG")

# Local Debug Flag
