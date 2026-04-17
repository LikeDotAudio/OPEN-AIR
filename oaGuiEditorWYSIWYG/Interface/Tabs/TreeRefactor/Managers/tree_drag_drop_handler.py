# Interface/Tabs/TreeRefactor/Managers/tree_drag_drop_handler.py
# Author: Gemini CLI
# Version: 20260417.001.0
#
# Description: Handles drag and drop events for the Treeview.

import inspect
from oaLogging.Methods.matrix_gate import matrix_log

class TreeDragDropHandler:
    """Handles drag and drop interactions for hierarchical reordering."""

    def __init__(self, tree, state_manager, refresh_callback):
        self.tree = tree
        self.state_manager = state_manager
        self.refresh_callback = refresh_callback
        self._dragging_item = None

    def on_drag_start(self, event):
        """Captures the item being dragged."""
        item = self.tree.identify_row(event.y)
        if item:
            self._dragging_item = item

    def on_drag_motion(self, event):
        """Optional: Visual feedback during drag."""
        if self._dragging_item:
            pass

    def on_drag_stop(self, event):
        """Handles the drop logic and element relocation."""
        if not self._dragging_item: return
        
        target_item = self.tree.identify_row(event.y)
        if not target_item or target_item == self._dragging_item: 
            self._dragging_item = None
            return

        source_path = self.tree.item(self._dragging_item, "values")[0]
        target_parent_path = self.tree.item(target_item, "values")[0]
        target_type = self.tree.item(target_item, "values")[1]
        
        source_parent_path = ".".join(source_path.split(".")[:-1])
        
        # If target is NOT a block/container, move to target's parent
        if "Block" not in target_type and "Array" not in target_type:
            target_parent_path = ".".join(target_parent_path.split(".")[:-1])

        if target_parent_path == source_parent_path:
             matrix_log("ui", "gui_builder", "on_drag_stop", "🌳 TreeRefactor: Drop target is same as source parent. Use UP/DOWN buttons for reordering.", "INFO")
        else:
            # Note: We need to append '.fields' if target is a Block to match our schema
            target_val = self.state_manager.get_value_at_path(target_parent_path)
            if isinstance(target_val, dict) and "type" in target_val:
                if "Block" in target_val.get("type", ""):
                    target_parent_path = f"{target_parent_path}.fields"
            
            self.state_manager.move_element(source_path, target_parent_path, source=self)
            self.refresh_callback()

        self._dragging_item = None
