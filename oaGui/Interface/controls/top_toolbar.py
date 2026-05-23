# Interface/top_toolbar.py
# Author: Anthony Peter Kuzub
# Version: 20260501.1000.1
#
# Description: Top toolbar for the main OPEN-AIR GUI application.

import tkinter as tk

from oaLogging.Methods.matrix_gate import matrix_log


class ApplicationToolbar(tk.Frame):
    """Top toolbar for the main application orchestrator."""
    def __init__(self, parent, launch_editor_callback, **kwargs):
        super().__init__(parent, bg="#333333", height=30, **kwargs)
        self.launch_editor_callback = launch_editor_callback
        self._init_ui()

    def _init_ui(self):
        tk.Label(self, text="OPEN-AIR CORE", bg="#333333", fg="white",
                 font=("Arial", 9, "bold")).pack(side="left", padx=10)

        tk.Button(self, text="Launch WYSIWYG Editor", bg="#444444", fg="#00FF00",
                  font=("Arial", 8, "bold"), relief="flat", padx=10,
                  command=self._launch_editor).pack(side="right", padx=10, pady=2)

    def _launch_editor(self):
        matrix_log("ui", "gui_shell", "_launch_wysiwyg_editor", "🚀 [EDITOR] Launching WYSIWYG Designer...", "INFO")
        if self.launch_editor_callback:
            self.launch_editor_callback()
