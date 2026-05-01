# oaGui/Workers/builder.py
# Author: Anthony Peter Kuzub
# Version: 20260416.Modular.1
#
# Description: Main Orchestrator for the Dynamic GUI Builder.
# Constructs a pixel-perfect, background-aware industrial UI from JSON state.

import tkinter as tk
from pathlib import Path
from tkinter import ttk
import threading

from oaConfigurationManager.FileReaders.config_reader import Config
from oaGui.Managers.gui_batch import GuiBatchBuilderMixin
from oaGui.Managers.gui_mqtt import GuiMqttManagerMixin
from oaGui.Managers.gui_re import GuiRebuilderMixin
from oaGuiElements.Core.background import BuilderBackgroundManagerMixin
from oaGui.Constants.builder_constants import RESIZE_THROTTLE_DELAY, RESIZE_WIDTH_THRESHOLD, SCROLL_SYNC_DELAY
from oaGui.Core.breakoff.window_breakoff_manager import WindowBreakoffManagerMixin

# --- MODULAR MIXINS ---
from oaGui.Core.context_menu import BuilderContextMenuMixin
from oaGui.Core.slicing_registry import BuilderSlicingRegistryMixin
from oaGuiElements.Core.input.input_mousewheel_mixin.input_mousewheel_mixin import MousewheelScrollMixin
from oaGui.Core.context.widget_context import WidgetContext
from oaGui.Core.factory.gui_widget_factory import GuiWidgetFactoryMixin
from oaGui.Core.telemetry.ui_tracking_service import UITrackingService

# --- ENGINE SERVICES ---
from oaGui.Core.transparency.transparency import TransparencyManager
from oaGui.Core.transparency.transparency_mixin import TransparencyMixin
from oaGui.FileReaders.gui_file_loader import GuiFileLoaderMixin

# --- GLOBAL ARCHITECTURE ---
# --- CORE MIXINS ---
from oaStyle.Core.gui_style import GuiStyleMixin
from oaStyle.Core.style import DEFAULT_THEME, THEMES


class AutoScrollbar(ttk.Scrollbar):
    """An industrial scrollbar that manages its own visibility based on content scale."""
    def __init__(self, master=None, **kwargs):
        self.grid_kwargs = {}
        super().__init__(master, **kwargs)

    def grid(self, **kwargs):
        self.grid_kwargs.update(kwargs)
        super().grid(**kwargs)

    def set(self, lo, hi):
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            self.grid_remove()
        else:
            self.grid(**self.grid_kwargs)
        ttk.Scrollbar.set(self, lo, hi)

