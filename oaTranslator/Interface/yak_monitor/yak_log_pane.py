# 22_Yak_Monitor/yak_log_pane.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Encapsulates the traffic log treeview for the Yak Monitor.

import tkinter as tk
from tkinter import ttk
from oaGui.Constants.builder_constants import (
    DEFAULT_TREE_COLUMN_WIDTH, LARGE_TREE_COLUMN_WIDTH, 
    SMALL_TREE_COLUMN_WIDTH, MAX_LOG_ENTRIES
)

class YakLogPane(ttk.Frame):
    """Encapsulates the traffic log treeview and its controls."""
    def __init__(self, parent, on_select_callback, **kwargs):
        super().__init__(parent, style="Dark.TFrame", **kwargs)
        self._on_select = on_select_callback
        self._setup_ui()

    def _setup_ui(self):
        cols = ("Device Type", "Model", "YAK", "Action", "Command", "Value", "Message")
        self.tree = ttk.Treeview(self, columns=cols, show="headings")
        for col in cols:
            self.tree.heading(col, text=col)
            width = LARGE_TREE_COLUMN_WIDTH if col == "Message" else (
                SMALL_TREE_COLUMN_WIDTH if col == "Value" else DEFAULT_TREE_COLUMN_WIDTH
            )
            self.tree.column(col, width=width, anchor="w" if col in ["Message", "Command", "Device Type", "Model", "YAK", "Action"] else "center")
        
        sy, sx = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview), ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
        self.tree.grid(row=0, column=0, sticky="nsew"); sy.grid(row=0, column=1, sticky="ns"); sx.grid(row=1, column=0, sticky="ew")
        self.grid_rowconfigure(0, weight=1); self.grid_columnconfigure(0, weight=1)
        self.tree.tag_configure("green_row", foreground="#00ff00"); self.tree.tag_configure("orange_row", foreground="#ffaa00")
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

    def add_entry(self, values, tags):
        self.tree.insert("", 0, values=values, tags=tags)
        if len(self.tree.get_children()) > MAX_LOG_ENTRIES: 
            self.tree.delete(self.tree.get_children()[-1])
