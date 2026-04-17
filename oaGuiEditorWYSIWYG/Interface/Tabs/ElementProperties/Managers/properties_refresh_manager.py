# Interface/Tabs/ElementProperties/Managers/properties_refresh_manager.py
# Author: Anthony Peter Kuzub
# Version: 20260417.001.0
#
# Description: Coordinates the rendering and caching of property editors.

import tkinter as tk
from oaLogging.Methods.matrix_gate import matrix_log
from ..Methods.data_merger import deep_merge
from .....Core.state import state_manager
from ....PropertyEditor.property_leaf import PropertyLeaf

class PropertiesRefreshManager:
    """Manages the lifecycle of rendering property editors for a focused element."""

    def __init__(self, workspace, ui, library):
        self.workspace = workspace
        self.ui = ui
        self.library = library
        self.widget_cache = {}

    def refresh(self, focused_path):
        """Clears existing content and renders the recursive property tree for the given path."""
        if not focused_path or not self.workspace.winfo_exists(): return
        
        matrix_log("ui", "gui_builder", "element_properties", f"🎨🎨🎨 [RENDER] ElementProperties: Refreshing content for {focused_path}", "DEBUG")

        self.ui.clear_content()
        self.ui.update_path_display(focused_path)

        actual_data = state_manager.get_value_at_path(focused_path)
        if actual_data is None: 
            tk.Label(self.ui.scroll_frame, text="Selected element not found in state.", bg="#2b2b2b", fg="#ff4444").pack(pady=50)
            return

        # 1. Prepare rendering data (Merge with Schema)
        display_data = self._prepare_display_data(actual_data)

        # 2. Render quick tools (alignment, sticky) if it's a widget
        self._render_quick_tools(actual_data)

        # 3. Render the recursive property tree
        new_widget_cache = {}
        self._render_tree(display_data, actual_data, focused_path, new_widget_cache)

        # 4. Lifecycle management: Destroy unused widgets from previous cache
        self._cleanup_unused_widgets(new_widget_cache)
        self.widget_cache = new_widget_cache

    def _prepare_display_data(self, actual_data):
        if not isinstance(actual_data, dict): return actual_data
        
        w_type = actual_data.get("type", actual_data.get("widget_type"))
        schema_template = next((c.get("schema", {}) for n, c in self.library.items() if c["type"] == w_type), {})
        if schema_template:
            return deep_merge(schema_template, actual_data)
        return actual_data

    def _render_quick_tools(self, actual_data):
        if isinstance(actual_data, dict) and (actual_data.get("type") or actual_data.get("widget_type")):
            tools = tk.Frame(self.ui.scroll_frame, bg="#252525", pady=10)
            tools.pack(fill="x", pady=(0, 10))
            self.workspace._render_alignment_quick_tools(actual_data, tools)
            self.workspace._render_sticky_quick_tools(actual_data, tools)

    def _render_tree(self, display_data, actual_data, focused_path, new_widget_cache):
        if isinstance(display_data, dict):
            self.workspace._render_recursive_properties(
                display_data, self.ui.scroll_frame,
                prefix=focused_path,
                actual_data=actual_data,
                widget_cache=self.widget_cache,
                new_widget_cache=new_widget_cache
            )
        else:
            PropertyLeaf.create(self.ui.scroll_frame, focused_path.split(".")[-1], 
                                display_data, focused_path, self.workspace)

    def _cleanup_unused_widgets(self, new_widget_cache):
        for full_path, widget_info in self.widget_cache.items():
            if full_path not in new_widget_cache:
                widget = widget_info.get("widget")
                if widget and widget.winfo_exists(): widget.destroy()
