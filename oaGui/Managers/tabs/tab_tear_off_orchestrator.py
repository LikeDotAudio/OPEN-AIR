# oaGui/Managers/tabs/tab_tear_off_orchestrator.py
# Author: Anthony Peter Kuzub
# Version: 20260502.1000.1
#
# Description: Orchestrates the "tear-off" functionality for notebook tabs into separate windows.

import tkinter as tk
from tkinter import ttk

from oaLogging.Methods.matrix_gate import matrix_log


def liberate_notebook_tab(tab_window_manager, event):
    """Detaches a tab from its notebook and rebuilds it in a new Toplevel window."""
    if not (event.state & 4 and event.num == 1):
        return

    notebook = event.widget
    try:
        selected_id = notebook.select()
        if not selected_id: return

        original_tab = notebook.nametowidget(selected_id)
        tab_text = notebook.tab(selected_id, "text")
        build_path = getattr(original_tab, "build_path", None)

        if not build_path:
            matrix_log("ui", "tabs", "tear_off", f"🖥️🟡 Tab '{tab_text}' is not tear-off enabled.", "DEBUG")
            return

        original_index = notebook.index(selected_id)
        notebook.forget(selected_id)

        # Cleanup original frame for background efficiency
        for child in original_tab.winfo_children():
            child.destroy()
        original_tab.is_populated = False

        # Create liberated window
        window = tk.Toplevel(tab_window_manager.application.root)
        window.title(f"{tab_text} - Detached")
        window.geometry(original_tab.winfo_geometry())
        window.grid_rowconfigure(0, weight=1); window.grid_columnconfigure(0, weight=1)

        content = ttk.Frame(window)
        content.grid(row=0, column=0, sticky="nsew")

        # Rebuild in new context
        tab_window_manager.application._build_from_directory(path=build_path, parent_widget=content)

        # Track for re-attachment
        tab_window_manager.torn_off_windows[window] = {
            "original_notebook": notebook,
            "original_tab_frame": original_tab,
            "original_index": original_index,
            "tab_text": tab_text,
        }

        def _set_protocol():
            if window.winfo_exists():
                window.protocol("WM_DELETE_WINDOW", lambda: tab_window_manager._on_tear_off_window_close(window))
        window.after(1, _set_protocol)

        matrix_log("ui", "tabs", "tear_off", f"🖥️✅ Tab '{tab_text}' liberated!", "SUCCESS")

    except Exception as error:
        from oaLogging.Methods.matrix_gate import is_debug_allowed
        if is_debug_allowed(system="ui", element="tabs"):
            from loguru import logger
            logger.exception(f"❌ Error liberating tab: {error}")
