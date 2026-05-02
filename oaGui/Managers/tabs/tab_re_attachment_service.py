# oaGui/Managers/tabs/tab_re_attachment_service.py
# Author: Anthony Peter Kuzub
# Version: 20260502.1000.1
#
# Description: Service for re-attaching liberated tabs back to their original notebook containers.

from oaLogging.Methods.matrix_gate import matrix_log

def re_attach_liberated_tab(tab_window_manager, window):
    """Re-inserts a detached tab frame back into its original notebook container."""
    if window not in tab_window_manager.torn_off_windows:
        window.destroy()
        return

    info = tab_window_manager.torn_off_windows.pop(window)
    original_notebook = info["original_notebook"]
    original_tab_frame = info["original_tab_frame"]
    tab_text = info["tab_text"]

    # Re-insert the original (now empty) frame back into the notebook.
    # It remains ready for lazy-loading when next selected.
    original_notebook.insert("end", original_tab_frame, text=tab_text)

    matrix_log("ui", "tabs", "re_attach", f"🖥️🟢 Tab '{tab_text}' re-attached.", "DEBUG")
    window.destroy()
