# workers/wysiwyg_editor/workspaces/interactive_layout.py
#
# The Interactive Layout Workspace.
# Orchestrates modular overlays for Selection, Structure, Blocks, 
# Columns, Sizing, Sticky, Alignment, and Colors.
#
# Author: Gemini CLI

import tkinter as tk
from tkinter import ttk
import time
from ..core.event_bus import event_bus
from ..core.state_manager import state_manager
from workers.builder.builder import DynamicGuiBuilder
from workers.logic.state_mirror_engine import StateMirrorEngine
from workers.logger.logger import initialize_logging, set_log_directory
from loguru import logger


# Modular Overlay Imports
from .layout_overlays import selection, structure, blocks, columns, sizing, sticky, alignment, colors

LOCAL_DEBUG = True    # Set to False in production, True for dev on this file

class InteractiveLayout(tk.Frame):
    """The visual workspace where users interact with the GUI layout."""

    def __init__(self, parent, *args, **kwargs):
        kwargs.pop("bg", None)
        super().__init__(parent, bg="#1a1a1a", *args, **kwargs)
        if LOCAL_DEBUG: logger.debug("📐 InteractiveLayout: Initializing workspace...")
        
        # Display Toggles
        self.show_structure = tk.BooleanVar(value=True)
        self.show_blocks = tk.BooleanVar(value=True)
        self.show_columns = tk.BooleanVar(value=False)
        self.show_sizing = tk.BooleanVar(value=False)
        self.show_sticky = tk.BooleanVar(value=False)
        self.show_alignment = tk.BooleanVar(value=False)
        self.show_colors = tk.BooleanVar(value=False)
        
        self.preview_builder = None
        self._refresh_timer = None
        self.focused_path = None
        self.pending_changes = 0
        
        # ⚡ AUTO-DISCOVERY: Ensure all widgets are registered for the preview builder
        from managers.Display.factory.widget_registry import WidgetRegistry
        WidgetRegistry.scan_widgets()
        
        self._build_ui()
        
        # Subscribe to state and focus events
        if LOCAL_DEBUG: logger.debug("📐 InteractiveLayout: Subscribing to EventBus events...")
        event_bus.subscribe("STATE_UPDATED", self._on_state_updated)
        event_bus.subscribe("FOCUS_REQUESTED", self._on_external_focus)
        
        self.bind("<Destroy>", self._on_destroy)

        # ⚡ INITIAL LOAD: Trigger rebuild immediately on startup
        if LOCAL_DEBUG: logger.debug("📐 InteractiveLayout: Scheduling initial startup sync in 100ms.")
        self.after(100, self._initial_startup_sync)

    def _initial_startup_sync(self):
        """Performs the first render and initializes the counter to 1."""
        if LOCAL_DEBUG: logger.info("📐 InteractiveLayout: Performing initial startup sync (First Render).")
        self._manual_rebuild()
        self.pending_changes = 1
        self._update_rebuild_ui()

    def _on_destroy(self, event):
        if event.widget == self:
            if self._refresh_timer: self.after_cancel(self._refresh_timer)
            if LOCAL_DEBUG: logger.info("📐 InteractiveLayout: Workspace destroyed. Cleaning up subscriptions.")
            event_bus.unsubscribe("STATE_UPDATED", self._on_state_updated)
            event_bus.unsubscribe("FOCUS_REQUESTED", self._on_external_focus)

    def _on_state_updated(self, json_data, source=None):
        """Track changes selectively. Wait for manual REBUILD."""
        if not self.winfo_exists(): return
        
        source_name = source.__class__.__name__ if source else "Unknown"
        if source == self:
            return

        if LOCAL_DEBUG: logger.debug(f"📐 InteractiveLayout: State update detected (Source: {source_name}). Queueing rebuild.")
        self.pending_changes += 1
        # ⚡ MANUAL ONLY: Increment counter but do NOT auto-rebuild.
        self._update_rebuild_ui()

    def _on_external_focus(self, path, source=None):
        """Highlight selected widget when focused via JSON or Props tab."""
        if not self.winfo_exists() or source == self: return
        if LOCAL_DEBUG: logger.info(f"📐 InteractiveLayout: Focus synchronization request for path: {path} (Source: {source.__class__.__name__ if source else 'Unknown'})")
        self.focused_path = path
        if self.preview_builder:
            if LOCAL_DEBUG: logger.debug("📐 InteractiveLayout: Refreshing overlays for focus change.")
            self._apply_structure_outlines(self.preview_builder.scroll_frame)

    def _build_ui(self):
        """Builds the layout workspace UI with visibility toggles and manual rebuild control."""
        if LOCAL_DEBUG: logger.debug("📐 InteractiveLayout: Building Control Header...")
        header = tk.Frame(self, bg="#333333", height=35)
        header.pack(side="top", fill="x")
        
        tk.Label(header, text="INTERACTIVE LAYOUT", bg="#333333", fg="white", 
                 font=("Arial", 9, "bold")).pack(side="left", padx=10, pady=5)
        
        rebuild_frame = tk.Frame(header, bg="#333333")
        rebuild_frame.pack(side="left", padx=20)
        
        self.rebuild_btn = tk.Button(rebuild_frame, text="REBUILD", bg="black", fg="#00ff00", 
                                    font=("Arial", 8, "bold"), relief="flat", padx=10,
                                    command=self._manual_rebuild)
        self.rebuild_btn.pack(side="left", padx=5)
        
        self.counter_lbl = tk.Label(rebuild_frame, text="CHANGES MADE: 0", bg="#333333", fg="#aaaaaa", 
                                   font=("Arial", 8, "bold"))
        self.counter_lbl.pack(side="left", padx=5)

        controls = [
            ("Structure", self.show_structure),
            ("Blocks", self.show_blocks),
            ("Columns", self.show_columns),
            ("Sizing", self.show_sizing),
            ("Sticky", self.show_sticky),
            ("Alignment", self.show_alignment),
            ("Colors", self.show_colors)
        ]
        
        for text, var in reversed(controls):
            cb = ttk.Checkbutton(header, text=text, variable=var, command=self._force_overlay_refresh)
            cb.pack(side="right", padx=5)

        self.render_area = tk.Frame(self, bg="#2b2b2b")
        self.render_area.pack(fill="both", expand=True)
        if LOCAL_DEBUG: logger.debug("📐 InteractiveLayout: Control Header built.")

    def _update_rebuild_ui(self):
        self.counter_lbl.config(text=f"CHANGES MADE: {self.pending_changes}")
        if self.pending_changes > 0:
            self.counter_lbl.config(fg="#FF9900")
            self.rebuild_btn.config(bg="#222222")
        else:
            self.counter_lbl.config(fg="#aaaaaa")
            self.rebuild_btn.config(bg="black")

    def _manual_rebuild(self):
        if LOCAL_DEBUG: logger.info("📐 InteractiveLayout: REBUILD sequence triggered.")
        self.pending_changes = 0
        self._update_rebuild_ui()
        self._refresh_preview()

    def _force_overlay_refresh(self):
        if LOCAL_DEBUG: logger.debug("📐 InteractiveLayout: Toggles changed. Refreshing overlays...")
        if self.preview_builder:
            self._apply_structure_outlines(self.preview_builder.scroll_frame)

    def _refresh_preview(self, json_data=None):
        """Re-renders the GUI preview."""
        self._refresh_timer = None
        if not self.winfo_exists() or not hasattr(self, 'render_area'): return
        
        if json_data is None: json_data = state_manager.get_state()

        import copy
        render_data = copy.deepcopy(json_data)
        
        # 🧩 DESIGNER OPTIMIZATION: Remove restrictive geometry constraints for preview
        # This prevents the 'jumbled' look when hardware-sized containers (168px) 
        # try to render multi-channel arrays.
        def _strip_constraints(data):
            if isinstance(data, dict):
                # Remove width/height from geometry stanzas
                if "geometry" in data and isinstance(data["geometry"], dict):
                    data["geometry"].pop("width", None)
                    data["geometry"].pop("height", None)
                # Remove top-level width/height
                data.pop("width", None)
                data.pop("height", None)
                # Recurse
                for v in data.values():
                    _strip_constraints(v)
            elif isinstance(data, list):
                for item in data:
                    _strip_constraints(item)

        _strip_constraints(render_data)

        if self.preview_builder:
            if LOCAL_DEBUG: logger.info("📐 InteractiveLayout: Updating DynamicGuiBuilder data and triggering internal rebuild...")
            self.preview_builder._is_rebuilding = True
            try:
                # Force reset of internal width tracking to ensure expansion
                self.preview_builder._last_reported_width = 0
                self.preview_builder.config_data = render_data
                self.preview_builder._rebuild_gui()
            finally:
                # Use a short delay to ensure sub-widgets (deferred) also finish their initial layout
                self.preview_builder.after(100, lambda: setattr(self.preview_builder, '_is_rebuilding', False))
        else:
            if LOCAL_DEBUG: logger.info("📐 InteractiveLayout: Creating NEW preview DynamicGuiBuilder instance.")
            # Inert engine for preview to prevent MQTT chatter/zombies
            inert_engine = StateMirrorEngine(base_topic="PREVIEW", subscriber_router=None, root=None, state_cache_manager=None)
            builder_config = {
                "state_mirror_engine": inert_engine,
                "subscriber_router": None,
                "on_focus_widget": self._on_widget_focused,
                "is_editor": True
            }
            self.preview_builder = DynamicGuiBuilder(self.render_area, config=builder_config, tab_name="InteractivePreview")
            self.preview_builder.pack(fill="both", expand=True)
            self.preview_builder._is_rebuilding = True
            try:
                self.preview_builder.config_data = render_data
                self.preview_builder._rebuild_gui()
            finally:
                self.preview_builder.after(100, lambda: setattr(self.preview_builder, '_is_rebuilding', False))
        
        if LOCAL_DEBUG: logger.debug("📐 InteractiveLayout: Scheduling overlay injection in 250ms...")
        self.after(250, lambda: self._apply_structure_outlines(self.preview_builder.scroll_frame))

    def _on_widget_focused(self, path):
        """Broadcasting widget selection from layout with OcaArray redirection."""
        if not self.winfo_exists(): return
        
        # 🛡️ SAFETY CHECK: Handle None path (deselection) early
        if path is None:
            if LOCAL_DEBUG: logger.info("📐 InteractiveLayout: Deselecting widget.")
            self.focused_path = None
            event_bus.publish("FOCUS_REQUESTED", path=None, source=self)
            self._force_overlay_refresh()
            return

        # 🧩 ARRAY REDIRECTION: If selecting an array item, focus the template (blueprint) instead
        parts = str(path).split(".")
        for i in range(len(parts)):
            sub_path = ".".join(parts[:i+1])
            val = state_manager.get_value_at_path(sub_path)
            if isinstance(val, dict) and val.get("type") == "OcaArray":
                # We found an OcaArray root. 
                # Check if we are inside the 'fields' of a synthetic item.
                # Array path structure: ArrayKey.fields.ItemKey.fields.WidgetKey
                if len(parts) > i + 3 and parts[i+1] == "fields" and parts[i+3] == "fields":
                    # Redirect to blueprint: ArrayKey.blueprint.fields.WidgetKey
                    new_path = f"{sub_path}.blueprint.{'.'.join(parts[i+3:])}"
                    path = new_path
                    if LOCAL_DEBUG: logger.info(f"🧩 InteractiveLayout: Array item detected. Redirecting focus to blueprint: {path}")
                    break
                elif len(parts) > i + 1 and parts[i+1] == "fields":
                    # Redirect to blueprint root
                    path = f"{sub_path}.blueprint"
                    if LOCAL_DEBUG: logger.info(f"🧩 InteractiveLayout: Array container detected. Redirecting focus to blueprint: {path}")
                    break

        self.focused_path = path
        if LOCAL_DEBUG: logger.info(f"📐 InteractiveLayout: Widget Clicked in Preview - Target Path: {path}")
        event_bus.publish("FOCUS_REQUESTED", path=path, source=self)
        self._force_overlay_refresh()

    def _apply_structure_outlines(self, container):
        """Recursively injects design handles and selection highlights."""
        if not container or not container.winfo_exists(): return
        if LOCAL_DEBUG: logger.debug(f"📐 InteractiveLayout: Scanning preview widgets for overlay injection...")
        self._recursive_clear_overlays(container)
        self._apply_recursive_overlays(container)
        if LOCAL_DEBUG: logger.debug("📐 InteractiveLayout: Overlay injection complete.")

    def _recursive_clear_overlays(self, container):
        for child in list(container.winfo_children()):
            if getattr(child, '_is_design_overlay', False):
                try: child.destroy()
                except: pass
            elif isinstance(child, (tk.Frame, ttk.Frame, tk.Canvas, tk.LabelFrame)):
                self._recursive_clear_overlays(child)

    def _apply_recursive_overlays(self, container, depth=0):
        # 🛡️ SAFETY LIMIT: Prevent freezing on massive trees
        if depth > 10: return

        for child in container.winfo_children():
            if getattr(child, '_is_design_overlay', False): continue
            
            path = getattr(child, '_oca_path', None)
            if path and "unknown" not in path:
                # 🧩 ARRAY DESIGN: Show handles for ALL items now that we removed the 1-item limit.
                # This allows the user to click any item to focus the master blueprint.
                self._inject_design_controls(child)
            
            if isinstance(child, (tk.Frame, ttk.Frame, tk.Canvas, tk.LabelFrame)):
                if path: # Keep recursing into blocks
                    self._apply_recursive_overlays(child, depth + 1)

    def _inject_design_controls(self, widget):
        """Dispatches design control logic to modular overlay handlers."""
        try:
            path = getattr(widget, '_oca_path', 'unknown')
            is_focused = (self.focused_path == path)
            design_elements = []
            sync_funcs = []

            # Apply Modular Overlays
            modules = [selection, structure, blocks, columns, sizing, sticky, alignment, colors]
            for mod in modules:
                sync_fn = mod.apply(self, widget, path, is_focused, design_elements)
                if sync_fn: sync_funcs.append(sync_fn)

            def _sync_pos(event=None):
                if not widget.winfo_exists(): return
                try:
                    x, y, w, h = widget.winfo_x(), widget.winfo_y(), widget.winfo_width(), widget.winfo_height()
                    if w <= 1 or h <= 1: return
                    for sync_fn in sync_funcs:
                        sync_fn(x, y, w, h)
                except tk.TclError: pass
            
            if hasattr(widget, '_oca_configure_sid'):
                try: widget.unbind("<Configure>", widget._oca_configure_sid)
                except: pass
            widget._oca_configure_sid = widget.bind("<Configure>", _sync_pos, add="+")
            
            # Initial Sync
            widget.after(100, _sync_pos)
                
        except Exception as e:
            logger.exception("❌ InteractiveLayout Error injecting handles for {path}")
