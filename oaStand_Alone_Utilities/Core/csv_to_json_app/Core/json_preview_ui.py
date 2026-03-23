# Core/json_preview_ui.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import tkinter as tk
from tkinter import ttk
import orjson

class JSONPreviewUI:
    """Manages the Structured Treeview and Raw JSON text preview areas."""

    def __init__(self, parent):
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        self._setup_structured_view()
        self._setup_raw_view()

    def _setup_structured_view(self):
        f = ttk.Frame(self.notebook)
        self.notebook.add(f, text="Structured View")
        self.tree = ttk.Treeview(f, columns=("Value"), show="tree headings")
        self.tree.heading("#0", text="Key"); self.tree.heading("Value", text="Value")
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb = ttk.Scrollbar(f, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set); vsb.pack(side=tk.RIGHT, fill=tk.Y)

    def _setup_raw_view(self):
        f = ttk.Frame(self.notebook)
        self.notebook.add(f, text="Raw JSON")
        self.text = tk.Text(f, wrap=tk.WORD, font=("Consolas", 10))
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb = ttk.Scrollbar(f, orient=tk.VERTICAL, command=self.text.yview)
        self.text.configure(yscrollcommand=vsb.set); vsb.pack(side=tk.RIGHT, fill=tk.Y)

    def update(self, data):
        """Refreshes both Treeview and Text areas with new JSON data."""
        self.tree.delete(*self.tree.get_children())
        def insert(parent, d):
            if isinstance(d, dict):
                for k, v in d.items():
                    if isinstance(v, (dict, list)): insert(self.tree.insert(parent, "end", text=k, open=True), v)
                    else: self.tree.insert(parent, "end", text=k, values=(v,))
            elif isinstance(d, list):
                for i, item in enumerate(d):
                    if isinstance(item, (dict, list)): insert(self.tree.insert(parent, "end", text=f"[{i}]", open=True), item)
                    else: self.tree.insert(parent, "end", text=f"[{i}]", values=(item,))
        insert("", data)

        self.text.delete(1.0, tk.END)
        try: self.text.insert(tk.END, orjson.dumps(data, option=orjson.OPT_INDENT_2).decode())
        except Exception as e: self.text.insert(tk.END, f"Error: {e}")
