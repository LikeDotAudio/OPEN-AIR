import tkinter as tk
from tkinter import ttk
from loguru import logger
from workers.importers.saver import save_markers_file_internally

class TreeCellEditor:
    """Manages the spawning and lifecycle of the in-place entry editor for Treeview cells."""

    @staticmethod
    def start(tab, item, col_idx, initial_value, navigation_cb):
        # 1. Clear existing editors
        for w in tab.marker_tree.winfo_children():
            if isinstance(w, ttk.Entry) and w.winfo_name() == "cell_editor": w.destroy()

        # 2. Spawn Editor
        editor = ttk.Entry(tab.marker_tree, style="Markers.TEntry", name="cell_editor")
        editor.insert(0, initial_value); editor.focus_force()
        
        x, y, w, h = tab.marker_tree.bbox(item, tab.marker_tree["columns"][col_idx])
        editor.place(x=x, y=y, width=w, height=h)

        def commit(direction=None):
            new_val = editor.get(); editor.destroy()
            
            vals = list(tab.marker_tree.item(item, "values"))
            vals[col_idx] = new_val
            tab.marker_tree.item(item, values=vals)
            
            row_idx = tab.marker_tree.index(item)
            if row_idx < len(tab.tree_data):
                tab.tree_data[row_idx][tab.tree_headers[col_idx]] = new_val
                logger.success(f"✅ Cell updated: Row {row_idx+1}, Col '{tab.tree_headers[col_idx]}'")
                save_markers_file_internally(tab)
            
            if direction: navigation_cb(item, col_idx, direction)

        # 3. Bindings
        editor.bind("<Return>", lambda e: commit("down"))
        editor.bind("<Tab>", lambda e: commit("right"))
        editor.bind("<Shift-Tab>", lambda e: commit("left"))
        editor.bind("<Control-Return>", lambda e: commit("ctrl_down"))
        editor.bind("<FocusOut>", lambda e: commit(None))
        for key in ["Up", "Down", "Left", "Right"]:
            editor.bind(f"<{key}>", lambda e, d=key.lower(): commit(d))
        
        return editor
