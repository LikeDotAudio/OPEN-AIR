# workers/wysiwyg_editor/workspaces/interactive_layout.py
# Modularized Interactive Layout Workspace.
# Version 20260315.Modular.1

import tkinter as tk
from tkinter import ttk
from loguru import logger

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True

from ..Core.event_bus import event_bus
from ..Core.state import state_manager

# --- EXTRACTED CORE MODULES ---
from .Core.layout.preview_engine import PreviewEngine
from .Core.layout.focus import FocusManager
from .Core.layout.overlay import OverlayManager

class InteractiveLayout(tk.Frame):
    """The visual workspace where users interact with the GUI layout."""

    def __init__(self, parent, *args, **kwargs):
        kwargs.pop("bg", None)
        super().__init__(parent, bg="#1a1a1a", *args, **kwargs)
        if LOCAL_DEBUG: logger.debug("📐 InteractiveLayout: Initializing workspace...")
        
        # Display Toggles
        self.show_structure = tk.BooleanVar(value=True)
        self.show_blocks = tk.BooleanVar(value=True)
        self.show_columns = tk.BooleanVar(value=True)
        self.show_sizing = tk.BooleanVar(value=True)
        self.show_sticky = tk.BooleanVar(value=True)
        self.show_alignment = tk.BooleanVar(value=True)
        self.show_colors = tk.BooleanVar(value=True)
        
        self.focused_path = None
        self.pending_changes = 0
        self._refresh_timer = None
        
        from oaGuiManager.Core.factory.widget_registry import WidgetRegistry
        WidgetRegistry.scan_widgets()
        
        self._build_ui()
        
        # Engines
        self.focus_mgr = FocusManager(self)
        self.preview_engine = PreviewEngine(self.render_area, self.focus_mgr.handle_focus_request)
        self.overlay_mgr = OverlayManager(self)
        self.preview_builder = None
        
        event_bus.subscribe("STATE_UPDATED", self._on_state_updated)
        event_bus.subscribe("FOCUS_REQUESTED", self._on_external_focus)
        self.bind("<Destroy>", self._on_destroy)

        self.after(100, self._initial_startup_sync)

    def _initial_startup_sync(self):
        self._manual_rebuild()
        self.pending_changes = 1
        self._update_rebuild_ui()

    def _on_destroy(self, event):
        if event.widget == self:
            if self._refresh_timer: self.after_cancel(self._refresh_timer)
            event_bus.unsubscribe("STATE_UPDATED", self._on_state_updated)
            event_bus.unsubscribe("FOCUS_REQUESTED", self._on_external_focus)

    def _on_state_updated(self, json_data, source=None):
        if not self.winfo_exists() or source == self: return
        self.pending_changes += 1
        self._update_rebuild_ui()

    def _on_external_focus(self, path, source=None):
        if not self.winfo_exists() or source == self: return
        self.focused_path = path
        if self.preview_builder: self.overlay_mgr.apply_outlines(self.preview_builder.scroll_frame)

    def _build_ui(self):
        header = tk.Frame(self, bg="#333333", height=35)
        header.pack(side="top", fill="x")
        
        tk.Label(header, text="INTERACTIVE LAYOUT", bg="#333333", fg="white", font=("Arial", 9, "bold")).pack(side="left", padx=10, pady=5)
        
        rebuild_frame = tk.Frame(header, bg="#333333"); rebuild_frame.pack(side="left", padx=20)
        self.rebuild_btn = tk.Button(rebuild_frame, text="REBUILD", bg="black", fg="#00ff00", font=("Arial", 8, "bold"), relief="flat", padx=10, command=self._manual_rebuild)
        self.rebuild_btn.pack(side="left", padx=5)
        
        self.counter_lbl = tk.Label(rebuild_frame, text="CHANGES MADE: 0", bg="#333333", fg="#aaaaaa", font=("Arial", 8, "bold"))
        self.counter_lbl.pack(side="left", padx=5)

        controls = [("Structure", self.show_structure), ("Blocks", self.show_blocks), ("Columns", self.show_columns), ("Sizing", self.show_sizing), ("Sticky", self.show_sticky), ("Alignment", self.show_alignment), ("Colors", self.show_colors)]
        for text, var in reversed(controls):
            ttk.Checkbutton(header, text=text, variable=var, command=self._force_overlay_refresh).pack(side="right", padx=5)

        self.render_area = tk.Frame(self, bg="#2b2b2b"); self.render_area.pack(fill="both", expand=True)

    def _update_rebuild_ui(self):
        self.counter_lbl.config(text=f"CHANGES MADE: {self.pending_changes}")
        if self.pending_changes > 0: self.counter_lbl.config(fg="#FF9900"); self.rebuild_btn.config(bg="#222222")
        else: self.counter_lbl.config(fg="#aaaaaa"); self.rebuild_btn.config(bg="black")

    def _manual_rebuild(self):
        self.pending_changes = 0; self._update_rebuild_ui(); self._refresh_preview()

    def _on_widget_focused(self, path):
        """Internal callback for selection events."""
        event_bus.publish("FOCUS_REQUESTED", path=path, source=self)

    def _force_overlay_refresh(self):
        if self.preview_builder: self.overlay_mgr.apply_outlines(self.preview_builder.scroll_frame)

    def _refresh_preview(self, json_data=None):
        if not self.winfo_exists() or not hasattr(self, 'render_area'): return
        if json_data is None: json_data = state_manager.get_state()
        
        self.preview_builder = self.preview_engine.refresh(json_data)
        self.after(250, lambda: self.overlay_mgr.apply_outlines(self.preview_builder.scroll_frame))
