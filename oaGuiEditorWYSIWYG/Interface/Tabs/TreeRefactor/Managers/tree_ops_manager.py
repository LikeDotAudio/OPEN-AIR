# Interface/Tabs/TreeRefactor/Managers/tree_ops_manager.py
# Author: Gemini CLI
# Version: 20260417.001.0
#
# Description: Handles move up, move down, and delete operations for the Treeview.

import tkinter as tk


class TreeOpsManager:
    """Manages tree operations such as reordering and deletion."""

    def __init__(self, tree, state_manager, refresh_callback):
        self.tree = tree
        self.state_manager = state_manager
        self.refresh_callback = refresh_callback

    def move_up(self):
        """Moves the selected item up in the hierarchy."""
        selected = self.tree.selection()
        if not selected: return

        path = self.tree.item(selected[0], "values")[0]
        self.state_manager.reorder_element(path, "up", source=self)
        self.refresh_callback()

    def move_down(self):
        """Moves the selected item down in the hierarchy."""
        selected = self.tree.selection()
        if not selected: return

        path = self.tree.item(selected[0], "values")[0]
        self.state_manager.reorder_element(path, "down", source=self)
        self.refresh_callback()

    def delete_item(self):
        """Deletes the selected item with confirmation."""
        selected = self.tree.selection()
        if not selected: return

        path = self.tree.item(selected[0], "values")[0]
        if tk.messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{path}'?"):
            self.state_manager.delete_element(path, source=self)
            self.refresh_callback()
