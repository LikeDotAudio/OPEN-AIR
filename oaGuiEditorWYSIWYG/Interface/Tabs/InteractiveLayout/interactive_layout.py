import inspect
from oaLogging.Methods.matrix_gate import matrix_log
# Interface/Tabs/InteractiveLayout/interactive_layout.py
# Author: Anthony Peter Kuzub
# Version: 20260416.Interface.1
#
# Description: Refactored Interactive Layout Workspace with modular components.

import tkinter as tk
from tkinter import ttk
from oaLogging.Core.logger import GUI_LOGGER as logger
from oaComBroker.Core.event_bus import event_bus
from ....Core.state import state_manager
from oaGui.Methods.safe_after_mixin import SafeAfterMixin

# --- MODULAR CORE COMPONENTS ---
from ...layout_engine.preview_engine import PreviewEngine
from ...layout_engine.focus import FocusManager
from ...layout_engine.overlay_manager import OverlayManager
from ...layout_engine.ruler import Ruler
from ...layout_engine.ghost_overlay import GhostOverlay

class InteractiveLayout(tk.Frame, SafeAfterMixin):
    """The visual workspace where users interact with the GUI layout."""

    def __init__(self, parent, *args, **kwargs):
        self._init_safe_after()
        kwargs.pop("bg", None)
        super().__init__(parent, bg="#1a1a1a", *args, **kwargs)
        
        # Display Toggles
        self.show_structure = tk.BooleanVar(value=False)
        self.show_blocks = tk.BooleanVar(value=False)
        self.show_columns = tk.BooleanVar(value=False)
        self.show_sizing = tk.BooleanVar(value=False)
        self.show_sticky = tk.BooleanVar(value=False)
        self.show_alignment = tk.BooleanVar(value=False)
        self.show_colors = tk.BooleanVar(value=False)
        
        self.render_tier_var = tk.StringVar(value="Fast")
        self.auto_rebuild_var = tk.BooleanVar(value=False)
        self.show_background_var = tk.BooleanVar(value=False)
        self.superficial_pad_var = tk.IntVar(value=0)
        
        self.focused_path = None
        self.pending_changes = 0
        self._refresh_timer = None
        self._initial_render_done = False

        self._setup_engines()
        self._build_ui()
        
        event_bus.subscribe("STATE_UPDATED", self._on_state_updated)
        event_bus.subscribe("FOCUS_REQUESTED", self._on_external_focus)
        event_bus.subscribe("COMPONENT_DRAGGING", self._on_component_dragging)
        event_bus.subscribe("COMPONENT_DROPPED", self._on_component_dropped_global)
        
        self.bind("<Destroy>", self._on_destroy)
        self.bind("<Configure>", self._on_layout_configure)
        self.safe_after(100, self._initial_startup_sync)

    def _setup_engines(self):
        """Initializes modular layout and interaction engines."""
        self.focus_mgr = FocusManager(self)
        self.overlay_mgr = OverlayManager(self)
        self.preview_engine = None # Initialized after UI container is ready

    def _build_ui(self):
        # 1. Ruler Infrastructure
        self.ruler_corner = tk.Frame(self, bg="#1a1a1a", width=20, height=20)
        self.ruler_corner.place(x=0, y=0) 
        
        self.h_ruler = Ruler(self, orient="horizontal")
        self.h_ruler.place(x=20, y=0, relwidth=1, width=-20, height=20)
        
        self.v_ruler = Ruler(self, orient="vertical")
        self.v_ruler.place(x=0, y=20, width=20, relheight=1, height=-20)

        # 2. Main Render Canvas
        self.render_area = tk.Frame(self, bg="#2b2b2b")
        self.render_area.place(x=20, y=20, relwidth=1, relheight=1, width=-20, height=-20)
        
        # 3. Engines requiring UI context
        self.preview_engine = PreviewEngine(self.render_area, self.focus_mgr.handle_focus_request, workspace=self)
        self.overlay_mgr.create_event_blocker(self.render_area)
        
        # 4. Ghost Layer
        self.ghost_overlay = GhostOverlay(self.render_area)
        self.ghost_overlay.place_forget() 

    def _on_layout_configure(self, event):
        if not self._initial_render_done and event.width > 50:
            self._initial_render_done = True
            self._manual_rebuild()

    def _initial_startup_sync(self):
        if not self._initial_render_done:
            self._manual_rebuild()
            self._initial_render_done = True
        self.pending_changes = 0
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
        if self.auto_rebuild_var.get():
            self._refresh_preview()

    def _on_external_focus(self, path, source=None):
        if not self.winfo_exists() or source == self: return
        self.focused_path = path
        if self.preview_engine.preview_builder:
            self.overlay_mgr.apply_outlines(self.preview_engine.preview_builder.scroll_frame)

    def _on_render_tier_change(self, event=None):
        tier_map = {"High-Res": "high_res", "Fast": "fast", "Ghost": "ghost"}
        tier = tier_map.get(self.render_tier_var.get(), "high_res")
        if self.preview_engine.preview_builder:
            self.preview_engine.refresh(state_manager.get_state(), render_tier=tier)
            self.overlay_mgr.apply_outlines(self.preview_engine.preview_builder.scroll_frame) 
        
    def _toggle_auto_rebuild(self):
        if self.auto_rebuild_var.get(): self._manual_rebuild() 

    def _sync_rulers(self, event=None):
        builder = self.preview_engine.preview_builder
        if not builder: return
        x_scroll, y_scroll = builder.canvas.xview(), builder.canvas.yview()
        sr = builder.canvas.cget("scrollregion")
        if not sr: return
        sr_p = [float(p) for p in sr.split()]
        fw, fh = sr_p[2] - sr_p[0], sr_p[3] - sr_p[1]
        self.h_ruler.set_offset(int(x_scroll[0] * fw))
        self.v_ruler.set_offset(int(y_scroll[0] * fh))
        self.h_ruler.set_center(fw // 2)
        self.v_ruler.set_center(fh // 2)

    def _refresh_preview(self):
        if self._refresh_timer: self.safe_after_cancel(self._refresh_timer)
        self._refresh_timer = self.safe_after(200, self._perform_refresh)

    def _perform_refresh(self):
        self._refresh_timer = None
        builder = self.preview_engine.refresh(
            state_manager.get_state(),
            render_tier=self.render_tier_var.get().lower(),
            superficial_pad=self.superficial_pad_var.get()
        )
        if builder:
            builder.canvas.bind("<Configure>", lambda e: self.safe_after(100, self._sync_rulers), add="+")
            builder.canvas.bind("<Motion>", self._sync_rulers, add="+")
            builder.canvas.bind("<Button-1>", self._sync_rulers, add="+")
            self._sync_rulers()

    def _toggle_background_visibility(self):
        if self.preview_engine.preview_builder and hasattr(self.preview_engine.preview_builder, '_update_background'):
            self.preview_engine.preview_builder._update_background()

    def _update_rebuild_ui(self):
        event_bus.publish("CHANGES_PENDING", count=self.pending_changes)

    def fill_menus(self, menubar):
        # 1. RENDER Menu
        render_menu = tk.Menu(menubar, tearoff=0)
        render_menu.add_command(label="Force Rebuild", command=self._manual_rebuild, accelerator="Ctrl+R")
        render_menu.add_separator()
        tier_menu = tk.Menu(render_menu, tearoff=0)
        for t in ["High-Res", "Fast", "Ghost"]:
            tier_menu.add_radiobutton(label=t, variable=self.render_tier_var, value=t, command=self._on_render_tier_change)
        render_menu.add_cascade(label="Render Tier", menu=tier_menu)
        render_menu.add_checkbutton(label="Auto-Rebuild", variable=self.auto_rebuild_var, command=self._toggle_auto_rebuild)
        render_menu.add_checkbutton(label="Show Background", variable=self.show_background_var, command=self._toggle_background_visibility)
        menubar.add_cascade(label="RENDER", menu=render_menu)
        
        # 2. GRID Menu
        grid_menu = tk.Menu(menubar, tearoff=0)
        pad_menu = tk.Menu(grid_menu, tearoff=0)
        for i in range(11):
            pad_menu.add_radiobutton(label=f"PAD {i}px", variable=self.superficial_pad_var, value=i, command=self._manual_rebuild)
        grid_menu.add_cascade(label="Spacing (PAD)", menu=pad_menu)
        menubar.add_cascade(label="GRID", menu=grid_menu)
        
        # 3. VIEW Menu (Overlays)
        view_menu = tk.Menu(menubar, tearoff=0)
        self.view_all_var = tk.BooleanVar(value=False)
        view_menu.add_checkbutton(label="VIEW ALL", variable=self.view_all_var, command=self._toggle_all_overlays, font=("Arial", 9, "bold"))
        view_menu.add_separator()
        for text, var in [("Structure", self.show_structure), ("Blocks", self.show_blocks), ("Columns", self.show_columns), 
                         ("Sizing", self.show_sizing), ("Sticky", self.show_sticky), ("Alignment", self.show_alignment), ("Colors", self.show_colors)]:
            view_menu.add_checkbutton(label=text, variable=var, command=self._force_overlay_refresh)
        menubar.add_cascade(label="VIEW", menu=view_menu)

    def _toggle_all_overlays(self):
        state = self.view_all_var.get()
        self.show_structure.set(state); self.show_blocks.set(state); self.show_columns.set(state)
        self.show_sizing.set(state); self.show_sticky.set(state); self.show_alignment.set(state); self.show_colors.set(state)
        self._force_overlay_refresh()

    def _manual_rebuild(self):
        self.pending_changes = 0; self._update_rebuild_ui(); self._refresh_preview()

    def _on_component_dragging(self, x, y, name):
        """Handles real-time feedback for components being dragged from the Grab Bag."""
        if not self.winfo_exists(): return
        
        # 1. Ensure ghost overlay is visible
        self.ghost_overlay.place(x=0, y=0, relwidth=1, relheight=1)
        
        # 2. Find target and update visuals
        target = self.focus_mgr.find_drop_target_at(x, y)
        if target:
            tw, tp, tmode, tcoords = target
            self.ghost_overlay.draw_insertion_line(*tcoords)
        else:
            self.ghost_overlay.clear_insertion()

    def _on_component_dropped_global(self, x, y, name, schema):
        """Clears drag feedback when a component is dropped."""
        if not self.winfo_exists(): return
        self.ghost_overlay.clear()
        self.ghost_overlay.place_forget()

    def _on_widget_focused(self, path):
        event_bus.publish("FOCUS_REQUESTED", path=path, source=self)

    def _force_overlay_refresh(self):
        builder = self.preview_engine.preview_builder
        if builder: 
            self.overlay_mgr.apply_outlines(builder.scroll_frame)
            if hasattr(builder, '_update_background'): builder._update_background()
