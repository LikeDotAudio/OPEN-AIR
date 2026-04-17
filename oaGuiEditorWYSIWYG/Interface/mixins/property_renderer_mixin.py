# Interface/mixins/property_renderer_mixin.py
# Author: Anthony Peter Kuzub
# Version: 20260416.Interface.1
#
# Description: Handles the recursive generation of the properties UI tree.

from ...Core.state import state_manager
from ..renderers.tree_renderer import TreeRenderer

class PropertyRendererMixin:
    """Handles the recursive generation of the properties UI tree."""

    def __init__(self):
        super().__init__()
        self.widget_cache = {} # Cache to store rendered widgets by path

    def _render_recursive_properties(self, data, parent, prefix="", depth=0, actual_data=None, widget_cache=None, new_widget_cache=None):
        """Delegates rendering to the modular TreeRenderer."""
        TreeRenderer.render_recursive(
            data, parent, prefix, depth, actual_data, 
            widget_cache, new_widget_cache, mixin_ref=self
        )

    def _add_state_item(self, path, value):
        """State manipulation logic (Logic stayed in mixin)."""
        state_manager.update_state(value, path=path, source=self)
        if hasattr(self, '_refresh_content'):
            self._refresh_content()

    def _reorder(self, path, direction):
        """Structural logic (Logic stayed in mixin)."""
        state_manager.reorder_element(path, direction, source=self)

    def _show_message_details(self, path, data):
        """Displays a popup with the message JSON."""
        import orjson
        from tkinter import messagebox
        
        popup = tk.Toplevel(self)
        popup.title(f"Message Details: {path}")
        popup.geometry("500x400")
        popup.configure(bg="#1e1e1e")
        
        header = tk.Frame(popup, bg="#333333", pady=5)
        header.pack(fill="x")
        tk.Label(header, text="MESSAGE BLUEPRINT", bg="#333333", fg="#33A1FD", font=("Arial", 9, "bold")).pack(padx=10)
        
        text_area = tk.Text(popup, bg="#1e1e1e", fg="#dcdcdc", font=("Consolas", 10), padx=10, pady=10, bd=0)
        text_area.pack(fill="both", expand=True)
        
        formatted = orjson.dumps(data, option=orjson.OPT_INDENT_2).decode()
        text_area.insert("1.0", formatted)
        text_area.config(state="disabled")
        
        btn_frame = tk.Frame(popup, bg="#1e1e1e", pady=10)
        btn_frame.pack(fill="x")
        tk.Button(btn_frame, text="CLOSE", command=popup.destroy, bg="#3a3a3a", fg="white", relief="flat", padx=20).pack()
