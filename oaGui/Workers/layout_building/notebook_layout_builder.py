# oaGui/Workers/layout_building/notebook_layout_builder.py
# Author: Anthony Peter Kuzub
# Version: 20260502.1000.1
#
# Description: Builder for tabbed notebook GUI layouts.

import tkinter as tk
from tkinter import ttk

from .base_layout_builder import BaseLayoutBuilder


class NotebookLayoutBuilder(BaseLayoutBuilder):
    """Constructs tabbed notebook layouts."""

    def build(self, path, parent_widget, layout_data, on_complete=None):
        notebook = ttk.Notebook(parent_widget)
        notebook.pack(fill=tk.BOTH, expand=True)
        if hasattr(self.scanner, '_notebooks'): self.scanner._notebooks[path] = notebook
        if hasattr(self.scanner, 'tab_window_manager'):
            notebook.bind("<Control-Button-1>", self.scanner.tab_window_manager.tear_off_tab)

        # ⚡ MULTI-BINDING: Ensure right-click works across different Linux environments/mice
        notebook.bind("<Button-2>", self.scanner._on_notebook_right_click) # Middle or Right on some setups
        notebook.bind("<Button-3>", self.scanner._on_notebook_right_click) # Standard Right
        notebook.bind("<ButtonRelease-3>", self.scanner._on_notebook_right_click, add="+")

        # ⚡ ACCESSIBILITY: Alternative for cases where right-click is captured by theme
        notebook.bind("<Shift-Button-1>", self.scanner._on_notebook_right_click, add="+")

        notebook.bind("<<NotebookTabChanged>>", self.scanner._on_tab_change)
        notebook.bind("<<NotebookTabChanged>>", self.scanner._handle_tab_visibility, add="+")

        for tab_info in layout_data.get("tabs", []):
            tab_path = tab_info["path"]
            tab_frame = tk.Frame(notebook, bg=self.scanner.theme_colors["bg"])
            if hasattr(self.scanner, '_frames_by_path'):
                self.scanner._frames_by_path[tab_path] = tab_frame
            tab_frame.is_populated = False
            tab_frame.build_path = tab_path
            notebook.add(tab_frame, text=tab_info["display_name"])

        if on_complete: on_complete()
