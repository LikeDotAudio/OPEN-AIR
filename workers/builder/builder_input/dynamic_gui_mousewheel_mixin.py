# builder_input/dynamic_gui_mousewheel_mixin.py
#
# This file provides the MousewheelScrollMixin class, adding mousewheel scrolling functionality to Tkinter Canvas widgets.
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
# Version 20250821.200641.1

import sys
import inspect
import datetime
import pathlib
import os

from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args
from managers.configini.config_reader import Config

app_constants = Config.get_instance()  # Get the singleton instance


# --- Global Scope Variables ---
current_file_path = pathlib.Path(__file__).resolve()
project_root = current_file_path.parent.parent.parent
current_file = str(current_file_path.relative_to(project_root)).replace("\\", "/")

# Replace old print with debug_log
debug_logger(
    message=f"DEBUG: Loading dynamic_gui_mousewheel_mixin.py from: {current_file_path}",
    **_get_log_args(),
)


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
        current_function_name = inspect.currentframe().f_code.co_name
        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"🖥️🔵 Mousewheel event detected: {event.num}. Scrolling canvas.",
                **_get_log_args(),
            )
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
        current_function_name = inspect.currentframe().f_code.co_name
        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"🖥️🔵 Binding mousewheel scrolling for canvas.",
                **_get_log_args(),
            )
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
        current_function_name = inspect.currentframe().f_code.co_name
        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message="🖥️🔵 Unbinding mousewheel scrolling for canvas.",
                **_get_log_args(),
            )
        # Unbind mousewheel scrolling when the mouse leaves the scrollable area
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")