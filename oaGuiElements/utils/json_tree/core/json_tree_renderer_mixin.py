import tkinter as tk

class JsonTreeRendererMixin:
    """Handles the iterative population and refreshing of the ttk.Treeview."""

    def _insert_node_iterative(self, data, filter_text="", show_values=False, max_depth=5):
        """Iterative tree insertion with filtering support."""
        filter_text = filter_text.lower()
        
        if isinstance(data, dict):
            stack = [("", k, v, 0) for k, v in reversed(list(data.items()))]
        elif isinstance(data, list):
            stack = [("", f"[{i}]", v, 0) for i, v in reversed(list(enumerate(data)))]
        else: return

        while stack:
            parent, key, value, depth = stack.pop()
            if depth > max_depth: continue

            text_key = str(key)
            is_container = isinstance(value, (dict, list))
            str_val = str(value) if not is_container else ""
            
            matches = not filter_text or (filter_text in text_key.lower() or filter_text in str_val.lower())
            is_open = bool(filter_text and matches)

            if is_container:
                node_id = self.tree.insert(parent, "end", text=text_key, open=is_open)
                if show_values and isinstance(value, dict):
                    for col in self.data_manager.dynamic_columns:
                        if col in value: self.tree.set(node_id, col, str(value[col]))
                
                if isinstance(value, dict):
                    for k, v in reversed(list(value.items())): stack.append((node_id, k, v, depth + 1))
                else:
                    for i, v in reversed(list(enumerate(value))): stack.append((node_id, f"[{i}]", v, depth + 1))
            else:
                if matches: self.tree.insert(parent, "end", text=text_key, values=(str_val))

    def refresh_tree_display(self, filter_text="", show_values=False):
        """Clears and repopulates the tree."""
        self.tree.delete(*self.tree.get_children())
        data = self.data_manager.raw_data
        if not data: return
        self._insert_node_iterative(data, filter_text, show_values)