class DynamicGuiBuilder(
    tk.Frame,
    GuiMqttManagerMixin,
    GuiStyleMixin,
    GuiWidgetFactoryMixin,
    GuiFileLoaderMixin,
    GuiRebuilderMixin,
    GuiBatchBuilderMixin,
    TransparencyMixin,
    BuilderContextMenuMixin,
    BuilderBackgroundManagerMixin,
    BuilderSlicingRegistryMixin,
    MousewheelScrollMixin,
    WindowBreakoffManagerMixin,
):
    """Orchestrates the construction and lifecycle of a dynamic industrial UI."""

    def __init__(self, parent, json_path=None, tab_name=None, use_grid=False, *args, **kwargs):
        config = kwargs.pop("config", {})
        
        # 🎨 THEME AWARE INITIALIZATION
        theme = THEMES.get(DEFAULT_THEME, THEMES["dark"])
        bg = theme["bg"]
        
        # Pass background directly to tk.Frame
        super().__init__(master=parent, bg=bg)

        self.parent_builder = self._find_parent_builder(parent)
        self._initialize_internal_state(json_path, tab_name, config)
        self._initialize_builder_services(config)
        self._build_ui_scaffolding(use_grid)
        self._setup_context_menu()

    def _find_parent_builder(self, parent_widget):
        """Traverses up the widget tree to find a parent DynamicGuiBuilder."""
        curr = parent_widget
        while curr:
            if hasattr(curr, 'builder_instance') and curr.builder_instance:
                return curr.builder_instance
            if isinstance(curr, DynamicGuiBuilder):
                return curr
            parent_path = curr.winfo_parent()
            if not parent_path: break
            curr = curr.nametowidget(parent_path)
        return None

    def _initialize_internal_state(self, path, tab_name, config):
        """Standardizes internal variables and engine references."""
        self.tab_name = tab_name
        self.json_filepath = Path(path) if path else None

        # External Engine Hooks
        self.state_mirror_engine = config.get("state_mirror_engine")
        self.subscriber_router = config.get("subscriber_router")
        self.app_instance = config.get("app_instance")
        self.on_focus_widget = config.get("on_focus_widget")

        # Builder State
        self.is_editor = config.get("is_editor", False)
        self.allow_horizontal_scroll = config.get("allow_horizontal_scroll", True)
        # ⚡ NEW: Support for disabling scrolling entirely (Direct Overlay mode)
        self.allow_scrolling = config.get("allow_scrolling", True)
        # ⚡ NEW: Support for forced transparency (Nested mode)
        self.is_transparent = config.get("transparent", False) or (self.parent_builder is not None)
        self._render_tier = config.get("render_tier", "high_res")
        
        self.config_data = {}
        self.tk_vars = {}
        self.topic_widgets = {}
        self._slicing_registry = []
        self._is_rebuilding = False
        self.last_build_hash = None
        self.gui_built = False

    def _initialize_builder_services(self, config):
        """Bootstraps telemetry and communication services."""
        self.tracking_service = UITrackingService()
        self._initialize_mqtt_context(self.json_filepath, Config.get_instance(), config.get("base_mqtt_topic_from_path"))
        self._initialize_widget_factory()
        self.tracking_service.track(self, self.tab_name, self.state_mirror_engine, self.base_mqtt_topic_from_path)

    def _build_ui_scaffolding(self, use_grid):
        """Constructs the Paned/Scrolled container hierarchy."""
        # 🎨 THEME AWARE BACKGROUND
        theme = THEMES.get(DEFAULT_THEME, THEMES["dark"])
        bg = theme["bg"]

        self.config(bg=bg)
        self.grid_rowconfigure(0, weight=1); self.grid_columnconfigure(0, weight=1)

        # ⚡ SIZING FIX: Use standard tk.Frame to ensure grid expansion works without ttk style interference
        self.main_content_frame = tk.Frame(self, bg=bg, bd=0, highlightthickness=0)
        self.main_content_frame.grid(row=0, column=0, sticky="nsew")
        self.main_content_frame.grid_rowconfigure(0, weight=1); self.main_content_frame.grid_columnconfigure(0, weight=1)

        # 🏗️ CANVAS & SCROLLING
        if self.allow_scrolling:
            self.canvas = tk.Canvas(self.main_content_frame, background=bg, bd=0, highlightthickness=0)
            self.scroll_frame = tk.Frame(self.canvas, bd=0, highlightthickness=0, bg=bg)
            self.canvas_window_id = self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
            self._setup_scrolling()
            self._setup_event_bindings()
            self.canvas.grid(row=0, column=0, sticky="nsew")
        else:
            # ⚡ OVERLAY MODE: Build directly into a transparent frame
            self.scroll_frame = tk.Frame(self.main_content_frame, bd=0, highlightthickness=0, bg=bg)
            self.scroll_frame.grid(row=0, column=0, sticky="nsew")
            self.canvas = None
            self.canvas_window_id = None

        # ⚡ FOOTER: Optional telemetry display
        if getattr(Config.get_instance(), 'FOOTER_ENABLED', False):
            self.footer_frame = tk.Frame(self.main_content_frame, bg="#111111", height=18)
            self.footer_frame.grid(row=2, column=0, columnspan=2, sticky="ew")
            self.footer_frame.grid_propagate(False)
            
            self.viewport_lbl = tk.Label(self.footer_frame, text="Viewport: 0x0", bg="#111111", fg="#888888", font=("Arial", 7))
            self.viewport_lbl.pack(side="left", padx=10)
            
            self.content_lbl = tk.Label(self.footer_frame, text="Content: 0x0", bg="#111111", fg="#888888", font=("Arial", 7))
            self.content_lbl.pack(side="left", padx=10)
            
            self.telemetry_geo_lbl = tk.Label(self.footer_frame, text="GEO: IDLE", bg="#111111", fg="#00FFFF", font=("Arial", 7))
            self.telemetry_geo_lbl.pack(side="right", padx=10)

            self.telemetry_cmd_lbl = tk.Label(self.footer_frame, text="TX: IDLE", bg="#111111", fg="#00FF00", font=("Arial", 7))
            self.telemetry_cmd_lbl.pack(side="right", padx=10)
        else:
            self.footer_frame = None

        # ⚡ TRANSPARENCY: If nested or explicit, register containers with parent builder
        if self.is_transparent and self.parent_builder:
            TransparencyManager.apply_transparency(self.main_content_frame, None, {"type": "OcaBlock"}, self.parent_builder)
            if self.canvas:
                TransparencyManager.apply_transparency(self.canvas, self.canvas, {"type": "OcaBin"}, self.parent_builder)
            TransparencyManager.apply_transparency(self.scroll_frame, None, {"type": "OcaBlock"}, self.parent_builder)

        if self.canvas and self.is_editor: self._draw_editor_grid()

    def _setup_scrolling(self):
        """Wires up the industrial scrollbars. Horizontal scrolling depends on allow_horizontal_scroll."""
        self.scrollbar_v = AutoScrollbar(self.main_content_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self._on_scroll_v)
        self.scrollbar_v.grid(row=0, column=1, sticky="ns")

        if self.allow_horizontal_scroll:
            self.scrollbar_h = AutoScrollbar(self.main_content_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
            self.canvas.configure(xscrollcommand=self._on_scroll_h)
            self.scrollbar_h.grid(row=1, column=0, sticky="ew")

    def _on_scroll_v(self, *args):
        self.scrollbar_v.set(*args)
        self._trigger_scroll_sync()

    def _on_scroll_h(self, *args):
        self.scrollbar_h.set(*args)
        self._trigger_scroll_sync()

    def _setup_event_bindings(self):
        """Standardizes lifecycle and resizing event handlers."""
        self._resize_timer = None
        self._scroll_timer = None
        
        if self.canvas:
            self.scroll_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
            self.canvas.bind("<Configure>", self._on_canvas_configure)
        else:
            # In overlay mode, we still need to track scroll_frame changes for background sizing
            self.scroll_frame.bind("<Configure>", lambda e: self._trigger_background_sync())
            
        self.bind("<Visibility>", self._on_visibility)

    def start(self):
        """Triggers the physical UI build sequence."""
        if self.json_filepath:
            self._load_and_build_from_file()
        else:
            self._rebuild_gui()

    def _trigger_scroll_sync(self):
        """Debounces reslicing notifications during continuous scrolling."""
        if self._is_rebuilding or getattr(self, '_resize_timer', None): return
        if not getattr(self, '_scroll_timer', None):
            self._scroll_timer = self.after(SCROLL_SYNC_DELAY, self._perform_scroll_sync)

    def _perform_scroll_sync(self):
        self._scroll_timer = None
        if self._is_rebuilding: return
        self._trigger_reslice_all()

    def _on_canvas_configure(self, event):
        """Reacts to physical window resizing with threshold-based throttling."""
        # ⚡ EVENT GATE: Ignore resize events from children (like the footer or buttons)
        if event.widget != self: return
        if self._is_rebuilding: return

        w, h = event.width, event.height

        # ⚡ THRESHOLD CHECK: Ignore micro-resizes
        last_w = getattr(self, '_last_w', 0)
        last_h = getattr(self, '_last_h', 0)

        if abs(w - last_w) < RESIZE_WIDTH_THRESHOLD and abs(h - last_h) < RESIZE_WIDTH_THRESHOLD:
            return

        self._last_w = w
        self._last_h = h

        if self._resize_timer: self.after_cancel(self._resize_timer)
        # ⚡ USE SETTLED DIMENSIONS: Throttled call must query physically settled pixels
        self._resize_timer = self.after(RESIZE_THROTTLE_DELAY, self._trigger_final_resize)
        if self.is_editor: self.after(RESIZE_THROTTLE_DELAY + 10, self._draw_editor_grid)

    def _trigger_final_resize(self):
        """Throttled entry point that reads settled dimensions."""
        if not self.winfo_exists(): return
        # ⚡ PHYSICAL SYNC: Use winfo to get the actual settled size
        self._perform_canvas_resize(self.winfo_width(), self.winfo_height())

    def _update_footer(self, width, height, req_w, req_h):
        """Updates the optional telemetry footer with real-time dimensions and highlights changes."""
        if not hasattr(self, 'footer_frame') or not self.footer_frame: return
        try:
            new_view = f"Viewport: {width}x{height}"
            new_cont = f"Content: {req_w}x{req_h}"
            
            # ⚡ GROWTH/SHRINK HIGHLIGHT: Pulse white if the values changed
            if self.viewport_lbl.cget("text") != new_view:
                self.viewport_lbl.config(text=new_view, fg="#FFFFFF")
                self.after(300, lambda: self.viewport_lbl.config(fg="#888888") if self.winfo_exists() else None)
            
            if self.content_lbl.cget("text") != new_cont:
                self.content_lbl.config(text=new_cont, fg="#FFFFFF")
                self.after(300, lambda: self.content_lbl.config(fg="#888888") if self.winfo_exists() else None)
            
            # ⚡ ACTIVITY SYNC: Simple spinner for geometry telemetry
            current_geo = self.telemetry_geo_lbl.cget("text")
            indicator = " /" if "/" not in current_geo else " \\" if "\\" not in current_geo else " -" if "-" not in current_geo else " |"
            # Note: GEO label is updated by the telemetry service to ensure truth
        except Exception: pass

    def _log_telemetry_tx(self, message):
        """Standard geometry telemetry callback."""
        if not hasattr(self, 'footer_frame') or not self.footer_frame: return
        try:
            self.telemetry_geo_lbl.config(text=str(message))
            self.telemetry_geo_lbl.config(fg="#FFFFFF")
            self.telemetry_geo_lbl.update_idletasks()
            self.after(200, lambda: self.telemetry_geo_lbl.config(fg="#00FFFF") if self.winfo_exists() else None)
        except Exception: pass

    def _log_command_tx(self, message):
        """Standard command telemetry callback."""
        if not hasattr(self, 'footer_frame') or not self.footer_frame: return
        try:
            display_msg = str(message)[:60] + ("..." if len(str(message)) > 60 else "")
            self.telemetry_cmd_lbl.config(text=f"TX: {display_msg}")
            self.telemetry_cmd_lbl.config(fg="#FFFFFF")
            self.telemetry_cmd_lbl.update_idletasks()
            self.after(200, lambda: self.telemetry_cmd_lbl.config(fg="#00FF00") if self.winfo_exists() else None)
        except Exception: pass

    def _perform_canvas_resize(self, width, height):
        self._resize_timer = None
        if width <= 1 or height <= 1 or not self.canvas_window_id: return

        # 📏 DIMENSION CALCULATION: 
        # width/height here is the physical VIEWPORT of the DynamicGuiBuilder.
        req_w = self.scroll_frame.winfo_reqwidth()
        req_h = self.scroll_frame.winfo_reqheight()

        # Stretch the inner frame to at least fill the viewport
        new_w = width if not self.allow_horizontal_scroll else max(width, req_w)
        new_h = max(height, req_h)
        
        from oaLogging.Methods.matrix_gate import matrix_log
        matrix_log("ui", "gui_render", "_perform_canvas_resize", 
                   f"📏 [BUILDER_SIZE] Tab: {getattr(self, 'tab_name', '??')} | "
                   f"Viewport: {width}x{height} | Content: {req_w}x{req_h} | Target: {new_w}x{new_h}", "TRACE")

        # ⚡ FOOTER UPDATE: Transmit the physical viewport size to the footer
        self._update_footer(width, height, req_w, req_h)

        if new_w <= 1 or new_h <= 1: return # X11 safety

        try:
            self.canvas.itemconfig(self.canvas_window_id, width=int(new_w), height=int(new_h))
            self._trigger_background_sync(force=True)
        except tk.TclError: pass

    def _draw_editor_grid(self):
        """Draws a 100px diagnostic grid for WYSIWYG alignment."""
        if not self.is_editor or not self.canvas.winfo_exists(): return
        self.canvas.delete("editor_grid")

        w = max(self.canvas.winfo_width(), self.scroll_frame.winfo_reqwidth())
        h = max(self.canvas.winfo_height(), self.scroll_frame.winfo_reqheight())

        for x in range(0, w, 100):
            self.canvas.create_line(x, 0, x, h, fill="#333333", dash=(2, 4), tags="editor_grid")
        for y in range(0, h, 100):
            self.canvas.create_line(0, y, w, y, fill="#333333", dash=(2, 4), tags="editor_grid")

        self.canvas.create_line(w//2, 0, w//2, h, fill="#FF9900", width=1, dash=(5, 5), tags="editor_grid")
        self.canvas.create_line(0, h//2, w, h//2, fill="#FF00FF", width=1, dash=(5, 5), tags="editor_grid")
        self.canvas.tag_lower("editor_grid")

    def _on_gui_visible(self, event=None):
        """Ensures background synchronization occurs only when the UI is physical."""
        if not self.winfo_exists() or not self.winfo_ismapped(): return
        
        # ⚡ INITIAL SETTLE: Trigger a resize pass to populate the footer and background
        # Also ensure the parent grid allows us to expand
        try:
            parent = self.nametowidget(self.winfo_parent())
            parent.grid_rowconfigure(0, weight=1)
            parent.grid_columnconfigure(0, weight=1)
        except Exception: pass

        self.update() # ⚡ FORCE GEOMETRY REALIZATION
        w, h = self.winfo_width(), self.winfo_height()
        if w > 1 and h > 1:
            self._perform_canvas_resize(w, h)
            self._log_telemetry_tx(f"GEO: {w}x{h}")

        if not hasattr(self, 'panel_bg_pil') or self.panel_bg_pil is None:
            self._trigger_background_sync(force=True)
        else:
            self._trigger_reslice_all()

    def _on_visibility(self, event=None):
        """Legacy handler for <Visibility> events."""
        self._on_gui_visible(event)

    def _get_widget_context(self) -> WidgetContext:
        """Factory for construction context passed to widget creators."""
        return WidgetContext(
            state_mirror_engine=self.state_mirror_engine,
            subscriber_router=self.subscriber_router,
            base_mqtt_topic_from_path=self.base_mqtt_topic_from_path,
            app_instance=self.app_instance,
            builder_instance=self,
            transparency_manager=TransparencyManager,
            on_focus_widget=self.on_focus_widget
        )

    def _update_background(self):
        """Synchronizes canvas and frame backgrounds with the global visibility toggle."""
        theme_bg = THEMES.get(DEFAULT_THEME, THEMES["dark"])["bg"]
        # target = theme_bg if (not show or show.get()) else "" # Removed buggy line
        target = theme_bg

        for w in [getattr(self, 'canvas', None), getattr(self, 'scroll_frame', None)]:
            if w is None: continue
            try:
                if w.cget("bg" if w == getattr(self, 'scroll_frame', None) else "background") != target:
                    w.configure(**{"bg" if w == getattr(self, 'scroll_frame', None) else "background": target})
            except tk.TclError: pass
        self._trigger_reslice_all()
