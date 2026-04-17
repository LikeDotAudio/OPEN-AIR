# Interface/Tabs/ElementProperties/Entry.py
#
# The Element Properties Workspace.
# Provides a high-level UI for adjusting parameters of the focused element.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Professional services for customizing and tailoring this software to your specific
# application can be negotiated. There is no charge to use, modify, or fork this software.
#
# Build Log: https://like.audio/category/software/spectrum-scanner/
# Source Code: https://github.com/APKaudio/
# Feature Requests can be emailed to i @ like . audio
#
# Version 20260417.0100.1
#
# Responsibilities (UI Partition):
# - Synchronize property views with the globally focused widget path.
# - Recursively render property editors based on component schemas.
# - Dispatch debounced state updates back to the Core StateManager.
# - Provide quick-access tools for alignment, sticky, and geometry.
#
# Hard Constraints:
# - Requires a populated library cache for schema-based rendering.
# - Relies on PropertyLeaf for primitive value manipulation.


import tkinter as tk
from tkinter import ttk
from oaComBroker.Core.event_bus import event_bus
from ....Core.state import state_manager
from ....FileReaders.grab_bag_loader import GrabBagLoader
from oaLogging.Methods.matrix_gate import matrix_log

# --- MODULAR IMPORTS ---
from .Interface.properties_ui import PropertiesUI
from .Managers.properties_refresh_manager import PropertiesRefreshManager
from .Methods.path_resolver import normalize_path

# --- MIXINS (To be modularized next phase) ---
from ...mixins.structural_mixin import StructuralManagerMixin
from ...mixins.layout_tools_mixin import LayoutToolsMixin
from ...mixins.property_renderer_mixin import PropertyRendererMixin

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
        self._refresh_job = None
        self.library = library_cache if library_cache is not None else GrabBagLoader().scan_library()

        # 1. Setup UI
        self.ui = PropertiesUI(self, self._delete_focused_element).build()
        self.scroll_frame = self.ui.scroll_frame # For mixin compatibility

        # 2. Setup Managers
        self.refresh_mgr = PropertiesRefreshManager(self, self.ui, self.library)
        self.widget_cache = self.refresh_mgr.widget_cache # Alias for compatibility

        # 3. Setup Styles
        self._setup_styles()

        # 4. Global Subscriptions
        event_bus.subscribe("FOCUS_REQUESTED", self._on_focus_requested)
        event_bus.subscribe("STATE_UPDATED", self._on_state_updated)
        self.bind("<Destroy>", self._on_cleanup)

    def _setup_styles(self):
        style = ttk.Style()
        style.configure("Property.TEntry", fieldbackground="#1e1e1e", foreground="#dcdcdc", 
                        insertcolor="white", bordercolor="#444444", font=("Arial", 8))

    def highlight_item(self, element_id):
        """Visual feedback when an item is clicked on the canvas."""
        self.config(highlightbackground="#007acc", highlightthickness=2)
        self.after(500, lambda: self.config(highlightthickness=0))

    def _on_cleanup(self, event):
        if event.widget == self:
            event_bus.unsubscribe("FOCUS_REQUESTED", self._on_focus_requested)
            event_bus.unsubscribe("STATE_UPDATED", self._on_state_updated)

    def _on_state_updated(self, json_data, source=None):
        if source == self or not self.focused_path: return
        self._request_debounced_refresh()

    def _on_focus_requested(self, path, source=None):
        if not self.winfo_exists(): return
        
        clean_path = normalize_path(path, state_manager)
        self.focused_path = clean_path
        
        matrix_log("ui", "gui_builder", "element_properties", f"🖱️🖱️🖱️ [ACTION] ElementProperties: Focus synchronization for path: {path} (Clean: {clean_path})", "INFO")
        self._refresh_content()

    def _request_debounced_refresh(self, delay=1500):
        if self._refresh_job: self.after_cancel(self._refresh_job)
        self._refresh_job = self.after(delay, self._refresh_content)

    def _refresh_content(self):
        self.refresh_mgr.refresh(self.focused_path)
        # Keep internal cache reference in sync if manager re-assigns
        self.widget_cache = self.refresh_mgr.widget_cache
