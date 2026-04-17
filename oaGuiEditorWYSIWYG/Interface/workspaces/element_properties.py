# Interface/workspaces/element_properties.py
# Author: Anthony Peter Kuzub
# Version: 20260416.Interface.1
#
# Description: Modularized Element Properties Workspace.

import tkinter as tk
from tkinter import ttk, messagebox
from oaComBroker.Core.event_bus import event_bus
from ...Core.state import state_manager
from ...FileReaders.grab_bag_loader import GrabBagLoader
# --- Standard Debug Logging Setup ---
from oaLogging.Core.logger import GUI_LOGGER as logger
from oaLogging.Methods.matrix_gate import matrix_log

# --- EXTRACTED CORE MODULES ---
from ..mixins.structural_mixin import StructuralManagerMixin
from ..mixins.layout_tools_mixin import LayoutToolsMixin
from ..mixins.property_renderer_mixin import PropertyRendererMixin

class AutoScrollbar(ttk.Scrollbar):
    def set(self, lo, hi):
        if float(lo) <= 0.0 and float(hi) >= 1.0: self.pack_forget()
        else: self.pack(side="right", fill="y")
        ttk.Scrollbar.set(self, lo, hi)

class ElementProperties(
    tk.Frame,
    StructuralManagerMixin,
    LayoutToolsMixin,
    PropertyRendererMixin
):
    """Refactored properties workspace with modular components."""

    def __init__(self, parent, library_cache=None, *args, **kwargs):
        kwargs.pop("bg", None)
        super().__init__(parent, bg="#2b2b2b", *args, **kwargs)
        
        self.focused_path = None
        self.scrub_start_val, self.scrub_start_x = 0, 0
        self._refresh_job = None
        self.library = library_cache if library_cache is not None else GrabBagLoader().scan_library()
        self.widget_cache = {} # Cache to store rendered widgets by path

        self._setup_styles()
        self._build_ui()
        
        event_bus.subscribe("FOCUS_REQUESTED", self._on_focus_requested)
        event_bus.subscribe("STATE_UPDATED", self._on_state_updated)
        self.bind("<Destroy>", self._on_cleanup)

    def _setup_styles(self):
        style = ttk.Style()
        style.configure("Property.TEntry", fieldbackground="#1e1e1e", foreground="#dcdcdc", 
                        insertcolor="white", bordercolor="#444444")

    def highlight_item(self, element_id):
        """Visual feedback when an item is clicked on the canvas."""
        # Flash the border to indicate focus
        self.config(highlightbackground="#007acc", highlightthickness=2)
        self.after(500, lambda: self.config(highlightthickness=0))

    def _build_ui(self):
        header = tk.Frame(self, bg="#333333", height=35)
        header.pack(side="top", fill="x")
        tk.Label(header, text="PROPERTIES", bg="#333333", fg="white", font=("Arial", 9, "bold")).pack(side="left", padx=10)
        
        tk.Button(header, text="DELETE WIDGET", bg="#cc0000", fg="white", font=("Arial", 7, "bold"), 
                  relief="flat", padx=5, command=self._delete_focused_element).pack(side="right", padx=5)

        self.path_lbl = tk.Label(header, text="No Selection", bg="#333333", fg="#33A1FD", font=("Arial", 8))
        self.path_lbl.pack(side="right", padx=10)

        self.canvas = tk.Canvas(self, bg="#2b2b2b", bd=0, highlightthickness=0)
        self.scrollbar = AutoScrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scroll_frame = tk.Frame(self.canvas, bg="#2b2b2b")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas_win = self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        
        self.scroll_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self.canvas_win, width=max(1, e.width)))
        
        # Initial placeholder message
        tk.Label(self.scroll_frame, text="Select a widget to edit properties.", bg="#2b2b2b", fg="#888888").pack(pady=50)

    def _on_cleanup(self, event):
        if event.widget == self:
            event_bus.unsubscribe("FOCUS_REQUESTED", self._on_focus_requested)
            event_bus.unsubscribe("STATE_UPDATED", self._on_state_updated)

    def _on_state_updated(self, json_data, source=None):
        # Only refresh if the focused path is still valid and the update didn't come from this widget itself.
        # Debounce the refresh to avoid excessive updates.
        if source == self or not self.focused_path: return
        self._request_debounced_refresh()

    def _normalize_path(self, path):
        """Standardizes path strings for internal resolution."""
        if not path: return ""
        normalized = str(path).strip().strip('.')
        if normalized.lower() == "root": return ""
        
        # 🛡️ HEURISTIC: Handle missing root key from layout
        full_state = state_manager.get_state()
        if full_state:
            root_keys = list(full_state.keys())
            if len(root_keys) == 1:
                root_name = root_keys[0]
                if not normalized.startswith(root_name) and not normalized.startswith(f"{root_name}."):
                    candidate = f"{root_name}.{normalized}"
                    if state_manager.get_value_at_path(candidate) is not None:
                        normalized = candidate
        return normalized

    def _on_focus_requested(self, path, source=None):
        if not self.winfo_exists(): return
        
        clean_path = self._normalize_path(path)
        self.focused_path = clean_path
        
        matrix_log("ui", "gui_builder", "element_properties", f"🖱️🖱️🖱️ [ACTION] ElementProperties: Focus synchronization for path: {path} (Clean: {clean_path})", "INFO")
        self._refresh_content()

    def _request_debounced_refresh(self, delay=1500):
        if self._refresh_job: self.after_cancel(self._refresh_job)
        self._refresh_job = self.after(delay, self._refresh_content)

    def _refresh_content(self):
        if not self.focused_path or not self.winfo_exists(): return
        
        # ⚡ LOGGING: Trace refresh activity
        matrix_log("ui", "gui_builder", "element_properties", f"🎨 [RENDER] ElementProperties: Refreshing content for {self.focused_path}", "DEBUG")

        # CLEANUP: Clear existing content
        for child in self.scroll_frame.winfo_children():
            child.destroy()

        self.path_lbl.config(text=f"Path: {self.focused_path}")

        actual_data = state_manager.get_value_at_path(self.focused_path)
        if actual_data is None: 
            tk.Label(self.scroll_frame, text="Selected element not found in state.", bg="#2b2b2b", fg="#ff4444").pack(pady=50)
            return

        # 1. Prepare rendering data (Merge with Schema)
        display_data = actual_data
        if isinstance(actual_data, dict):
            w_type = actual_data.get("type", actual_data.get("widget_type"))
            schema_template = next((c.get("schema", {}) for n, c in self.library.items() if c["type"] == w_type), {})
            if schema_template:
                display_data = self._deep_merge(schema_template, actual_data)

        # 2. Render quick tools (alignment, sticky) if it's a widget
        if isinstance(actual_data, dict) and (actual_data.get("type") or actual_data.get("widget_type")):
            tools = tk.Frame(self.scroll_frame, bg="#252525", pady=10)
            tools.pack(fill="x", pady=(0, 10))
            self._render_alignment_quick_tools(actual_data, tools)
            self._render_sticky_quick_tools(actual_data, tools)

        # 3. Render the recursive property tree
        new_widget_cache = {}
        if isinstance(display_data, dict):
            self._render_recursive_properties(display_data, self.scroll_frame,
                                            prefix=self.focused_path,
                                            actual_data=actual_data,
                                            widget_cache=self.widget_cache,
                                            new_widget_cache=new_widget_cache)
        else:
            # Handle primitive leaf (e.g. state_manager pointing directly to a string)
            from ..factories.leaf_editor_factory import LeafEditorFactory
            LeafEditorFactory.create(self.scroll_frame, self.focused_path.split(".")[-1], actual_data, self.focused_path, self)

        # 4. Lifecycle management: Destroy unused widgets from previous cache
        for full_path, widget_info in self.widget_cache.items():
            if full_path not in new_widget_cache:
                widget = widget_info.get("widget")
                if widget and widget.winfo_exists(): widget.destroy()

        self.widget_cache = new_widget_cache

    def _deep_merge(self, template, actual):
        if not isinstance(template, dict) or not isinstance(actual, dict): return actual
        result = template.copy()
        for k, v in actual.items():
            result[k] = self._deep_merge(result[k], v) if k in result and isinstance(result[k], dict) and isinstance(v, dict) else v
        return result
