# input_mousewheel_mixin/input_mousewheel_mixin.py
# Author: Anthony Peter Kuzub
# Version: 20250821.200641.1
#
# Description: input_mousewheel_mixin/mousewheel_mixin.py

import sys
import inspect
import pathlib
import os

# --- Standard Debug Logging Setup ---
BUILDER_DEBUG = False    # Set to False in production, True for dev on this file
from oaLogging.Core.logger import initialize_logging, set_log_directory, builder_logger
from loguru import logger

from oaConfiguration.FileReaders.config_reader import Config

app_constants = Config.get_instance()  # Get the singleton instance


# --- Global Scope Variables ---
current_file_path = pathlib.Path(__file__).resolve()
project_root = current_file_path.parent.parent.parent
current_file = str(current_file_path.relative_to(project_root)).replace("\\", "/")

# Replace old print with debug_log
if BUILDER_DEBUG: builder_logger.debug(f"📐🏗️💻 [BUILDER] Loading mousewheel_mixin.py from: {current_file_path}")


class MousewheelScrollMixin:
    """
    Mixin to add mousewheel scrolling functionality to a Tkinter Canvas.
    Assumes the presence of `self.canvas` and logging utilities.
    """

    # Handles mousewheel scroll events for the canvas.
    # This method interprets mousewheel input (platform-specific) and scrolls the
    # canvas vertically, providing intuitive navigation for large content areas.
    # Inputs:
    #     event: The tkinter mousewheel event object.
    # Outputs:
    #     None.
    def _on_mousewheel(self, event):
        if BUILDER_DEBUG: builder_logger.trace(f"🖱️🔄📏 [SCROLL] Mousewheel event detected: {event.num}. Scrolling canvas.")
        # Platform-specific mouse wheel scrolling
        if sys.platform == "linux":
            if event.num == 4:  # Scroll up
                self.canvas.yview_scroll(-1, "units")
            elif event.num == 5:  # Scroll down
                self.canvas.yview_scroll(1, "units")
        else:  # Windows and macOS
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # Binds mousewheel scroll events to the canvas.
    # This method attaches the _on_mousewheel handler to platform-specific mousewheel
    # events when the mouse cursor enters the canvas area.
    # Inputs:
    #     event: The tkinter event object (e.g., <Enter> event).
    # Outputs:
    #     None.
    def _bind_mousewheel(self, event):
        if BUILDER_DEBUG: builder_logger.trace(f"🖱️👆🔗 [EVENTS] Binding mousewheel scrolling for canvas.")
        # Bind mousewheel scrolling when the mouse enters the scrollable area
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)  # Linux scroll up
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)  # Linux scroll down

    # Unbinds mousewheel scroll events from the canvas.
    # This method removes the mousewheel event handlers when the mouse cursor leaves
    # the canvas area, preventing unintended scrolling in other parts of the application.
    # Inputs:
    #     event: The tkinter event object (e.g., <Leave> event).
    # Outputs:
    #     None.
    def _unbind_mousewheel(self, event):
        if BUILDER_DEBUG: builder_logger.trace("🖱️❌🧹 [EVENTS] Unbinding mousewheel scrolling for canvas.")
        # Unbind mousewheel scrolling when the mouse leaves the scrollable area
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")
