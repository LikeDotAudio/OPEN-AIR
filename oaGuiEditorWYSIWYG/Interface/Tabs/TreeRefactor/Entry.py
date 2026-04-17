# Interface/Tabs/TreeRefactor/Entry.py
# Author: Gemini CLI
# Version: 20260417.001.0
#
# Description: Gatekeeper for the TreeRefactor module. Orchestrates UI, state, and interactions.

import tkinter as tk
from tkinter import ttk
from oaComBroker.Core.event_bus import event_bus
from ....Core.state import state_manager

# --- Standard Debug Logging Setup ---
from oaLogging.Core.logger import GUI_LOGGER as logger

# --- MODULAR IMPORTS ---
from .Core.tree_styler import apply_tree_styles
from .Managers.tree_drag_drop_handler import TreeDragDropHandler
from .Managers.tree_ops_manager import TreeOpsManager
from .Methods.path_resolver import normalize_path
from .Methods.tree_populator import populate_tree
from .Interface.tree_view_ui import TreeViewUI

class TreeRefactor(ttk.Frame):
    """Hierarchical tree view for GUI structure refactoring."""

    def __init__(self, parent):
        apply_tree_styles()
        super().__init__(parent, style="Dark.TFrame")
        
        # Internal state
        self._last_clean_path = None
        
        # 1. Initialize Managers
        self._ops_manager = None # Set after UI build
        self._drag_handler = None # Set after UI build

        # 2. Build UI
        self.tree = TreeViewUI.build(
            self, 
            on_up=lambda: self._ops_manager.move_up(),
            on_down=lambda: self._ops_manager.move_down(),
            on_delete=lambda: self._ops_manager.delete_item()
        )
        
        # 3. Finalize Managers with UI references
        self._ops_manager = TreeOpsManager(self.tree, state_manager, self._refresh_after_op)
        self._drag_handler = TreeDragDropHandler(self.tree, state_manager, self._refresh_after_op)

        # 4. Bind Interactions
        self._bind_events()
        
        # 5. Global Subscriptions
        event_bus.subscribe("STATE_UPDATED", self._on_state_updated)
        event_bus.subscribe("FOCUS_REQUESTED", self._on_external_focus)
        
        # 6. Initial Data Load
        current_state = state_manager.get_state()
        if current_state:
            self._on_state_updated(current_state)

    def _bind_events(self):
        """Binds UI events to manager methods."""
        # Drag and Drop
        self.tree.bind("<ButtonPress-1>", self._drag_handler.on_drag_start)
        self.tree.bind("<B1-Motion>", self._drag_handler.on_drag_motion)
        self.tree.bind("<ButtonRelease-1>", self._drag_handler.on_drag_stop)
        
        # Selection and Expansion
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        self.tree.bind("<<TreeviewOpen>>", self._on_tree_open)

    def _on_state_updated(self, json_data, source=None):
        """Refreshes the tree when the master state changes."""
        if source == self or source == self._ops_manager or source == self._drag_handler: 
            return # Avoid infinite loops
        
        self.tree.delete(*self.tree.get_children())
        populate_tree(self.tree, "", json_data)
        
        # Re-apply focus if we had one
        if self._last_clean_path:
             self._select_path_in_tree(self._last_clean_path)

    def _on_external_focus(self, path, source=None):
        """Handles focus requests from other tabs."""
        if source == self or not self.winfo_exists(): return
        
        clean_path = normalize_path(path, state_manager)
        self._last_clean_path = clean_path
        self._select_path_in_tree(clean_path)

    def _select_path_in_tree(self, path):
        """Finds and selects the node corresponding to the given dot-notated path."""
        if not path: return

        # ⚡ EXPAND PARENTS
        parts = path.split('.')
        for i in range(1, len(parts)):
            p = ".".join(parts[:i])
            if self.tree.exists(p):
                self.tree.item(p, open=True)

        if self.tree.exists(path):
            self.tree.selection_set(path)
            self.tree.see(path)

    def _on_tree_open(self, event):
        """Lazy loads children when a node is expanded."""
        node_id = self.tree.focus()
        children = self.tree.get_children(node_id)
        if len(children) == 1 and self.tree.item(children[0], "values")[0] == "dummy":
            self.tree.delete(children[0])
            path = self.tree.item(node_id, "values")[0]
            data = state_manager.get_value_at_path(path)
            if data is not None:
                populate_tree(self.tree, node_id, data)

    def _on_tree_select(self, event):
        """Syncs selection with the global focus."""
        selected = self.tree.selection()
        if not selected: return
        
        path = self.tree.item(selected[0], "values")[0]
        event_bus.publish("FOCUS_REQUESTED", path=path, source=self)

    def _refresh_after_op(self):
        """Manually triggers a tree rebuild after a local operation."""
        self._on_state_updated(state_manager.get_state())

# Standardized exports
__all__ = ["TreeRefactor"]
