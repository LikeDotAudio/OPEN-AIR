# oaGui/FileReaders/json_gui_host.py
# Author: Anthony Peter Kuzub
# Version: 20260111.1510.1
#
# Description: Universal GUI Loader - Host for Dynamic GUI components.

import inspect
import pathlib
import tkinter as tk
from typing import Any

from loguru import logger

from oaGui.Workers.orchestration.loader_orchestrator import LoaderOrchestrator
from oaGui.Core.context.cache_widget_context import WidgetContext
from oaLogging.Methods.matrix_gate import matrix_log
from oaGui.Methods.validation.json_integrity_validator import JsonIntegrityValidator

# Globals
current_version = "20260111.1510.1"

class JsonGuiHost(tk.Frame):
    """
    The Universal Wrapper.
    It takes a JSON path and builds the interface.
    """

    def __init__(self, parent, json_path: str, config: dict[str, Any] | None = None, **kwargs):
        """
        Initialize the Universal GUI Loader.
        """
        if "bg" not in kwargs and "background" not in kwargs:
            kwargs["bg"] = "#2b2b2b"

        super().__init__(parent, **kwargs)

        self.json_path = pathlib.Path(json_path)
        self.configuration = config if config else {}
        self.module_name = self.json_path.stem.replace("gui_", "").upper()

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.app = self.configuration.get("app_instance")
        self._init_ui()

    def _init_ui(self):
        """Skip the loading label and start the build immediately."""
        self.after(1, self._construct_dynamic_gui)

    def _construct_dynamic_gui(self):
        """The Main Event: Handing off to the Builder."""
        try:
            if not self.json_path.exists():
                raise FileNotFoundError(f"Blueprint missing! {self.json_path}")

            matrix_log("UI", "GUI_MANAGER", inspect.currentframe().f_code.co_name,
                       f"🏗️🏗️🏗️ [BUILDER] Constructing '{self.module_name}' via LoaderOrchestrator...",
                       level="DEBUG")

            self._instantiate_builder()

            matrix_log("UI", "GUI_MANAGER", inspect.currentframe().f_code.co_name,
                       f"✅✅✅ [SUCCESS] It works! {self.module_name} is fully operational!",
                       level="SUCCESS")

        except FileNotFoundError as e:
            matrix_log("UI", "GUI_MANAGER", "_construct_dynamic_gui",
                       f"⚠️⚠️⚠️ [VALIDATION] Blueprint missing! Module: {self.module_name} | Path: {self.json_path}",
                       level="WARNING")
            self._handle_build_error(e)

        except Exception as e:
            logger.exception(f"💥💥💥 [CATASTROPHIC] The Flux Capacitocracked while building {self.module_name}! Error: {e}")
            self._handle_build_error(e)

    def _instantiate_builder(self):
        """Creates the LoaderOrchestrator instance."""
        builder_config = self.configuration.copy()

        # ⚡ PRE-FLIGHT: Inspect JSON for behavior flags
        overrides = JsonIntegrityValidator.validate(self.json_path)
        builder_config.update(overrides)

        # ⚡ SANITIZATION: Enforce 1x1 minimum
        if "geometry" in builder_config:
            builder_config["geometry"] = WidgetContext.sanitize_geometry(builder_config["geometry"])

        try:
            self.dynamic_gui = LoaderOrchestrator(
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
