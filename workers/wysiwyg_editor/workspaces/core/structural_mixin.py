from tkinter import messagebox
from ..core.state_manager import state_manager

class StructuralManagerMixin:
    """Handles structural operations on the JSON tree (Delete, Reorder, Nesting)."""

    def _delete_focused_element(self):
        if not getattr(self, 'focused_path', None): return
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{self.focused_path}'?\nThis cannot be undone."):
            state_manager.delete_element(self.focused_path, source=self)
            self.focused_path = None
            self._refresh_content()

    def _move_out(self, path):
        parts = path.split(".")
        if len(parts) < 3: return
        target_parts = parts[:-2] 
        state_manager.move_element(path, target_parts, source=self)

    def _move_in(self, path):
        parts = path.split(".")
        key = parts[-1]
        parent_path = ".".join(parts[:-1])
        parent_data = state_manager.get_value_at_path(parent_path)
        if not isinstance(parent_data, dict): return
        keys = list(parent_data.keys())
        idx = keys.index(key)
        if idx == 0: return
        prev_key = keys[idx-1]
        prev_sibling = parent_data[prev_key]
        if isinstance(prev_sibling, dict) and prev_sibling.get("type") == "OcaBlock":
            target_path = f"{parent_path}.{prev_key}.fields"
            state_manager.move_element(path, target_path, source=self)

    def _reorder(self, path, direction):
        state_manager.reorder_element(path, direction, source=self)
