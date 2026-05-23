# 22_Yak_Monitor/yak_dissector_pane.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Encapsulates the JSON deep packet inspection tree for the Yak Monitor.

import tkinter as tk
from tkinter import ttk

import orjson


class YakDissectorPane(ttk.Frame):
    """Encapsulates the JSON deep packet inspection tree."""
    def __init__(self, parent, theme_bg, **kwargs):
        super().__init__(parent, style="Dark.TFrame", **kwargs)
        self.theme_bg = theme_bg
        self._setup_ui()

    def _setup_ui(self):
        self._setup_header()
        self.tree = ttk.Treeview(self, columns=("Value"), show="tree headings")
        self.tree.heading("#0", text="Key / Index"); self.tree.heading("Value", text="Value")
        self.tree.column("#0", width=200, anchor="w"); self.tree.column("Value", width=400, anchor="w")
        sy = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sy.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True); sy.pack(side=tk.RIGHT, fill=tk.Y)

    def _setup_header(self):
        f = tk.Frame(self, bg=self.theme_bg); f.pack(side=tk.TOP, fill=tk.X, pady=(5, 0))
        self.vars = {k: tk.StringVar(value=f"{k}: -") for k in ["Device Type", "Model", "YAK", "Action", "Command"]}
        d = tk.Frame(f, bg=self.theme_bg); d.pack(side=tk.LEFT, fill=tk.X, expand=True)
        for k in self.vars: ttk.Label(d, textvariable=self.vars[k], font=("Helvetica", 10, "bold"), style="Dark.TLabel", padding=(0, 0, 10, 0)).pack(side=tk.LEFT)

    def update(self, details, payload):
        for k, v in details.items(): self.vars[k].set(f"{k}: {v}")
        for item in self.tree.get_children(): self.tree.delete(item)
        try:
            data = orjson.loads(payload)
            self._populate("", data)
        except: self.tree.insert("", "end", text="Raw Payload", values=(payload))

    def _populate(self, parent, data):
        if isinstance(data, dict):
            for k, v in data.items():
                if isinstance(v, (dict, list)): self._populate(self.tree.insert(parent, "end", text=k, open=True), v)
                else: self.tree.insert(parent, "end", text=k, values=(v))
        elif isinstance(data, list):
            for i, v in enumerate(data):
                if isinstance(v, (dict, list)): self._populate(self.tree.insert(parent, "end", text=f"[{i}]", open=True), v)
                else: self.tree.insert(parent, "end", text=f"[{i}]", values=(v))
