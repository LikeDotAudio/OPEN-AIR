import inspect
from oaLogging.Methods.matrix_gate import matrix_log
# workspaces/interactive_layout.py
# Author: Anthony Peter Kuzub
# Version: 20260315.Modular.1
#
# Description: Modularized Interactive Layout Workspace.

import tkinter as tk
from tkinter import ttk
# --- Standard Debug Logging Setup ---
from oaLogging.Core.logger import GUI_LOGGER as logger

from ..event_bus import event_bus
from ..state import state_manager

# --- EXTRACTED CORE MODULES ---
from .Core.layout.preview_engine import PreviewEngine
from .Core.layout.focus import FocusManager
from .Core.layout.overlay import OverlayManager

class InteractiveLayout(tk.Frame):
    """The visual workspace where users interact with the GUI layout."""

    def __init__(self, parent, *args, **kwargs):
        kwargs.pop("bg", None)
        super().__init__(parent, bg="#1a1a1a", *args, **kwargs)
        matrix_log("ui", "gui_builder", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "InteractiveLayout: Initializing workspace...", "DEBUG")
        
        # Display Toggles
        self.show_structure = tk.BooleanVar(value=True)
        self.show_blocks = tk.BooleanVar(value=True)
        self.show_columns = tk.BooleanVar(value=True)
        self.show_sizing = tk.BooleanVar(value=True)
        self.show_sticky = tk.BooleanVar(value=True)
        self.show_alignment = tk.BooleanVar(value=True)
        self.show_colors = tk.BooleanVar(value=True)
        
        self.render_tier_var = tk.StringVar(value="High-Res") # Default value
        self.auto_rebuild_var = tk.BooleanVar(value=True) # Default to auto-rebuild
        self.show_background_var = tk.BooleanVar(value=True) # Toggle for background visibility
        
        self.focused_path = None
        self.pending_changes = 0
        self._refresh_timer = None

        from oaGuiManager.Core.factory.widget_registry import WidgetRegistry
        WidgetRegistry.scan_widgets()
        
        self._build_ui()
        
        # Initialize render_area after header to ensure correct packing order
        self.render_area = tk.Frame(self, bg="#2b2b2b")
        self.render_area.pack(fill="both", expand=True)
        
        # Engines
        self.focus_mgr = FocusManager(self)
        self.preview_engine = PreviewEngine(self.render_area, self.focus_mgr.handle_focus_request)
        self.overlay_mgr = OverlayManager(self)
        self.overlay_mgr.create_event_blocker(self.render_area) # Create the event blocking canvas
        self.preview_builder = None
        
        # Initial subscription for STATE_UPDATED is now managed by _toggle_auto_rebuild()
        event_bus.subscribe("FOCUS_REQUESTED", self._on_external_focus)
        self.bind("<Destroy>", self._on_destroy)
        
        # Call _toggle_auto_rebuild to set up initial subscription state
        self._toggle_auto_rebuild() 

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
        if self.auto_rebuild_var.get(): # Only refresh if auto-rebuild is enabled
            self._refresh_preview()

    def _on_external_focus(self, path, source=None):
        if not self.winfo_exists() or source == self: return
        self.focused_path = path
        if self.preview_builder: self.overlay_mgr.apply_outlines(self.preview_builder.scroll_frame)

    def _on_render_tier_change(self, event=None):
        """Callback when the render tier dropdown selection changes."""
        selected_tier = self.render_tier_var.get()
        # Map UI text to internal keys if necessary
        render_tier_map = {
            "High-Res": "high_res",
            "Fast": "fast",
            "Ghost": "ghost"
        }
        internal_tier = render_tier_map.get(selected_tier, "high_res")
        
        if self.preview_builder:
            # The refresh method in preview_engine takes the render_tier
            # It will then pass it to self.preview_builder._render_tier
            self.preview_engine.refresh(state_manager.get_state(), render_tier=internal_tier)
            # Ensure overlays are refreshed too, as they might depend on render tier
            self.overlay_mgr.apply_outlines(self.preview_builder.scroll_frame) 
        
    def _toggle_auto_rebuild(self):
        """Toggles the auto-rebuild behavior."""
        if self.auto_rebuild_var.get():
            event_bus.subscribe("STATE_UPDATED", self._on_state_updated)
            self._manual_rebuild() # Rebuild immediately if auto-rebuild is turned on
        else:
            event_bus.unsubscribe("STATE_UPDATED", self._on_state_updated)
            self.pending_changes = 0 # Clear pending changes if auto-rebuild is off
            self._update_rebuild_ui() # Refresh UI to reflect cleared pending changes

    def _build_ui(self):
        header = tk.Frame(self, bg="#333333", height=35)
        header.pack(side="top", fill="x")
        
        tk.Label(header, text="INTERACTIVE LAYOUT", bg="#333333", fg="white", font=("Arial", 9, "bold")).pack(side="left", padx=10, pady=5)

        # --- New Render Tier Dropdown ---
        render_tier_frame = tk.Frame(header, bg="#333333")
        render_tier_frame.pack(side="left", padx=10)
        tk.Label(render_tier_frame, text="Render:", bg="#333333", fg="#aaaaaa", font=("Arial", 8, "bold")).pack(side="left", padx=2)
        self.render_tier_combo = ttk.Combobox(
            render_tier_frame, 
            textvariable=self.render_tier_var, 
            values=["High-Res", "Fast", "Ghost"], 
            state="readonly", 
            width=10,
            background="#333333", # Set background for combobox
            foreground="#aaaaaa" # Set foreground for combobox
        )
        self.render_tier_combo.pack(side="left", padx=2)
        self.render_tier_combo.bind("<<ComboboxSelected>>", self._on_render_tier_change)
        
        # --- New Auto-Rebuild Checkbox ---
        self.auto_rebuild_cb = ttk.Checkbutton(header, text="Auto-Rebuild", variable=self.auto_rebuild_var, command=self._toggle_auto_rebuild, onvalue=True, offvalue=False)
        self.auto_rebuild_cb.pack(side="left", padx=10)

        # --- New Background Visibility Toggle ---
        self.background_visibility_cb = ttk.Checkbutton(header, text="Background", variable=self.show_background_var, command=self._toggle_background_visibility, onvalue=True, offvalue=False)
        self.background_visibility_cb.pack(side="left", padx=10)

        # --- Rebuild Controls ---
        rebuild_frame = tk.Frame(header, bg="#333333")
        rebuild_frame.pack(side="left", padx=10)
        
        self.rebuild_btn = tk.Button(rebuild_frame, text="REBUILD", bg="black", fg="#00ff00", font=("Arial", 8, "bold"), relief="flat", padx=10, command=self._manual_rebuild)
        self.rebuild_btn.pack(side="left", padx=5)
        
        self.counter_lbl = tk.Label(rebuild_frame, text="CHANGES MADE: 0", bg="#333333", fg="#aaaaaa", font=("Arial", 8, "bold"))
        self.counter_lbl.pack(side="left", padx=5)

        controls = [("Structure", self.show_structure), ("Blocks", self.show_blocks), ("Columns", self.show_columns), ("Sizing", self.show_sizing), ("Sticky", self.show_sticky), ("Alignment", self.show_alignment), ("Colors", self.show_colors)]
        for text, var in reversed(controls):
            ttk.Checkbutton(header, text=text, variable=var, command=self._force_overlay_refresh).pack(side="right", padx=5)

        self.render_area = tk.Frame(self, bg="#2b2b2b"); self.render_area.pack(fill="both", expand=True)

    def _toggle_background_visibility(self):
        """Toggles the visibility of the background in the preview."""
        # The actual logic to show/hide the background will depend on how the background is implemented
        # in the preview_builder. For now, this method ensures the command doesn't raise an error.
        # If background is a widget, e.g., self.preview_builder.background_widget,
        # then it might be self.preview_builder.background_widget.pack_forget() or .pack()
        # or self.preview_builder.background_widget.grid_forget() or .grid()
        # For now, we ensure the method exists.
        matrix_log("ui", "gui_builder", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"Background visibility toggled to: {self.show_background_var.get()}", "DEBUG")
        # Placeholder: actual background visibility logic needs to be implemented if it affects preview rendering.
        pass

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
        if self.preview_builder: 
            self.overlay_mgr.apply_outlines(self.preview_builder.scroll_frame)
            # Explicitly trigger background update in the builder
            if hasattr(self.preview_builder, '_update_background'):
                self.preview_builder._update_background()

    def _refresh_preview(self, json_data=None):
        if not self.winfo_exists() or not hasattr(self, 'render_area'): return
        if json_data is None: json_data = state_manager.get_state()
        
        self.preview_builder = self.preview_engine.refresh(json_data)
        # Raise the event blocker canvas above the newly rendered preview_builder
        if self.overlay_mgr.event_blocker_canvas:
            self.tk.call('raise', self.overlay_mgr.event_blocker_canvas._w)
        self.after(250, lambda: self.overlay_mgr.apply_outlines(self.preview_builder.scroll_frame))
