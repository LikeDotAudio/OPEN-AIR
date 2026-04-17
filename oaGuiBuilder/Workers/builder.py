# oaGuiBuilder/Workers/builder.py
# Author: Anthony Peter Kuzub
# Version: 20260416.Modular.1
#
# Description: Main Orchestrator for the Dynamic GUI Builder.
# Constructs a pixel-perfect, background-aware industrial UI from JSON state.

import tkinter as tk
from tkinter import ttk
from pathlib import Path

# --- GLOBAL ARCHITECTURE ---
from oaLogging.Methods.matrix_gate import matrix_log
from oaConfigurationManager.FileReaders.config_reader import Config
from oaStyle.Core.style import DEFAULT_THEME, THEMES
from oaGuiManager.Core.context.widget_context import WidgetContext
from oaGuiBuilder.Constants.builder_constants import (
    SCROLL_SYNC_DELAY, RESIZE_THROTTLE_DELAY, RESIZE_WIDTH_THRESHOLD
)

# --- ENGINE SERVICES ---
from oaGuiManager.Core.transparency.transparency import TransparencyManager
from oaGuiManager.Core.telemetry.ui_tracking_service import UITrackingService

# --- CORE MIXINS ---
from oaStyle.Core.gui_style import GuiStyleMixin
from oaGuiManager.Core.factory.gui_widget_factory import GuiWidgetFactoryMixin
from oaGui.Managers.gui_mqtt import GuiMqttManagerMixin
from oaGuiManager.FileReaders.gui_file_loader import GuiFileLoaderMixin
from oaGui.Managers.gui_re import GuiRebuilderMixin
from oaGui.Managers.gui_batch import GuiBatchBuilderMixin
from oaGuiManager.Core.transparency.transparency_mixin import TransparencyMixin

# --- MODULAR MIXINS ---
from oaGuiBuilder.Core.context_menu import BuilderContextMenuMixin
from oaGuiBackground.Core.background import BuilderBackgroundManagerMixin
from oaGuiBuilder.Core.slicing_registry import BuilderSlicingRegistryMixin
from oaGuiBuilder.Core.breakoff.window_breakoff_manager import WindowBreakoffManagerMixin
from oaGuiElements.Core.input.input_mousewheel_mixin.input_mousewheel_mixin import MousewheelScrollMixin

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
    ttk.Frame,
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
        super().__init__(master=parent)

        self._initialize_internal_state(json_path, tab_name, config)
        self._initialize_builder_services(config)
        self._build_ui_scaffolding(use_grid)
        self._setup_context_menu()

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
        self.config_data = {}
        self.tk_vars = {}
        self.topic_widgets = {}
        self._slicing_registry = []
        self._is_rebuilding = False

    def _initialize_builder_services(self, config):
        """Bootstraps telemetry and communication services."""
        self.tracking_service = UITrackingService()
        self._initialize_mqtt_context(self.json_filepath, Config.get_instance(), config.get("base_mqtt_topic_from_path"))
        self._initialize_widget_factory()
        self.tracking_service.track(self, self.tab_name, self.state_mirror_engine, self.base_mqtt_topic_from_path)

    def _build_ui_scaffolding(self, use_grid):
        """Constructs the Paned/Scrolled container hierarchy."""
        self.config(style="Dark.TFrame")
        self.grid_rowconfigure(0, weight=1); self.grid_columnconfigure(0, weight=1)

        self.main_content_frame = ttk.Frame(self, style="Dark.TFrame")
        self.main_content_frame.grid(row=0, column=0, sticky="nsew")
        self.main_content_frame.grid_rowconfigure(0, weight=1); self.main_content_frame.grid_columnconfigure(0, weight=1)

        # 🎨 THEME AWARE BACKGROUND
        theme = THEMES.get(DEFAULT_THEME, THEMES["dark"])
        bg = theme["bg"]
        # Note: If show_background_var is False, we still use the theme color for the container 
        # but skip high-res background slice generation in the build loop.

        # 🏗️ CANVAS & SCROLLING
        self.canvas = tk.Canvas(self.main_content_frame, background=bg, bd=0, highlightthickness=0)
        self.scroll_frame = tk.Frame(self.canvas, bd=0, highlightthickness=0, bg=bg)
        self.canvas_window_id = self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")

        self._setup_scrolling()
        self._setup_event_bindings()
        
        self.canvas.grid(row=0, column=0, sticky="nsew")
        if self.is_editor: self._draw_editor_grid()

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
        self.scroll_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", self._on_canvas_configure)
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
        if self._is_rebuilding: return
        w = event.width
        if abs(w - getattr(self, '_last_w', 0)) < RESIZE_WIDTH_THRESHOLD: return
        self._last_w = w
        
        if self._resize_timer: self.after_cancel(self._resize_timer)
        self._resize_timer = self.after(RESIZE_THROTTLE_DELAY, self._perform_canvas_resize, w)
        if self.is_editor: self.after(RESIZE_THROTTLE_DELAY + 10, self._draw_editor_grid)

    def _perform_canvas_resize(self, width):
        self._resize_timer = None
        if width <= 1 or not self.canvas_window_id: return

        # ⚡ HORIZONTAL LOCK: Content frame width matches visible canvas width UNLESS horizontal scroll is allowed.
        req_w = self.scroll_frame.winfo_reqwidth()
        new_w = width if not self.allow_horizontal_scroll else max(width, req_w)
        
        if new_w <= 1: return # X11 safety

        try:
            self.canvas.itemconfig(self.canvas_window_id, width=int(new_w))
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

    def _on_visibility(self, event=None):
        """Ensures background synchronization occurs only when the UI is physical."""
        if not self.winfo_ismapped(): return
        if not hasattr(self, 'panel_bg_pil') or self.panel_bg_pil is None:
            self._trigger_background_sync(force=True)
        else:
            self._trigger_reslice_all()

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
        
        for w in [self.canvas, self.scroll_frame]:
            try:
                if w.cget("bg" if w == self.scroll_frame else "background") != target:
                    w.configure(**{"bg" if w == self.scroll_frame else "background": target})
            except tk.TclError: pass
        self._trigger_reslice_all()
