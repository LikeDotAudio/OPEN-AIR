# workers/wysiwyg_editor/workspaces/element_properties.py
# Modularized Element Properties Workspace.
# Version 20260315.Modular.1

import tkinter as tk
from tkinter import ttk, messagebox
from ..core.event_bus import event_bus
from ..core.state_manager import state_manager
from ..grab_bag.grab_bag_loader import GrabBagLoader
from loguru import logger

# --- EXTRACTED CORE MODULES ---
from .core.structural_manager_mixin import StructuralManagerMixin
from .core.layout_tools_mixin import LayoutToolsMixin
from .core.property_renderer_mixin import PropertyRendererMixin

LOCAL_DEBUG = True

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

    def __init__(self, parent, *args, **kwargs):
        kwargs.pop("bg", None)
        super().__init__(parent, bg="#2b2b2b", *args, **kwargs)
        
        self.focused_path = None
        self.scrub_start_val, self.scrub_start_x = 0, 0
        self._refresh_job = None
        self.library = GrabBagLoader().scan_library()

        self._setup_styles()
        self._build_ui()
        
        event_bus.subscribe("FOCUS_REQUESTED", self._on_focus_requested)
        event_bus.subscribe("STATE_UPDATED", self._on_state_updated)
        self.bind("<Destroy>", self._on_cleanup)

    def _setup_styles(self):
        style = ttk.Style()
        style.configure("Property.TEntry", fieldbackground="#1e1e1e", foreground="#dcdcdc", 
                        insertcolor="white", bordercolor="#444444")

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
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self.canvas_win, width=e.width))
        
        tk.Label(self.scroll_frame, text="Select a widget to edit properties.", bg="#2b2b2b", fg="#888888").pack(pady=50)

    def _on_cleanup(self, event):
        if event.widget == self:
            event_bus.unsubscribe("FOCUS_REQUESTED", self._on_focus_requested)
            event_bus.unsubscribe("STATE_UPDATED", self._on_state_updated)

    def _on_state_updated(self, json_data, source=None):
        if source == self or not self.focused_path: return
        self._request_debounced_refresh()

    def _on_focus_requested(self, path, source=None):
        if not self.winfo_exists(): return
        self.focused_path = path
        self._refresh_content()

    def _request_debounced_refresh(self, delay=1500):
        if self._refresh_job: self.after_cancel(self._refresh_job)
        self._refresh_job = self.after(delay, self._refresh_content)

    def _refresh_content(self):
        if not self.focused_path or not self.winfo_exists(): return
        for child in self.scroll_frame.winfo_children(): child.destroy()
        self.path_lbl.config(text=f"Path: {self.focused_path}")

        actual_data = state_manager.get_value_at_path(self.focused_path)
        if actual_data is None: return

        if isinstance(actual_data, dict) and (actual_data.get("type") or actual_data.get("widget_type")):
            tools = tk.Frame(self.scroll_frame, bg="#252525", pady=10)
            tools.pack(fill="x", pady=(0, 10))
            self._render_alignment_quick_tools(actual_data, tools)
            self._render_sticky_quick_tools(actual_data, tools)

        if isinstance(actual_data, dict):
            w_type = actual_data.get("type", actual_data.get("widget_type"))
            schema = next((c.get("schema", {}) for n, c in self.library.items() if c["type"] == w_type), {})
            display_data = self._deep_merge(schema, actual_data)
            self._render_recursive_properties(display_data, self.scroll_frame, prefix=self.focused_path, actual_data=actual_data)
        else:
            from .core.leaf_editor_factory import LeafEditorFactory
            LeafEditorFactory.create(self.scroll_frame, self.focused_path.split(".")[-1], actual_data, self.focused_path, self)

    def _deep_merge(self, template, actual):
        if not isinstance(template, dict) or not isinstance(actual, dict): return actual
        res = template.copy()
        for k, v in actual.items():
            res[k] = self._deep_merge(res[k], v) if k in res and isinstance(res[k], dict) and isinstance(v, dict) else v
        return res
