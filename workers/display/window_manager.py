# display/window_manager.py
#
# Manages Toplevel windows for tear-off tabs and handles window management protocols.
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

import tkinter as tk
from tkinter import ttk
import inspect
import os
import sys
import pathlib
from managers.configini.config_reader import Config

app_constants = Config.get_instance()  # Get the singleton instance
from workers.logger.logger import debug_logger  # Import the global debug_log
from workers.logger.log_utils import _get_log_args


class WindowManager:
    """
    Manages Toplevel windows for tear-off tabs and handles window management protocols.
    """

    # Initializes the WindowManager.
    # This constructor takes a reference to the main application instance, allowing
    # it to access necessary global settings and the root Tkinter window for managing
    # torn-off windows.
    # Inputs:
    #     application_instance: A reference to the main Application class instance.
    # Outputs:
    #     None.
    def __init__(
        self, application_instance
    ):  # Removed current_version, LOCAL_DEBUG_ENABLE, debug_log_func
        self.application = (
            application_instance  # Reference to the main Application class
        )
        # self.current_version = app_constants.current_version # No longer needed
        # self.LOCAL_DEBUG_ENABLE = app_constants.LOCAL_DEBUG_ENABLE # No longer needed
        # self.debug_log = debug_log # No longer needed
        self.torn_off_windows = {}  # To keep track of torn-off windows

    # Handles the tear-off functionality for a notebook tab.
    # When a Control+Left-Click event is detected on a notebook tab, this method
    # detaches the tab's content into a new Toplevel window, allowing it to function
    # as a separate, independent window.
    # Inputs:
    #     event: The tkinter event object (expected from a notebook tab click).
    # Outputs:
    #     None.
    def tear_off_tab(self, event):
        """
        Handles the tear-off functionality for a notebook tab.
        When Ctrl + Left Click is detected on a tab, it creates a new Toplevel
        window and rebuilds the tab's content inside it.
        """
        current_function_name = inspect.currentframe().f_code.co_name
        if not (event.state & 4 and event.num == 1):  # Check for Control-Left-Click
            return

        notebook = event.widget
        try:
            selected_tab_id = notebook.select()
            if not selected_tab_id:
                return

            original_tab_frame = notebook.nametowidget(selected_tab_id)
            tab_text = notebook.tab(selected_tab_id, "text")

            # Ensure the tab is designed for lazy loading and has a build path
            build_path = getattr(original_tab_frame, "build_path", None)
            if not build_path:
                debug_logger(
                    message=f"🖥️🟡 Tab '{tab_text}' is not designed to be torn off (no build_path).",
                    **_get_log_args(),
                )
                return

            # Store details needed to re-attach the tab later
            original_index = notebook.index(selected_tab_id)

            # Forget the tab from the notebook. This hides it but does not destroy the frame.
            notebook.forget(selected_tab_id)

            # Create the new, separate window for the torn-off content.
            # Its parent must be the main root window, which is stored in self.application.root.
            tear_off_window = tk.Toplevel(self.application.root)
            tear_off_window.title(f"{tab_text} - Detached")
            tear_off_window.geometry(
                original_tab_frame.winfo_geometry()
            )  # Set initial geometry based on original tab size

            # Configure the tear-off window to expand its content
            tear_off_window.grid_rowconfigure(0, weight=1)
            tear_off_window.grid_columnconfigure(0, weight=1)

            # Create an intermediate frame to hold the content, filling the new window
            content_frame = ttk.Frame(tear_off_window)
            content_frame.grid(row=0, column=0, sticky="nsew")

            # Rebuild the content from scratch inside the new content_frame
            self.application._build_from_directory(
                path=build_path, parent_widget=content_frame
            )

            # Store the necessary info to re-attach the tab when the window is closed
            self.torn_off_windows[tear_off_window] = {
                "original_notebook": notebook,
                "original_tab_frame": original_tab_frame,
                "original_index": original_index,
                "tab_text": tab_text,
            }

            # Defer setting the protocol to the next event loop cycle to avoid race conditions.
            def set_protocol():
                if tear_off_window.winfo_exists():
                    tear_off_window.protocol(
                        "WM_DELETE_WINDOW",
                        lambda win=tear_off_window: self._on_tear_off_window_close(win),
                    )

            tear_off_window.after(1, set_protocol)

            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"🖥️✅ Tab '{tab_text}' has been liberated into its own Toplevel window!",
                    **_get_log_args(),
                )

        except Exception as e:
            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"❌ Error tearing off tab: {e}", **_get_log_args()
                )

    # Handles the event when a torn-off window is closed.
    # This method re-attaches the content of the closed Toplevel window back into
    # its original notebook, effectively returning the tab to its initial state
    # within the main application window.
    # Inputs:
    #     top_level_window: The Toplevel window that was closed.
    # Outputs:
    #     None.
    def _on_tear_off_window_close(self, top_level_window):
        """
        Handles closing a torn-off window by re-inserting the original (empty)
        tab frame back into its notebook, ready for lazy loading again.
        """
        if top_level_window in self.torn_off_windows:
            tab_info = self.torn_off_windows.pop(top_level_window)

            original_notebook = tab_info["original_notebook"]
            original_tab_frame = tab_info["original_tab_frame"]
            original_index = tab_info["original_index"]
            tab_text = tab_info["tab_text"]

            # Re-insert the original frame back into the notebook at its old position.
            # Since the content was built in the new window, this frame is now empty,
            # but it is ready to be lazy-loaded again if clicked.
            original_notebook.insert("end", original_tab_frame, text=tab_text)

            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"🖥️🟢 Tab '{tab_text}' re-attached to its original notebook.",
                    **_get_log_args(),
                )

            top_level_window.destroy()
        else:
            # Fallback for safety
            top_level_window.destroy()

    # Re-attaches a torn-off tab back to its original or a new notebook.
    # This method is a placeholder for future implementation of a more robust
    # re-attachment mechanism, allowing users to explicitly re-integrate detached
    # windows into the main application interface.
    # Inputs:
    #     torn_off_window_id: The identifier of the torn-off window to re-attach.
    # Outputs:
    #     None.
    def re_attach_tab(self, torn_off_window_id):
        """
        Re-attaches a torn-off tab back to its original notebook or a new one.
        This is a placeholder and requires significant logic to implement fully.
        """
        current_function_name = inspect.currentframe().f_code.co_name
        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message="🖥️🟡 Re-attaching tab functionality is currently a theoretical construct. Implementation pending further research!",
                **_get_log_args(),
            )


# Example of how to integrate into gui_display.py:
# In Application.__init__:
# self.window_manager = WindowManager(self, app_constants.current_version, app_constants.LOCAL_DEBUG_ENABLE,  debug_logger)
#
# In Application._build_from_directory (when creating a notebook):
# notebook.bind('<Control-Button-1>', self.window_manager.tear_off_tab)
#
# The exact widget handling for reparenting may require careful adjustment
# based on the internal structure of ttk.Notebook and how frames are managed.