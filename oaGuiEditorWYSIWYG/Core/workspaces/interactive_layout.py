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

from oaComBroker.Core.event_bus import event_bus
from ..state import state_manager
from oaGui.Methods.safe_after_mixin import SafeAfterMixin

# --- EXTRACTED CORE MODULES ---
from .Core.layout.preview_engine import PreviewEngine
from .Core.layout.focus import FocusManager
from .Core.layout.overlay import OverlayManager
from .Core.layout.ruler import Ruler
from .Core.layout.ghost_overlay import GhostOverlay

class InteractiveLayout(tk.Frame, SafeAfterMixin):
    """The visual workspace where users interact with the GUI layout."""

    def __init__(self, parent, *args, **kwargs):
        self._init_safe_after()
        kwargs.pop("bg", None)
        super().__init__(parent, bg="#1a1a1a", *args, **kwargs)
        matrix_log("ui", "gui_builder", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "InteractiveLayout: Initializing workspace...", "DEBUG")
        
        # Display Toggles - Defaulting all to False per user request
        self.show_structure = tk.BooleanVar(value=False)
        self.show_blocks = tk.BooleanVar(value=False)
        self.show_columns = tk.BooleanVar(value=False)
        self.show_sizing = tk.BooleanVar(value=False)
        self.show_sticky = tk.BooleanVar(value=False)
        self.show_alignment = tk.BooleanVar(value=False)
        self.show_colors = tk.BooleanVar(value=False)
        
        self.render_tier_var = tk.StringVar(value="Fast") # Default value to Fast per user request
        self.auto_rebuild_var = tk.BooleanVar(value=False) # Default to manual rebuild per user request
        self.show_background_var = tk.BooleanVar(value=False) # Toggle for background visibility - Default Off
        self.superficial_pad_var = tk.IntVar(value=0) # Superficial padding for editor spacing
        
        self.focused_path = None
        self.pending_changes = 0
        self._refresh_timer = None

        from oaGuiManager.Core.factory.widget_registry import WidgetRegistry
        WidgetRegistry.scan_widgets()
        
        self._build_ui()
        
        # --- Ruler Containers ---
        # ⚡ ADJUSTED: Rulers now start at y=0 as the header is removed.
        self.ruler_corner = tk.Frame(self, bg="#1a1a1a", width=20, height=20)
        self.ruler_corner.place(x=0, y=0) 
        
        self.h_ruler = Ruler(self, orient="horizontal")
        self.h_ruler.place(x=20, y=0, relwidth=1, width=-20, height=20)
        
        self.v_ruler = Ruler(self, orient="vertical")
        self.v_ruler.place(x=0, y=20, width=20, relheight=1, height=-20)

        # Initialize render_area after rulers
        self.render_area = tk.Frame(self, bg="#2b2b2b")
        self.render_area.place(x=20, y=20, relwidth=1, relheight=1, width=-20, height=-20)
        
        # 👻 GHOST LAYER: High-speed interaction layer
        self.ghost_overlay = GhostOverlay(self.render_area)
        # ⚡ HIDDEN BY DEFAULT: So it doesn't block clicks on the grid
        self.ghost_overlay.place_forget() 
        
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

        self.safe_after(100, self._initial_startup_sync)

    def _initial_startup_sync(self):
        self._manual_rebuild()
        self.pending_changes = 1
        self._update_rebuild_ui()

    def _on_destroy(self, event):
        if event.widget == self:
            self._cleanup_safe_after()
            if self._refresh_timer: self.safe_after_cancel(self._refresh_timer)
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
        """Headers are now managed by the main application menu."""
        pass

    def _sync_rulers(self, event=None):
        """Syncs ruler offsets and center points with the preview canvas."""
        if not self.preview_builder: return
        
        # Get canvas scroll offsets
        x_scroll = self.preview_builder.canvas.xview()
        y_scroll = self.preview_builder.canvas.yview()
        
        # Calculate pixel offsets
        # scrollregion is (x1, y1, x2, y2)
        sr = self.preview_builder.canvas.cget("scrollregion")
        if not sr: return
        
        sr_parts = [float(p) for p in sr.split()]
        full_w = sr_parts[2] - sr_parts[0]
        full_h = sr_parts[3] - sr_parts[1]
        
        off_x = int(x_scroll[0] * full_w)
        off_y = int(y_scroll[0] * full_h)
        
        self.h_ruler.set_offset(off_x)
        self.v_ruler.set_offset(off_y)
        
        # Set centers
        self.h_ruler.set_center(full_w // 2)
        self.v_ruler.set_center(full_h // 2)

    def _refresh_preview(self):
        """Throttled refresh of the preview."""
        if self._refresh_timer:
            self.safe_after_cancel(self._refresh_timer)
        self._refresh_timer = self.safe_after(200, self._perform_refresh)

    def _perform_refresh(self):
        self._refresh_timer = None
        self.preview_builder = self.preview_engine.refresh(
            state_manager.get_state(),
            render_tier=self.render_tier_var.get().lower(),
            superficial_pad=self.superficial_pad_var.get()
        )
        # Bind scroll events for ruler syncing
        if self.preview_builder:
            self.preview_builder.canvas.bind("<Configure>", lambda e: self.safe_after(100, self._sync_rulers), add="+")
            # We also need to catch the actual scrolling.
            # Using <Motion> and <Button-1> as proxies for interaction that might cause scrolling
            self.preview_builder.canvas.bind("<Motion>", self._sync_rulers, add="+")
            self.preview_builder.canvas.bind("<Button-1>", self._sync_rulers, add="+")
            self._sync_rulers()

    def _toggle_background_visibility(self):
        """Toggles the visibility of the background in the preview."""
        matrix_log("ui", "gui_builder", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"Background visibility toggled to: {self.show_background_var.get()}", "DEBUG")
        if self.preview_builder:
            # Explicitly trigger background update in the builder
            if hasattr(self.preview_builder, '_update_background'):
                self.preview_builder._update_background()

    def _update_rebuild_ui(self):
        # ⚡ STANDALONE: Update labels/buttons only if they exist (they moved to Menu)
        if hasattr(self, 'counter_lbl') and self.counter_lbl.winfo_exists():
            self.counter_lbl.config(text=f"CHANGES MADE: {self.pending_changes}")
            if self.pending_changes > 0: self.counter_lbl.config(fg="#FF9900")
            else: self.counter_lbl.config(fg="#aaaaaa")
        
        # We can also notify the main editor status bar via EventBus if needed
        event_bus.publish("CHANGES_PENDING", count=self.pending_changes)

    def fill_menus(self, menubar):
        """Populates the provided menubar with layout-specific controls."""
        # 1. RENDER Menu
        render_menu = tk.Menu(menubar, tearoff=0)
        render_menu.add_command(label="Force Rebuild", command=self._manual_rebuild, accelerator="Ctrl+R")
        render_menu.add_separator()
        
        # Render Tier Submenu
        tier_menu = tk.Menu(render_menu, tearoff=0)
        for tier in ["High-Res", "Fast", "Ghost"]:
            tier_menu.add_radiobutton(label=tier, variable=self.render_tier_var, 
                                      value=tier, command=self._on_render_tier_change)
        render_menu.add_cascade(label="Render Tier", menu=tier_menu)
        
        render_menu.add_checkbutton(label="Auto-Rebuild", variable=self.auto_rebuild_var, 
                                    command=self._toggle_auto_rebuild)
        render_menu.add_checkbutton(label="Show Background", variable=self.show_background_var, 
                                    command=self._toggle_background_visibility)
        menubar.add_cascade(label="RENDER", menu=render_menu)
        
        # 2. GRID Menu
        grid_menu = tk.Menu(menubar, tearoff=0)
        pad_menu = tk.Menu(grid_menu, tearoff=0)
        for i in range(11):
            pad_menu.add_radiobutton(label=f"PAD {i}px", variable=self.superficial_pad_var, 
                                     value=i, command=self._manual_rebuild)
        grid_menu.add_cascade(label="Spacing (PAD)", menu=pad_menu)
        menubar.add_cascade(label="GRID", menu=grid_menu)
        
        # 3. VIEW Menu (Overlays)
        view_menu = tk.Menu(menubar, tearoff=0)
        
        # VIEW ALL TOGGLE
        self.view_all_var = tk.BooleanVar(value=False)
        view_menu.add_checkbutton(label="VIEW ALL", variable=self.view_all_var, 
                                  command=self._toggle_all_overlays, font=("Arial", 9, "bold"))
        view_menu.add_separator()

        controls = [
            ("Structure", self.show_structure), 
            ("Blocks", self.show_blocks), 
            ("Columns", self.show_columns), 
            ("Sizing", self.show_sizing), 
            ("Sticky", self.show_sticky), 
            ("Alignment", self.show_alignment), 
            ("Colors", self.show_colors)
        ]
        for text, var in controls:
            view_menu.add_checkbutton(label=text, variable=var, command=self._force_overlay_refresh)
        menubar.add_cascade(label="VIEW", menu=view_menu)

    def _toggle_all_overlays(self):
        """Toggles all design overlays at once."""
        state = self.view_all_var.get()
        self.show_structure.set(state)
        self.show_blocks.set(state)
        self.show_columns.set(state)
        self.show_sizing.set(state)
        self.show_sticky.set(state)
        self.show_alignment.set(state)
        self.show_colors.set(state)
        self._force_overlay_refresh()

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
