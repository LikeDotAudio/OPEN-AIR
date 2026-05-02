# 3_Command_Router/command_investigation_pane.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Encapsulates the dual-packet inspection logic for the Command Router.

import tkinter as tk
from .command_router_legend import CommandRouterLegend

class CommandInvestigationPane(tk.Frame):
    """Encapsulates the dual-packet inspection logic."""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg="#000000", bd=1, relief="sunken", **kwargs)
        self._setup_ui()

    def _setup_ui(self):
        tk.Label(self, text="🔍 DUAL PACKET INVESTIGATION & SPLINK DISCOVERY", font=("Helvetica", 10, "bold"), fg="#888888", bg="#000000").pack(side=tk.TOP, anchor="nw", padx=5)
        split_frame = tk.Frame(self, bg="#000000")
        split_frame.pack(fill=tk.BOTH, expand=True)

        self.text_src = self._create_inspector(split_frame, "[ SOURCE ]", "#00ff00")
        self.text_dest = self._create_inspector(split_frame, "[ DESTINATION ]", "#ffff00")
        self.legend = CommandRouterLegend(split_frame)
        self.legend.pack(side=tk.RIGHT, fill=tk.Y)

    def _create_inspector(self, parent, title, color):
        col = tk.Frame(parent, bg="#000000")
        col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tk.Label(col, text=title, font=("Helvetica", 8, "bold"), fg=color, bg="#000000").pack(anchor="nw", padx=10)
        text = tk.Text(col, bg="#000000", fg=color, font=("Courier", 9), bd=0, highlightthickness=0)
        text.pack(fill=tk.BOTH, expand=True, padx=5, pady=2)
        return text

    def update_inspectors(self, src_data, dest_data):
        """Updates text widgets with formatted JSON data."""
        self.text_src.delete("1.0", tk.END)
        self.text_dest.delete("1.0", tk.END)
        if src_data: self.text_src.insert(tk.END, src_data)
        if dest_data: self.text_dest.insert(tk.END, dest_data)
