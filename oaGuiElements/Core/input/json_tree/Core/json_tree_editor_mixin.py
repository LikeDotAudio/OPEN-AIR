# Core/json_tree_editor_mixin.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import tkinter as tk
from tkinter import ttk


class JsonTreeEditorMixin:
    """Encapsulates inline editing logic for the Treeview."""

    def _setup_editing(self):
        self.tree.bind("<Double-1>", self._on_double_click)

    def _on_double_click(self, event):
        item_id = self.tree.identify_row(event.y)
        column_id = self.tree.identify_column(event.x)
        if not item_id: return

        # Only allow editing the 'value' column (index 1)
        col_idx = int(column_id.replace("#", ""))
        if col_idx != 1: return

        logical_col = "value"
        old_value = self.tree.set(item_id, logical_col)
        x, y, w, h = self.tree.bbox(item_id, column_id)

        entry = ttk.Entry(self.tree)
        entry.insert(0, old_value)
        entry.select_range(0, tk.END)
        entry.focus_set()
        entry.place(x=x, y=y, width=w, height=h)

        def save_edit(event=None):
            new_value = entry.get()
            typed_value = self._parse_typed_value(new_value)
            self.tree.set(item_id, logical_col, str(typed_value))
            self._update_data_from_tree_id(item_id, typed_value)
            entry.destroy()

        entry.bind("<Return>", save_edit)
        entry.bind("<FocusOut>", save_edit)
        entry.bind("<Escape>", lambda e: entry.destroy())

    def _parse_typed_value(self, value):
        if value.lower() == "true": return True
        if value.lower() == "false": return False
        try:
            if "." in value: return float(value)
            return int(value)
        except ValueError: return value

    def _update_data_from_tree_id(self, item_id, new_value):
        path = []
        curr = item_id
        while curr:
            text = self.tree.item(curr, "text")
            if text.startswith("[") and text.endswith("]"):
                try: path.insert(0, int(text[1:-1]))
                except: path.insert(0, text)
            else: path.insert(0, text)
            curr = self.tree.parent(curr)

        self.data_manager.update_at_path(path, new_value)
