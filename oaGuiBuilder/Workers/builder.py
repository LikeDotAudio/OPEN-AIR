# Workers/builder.py
# Author: Anthony Peter Kuzub
# Version: 20260315.Modular.1
#
# Description: Defines the main DynamicGuiBuilder class, which is responsible for constructing the application's GUI from a JSON configuration.

import os
import time
import tkinter as tk
from tkinter import ttk
from pathlib import Path

# --- Standard Debug Logging Setup ---
from oaLogging.Core.logger import initialize_logging, set_log_directory, builder_logger
from oaLogging.Methods.matrix_gate import is_debug_allowed, matrix_log
BUILDER_DEBUG = is_debug_allowed(system="gui", element="gui_builder")

from loguru import logger

from oaConfigurationManager.FileReaders.config_reader import Config
app_constants = Config.get_instance()

from oaStyle.Core.style import DEFAULT_THEME, THEMES

# --- 1. CORE MIXINS ---
from oaStyle.Core.gui_style import GuiStyleMixin
from oaGuiManager.Core.factory.gui_widget_factory import GuiWidgetFactoryMixin
from oaGui.Managers.gui_mqtt import GuiMqttManagerMixin
from oaGuiManager.FileReaders.gui_file_loader import GuiFileLoaderMixin
from oaGui.Managers.gui_re import GuiRebuilderMixin
from oaGui.Managers.gui_batch import GuiBatchBuilderMixin
from oaGuiManager.Core.transparency.transparency_mixin import TransparencyMixin

# --- EXTRACTED CORE MODULES ---
from oaGuiBuilder.Core.context_menu import BuilderContextMenuMixin
from oaGuiBackground.Core.background import BuilderBackgroundManagerMixin
from oaGuiBuilder.Core.slicing_registry import BuilderSlicingRegistryMixin

# --- 2. DECOUPLED SERVICES ---
from oaGuiManager.Core.transparency.transparency import TransparencyManager
from oaGuiManager.Core.telemetry.ui_tracking_service import UITrackingService

# --- 3. HIDDEN FEATURES ---
from oaGuiElements.Core.utils.breakoff.hidden_breakoff import HiddenBreakoffManagerMixin

# --- 4. UTILITIES ---
from oaGuiElements.Core.input.input_mousewheel_mixin.input_mousewheel_mixin import (
    MousewheelScrollMixin,
)
from oaGuiElements.Core.utils.panels.panel_generator import PanelGenerator
from PIL import ImageTk
from oaGuiManager.Core.context.widget_context import WidgetContext
from oaGuiBuilder.Constants.builder_constants import (
    SCROLL_SYNC_DELAY, 
    RESIZE_THROTTLE_DELAY, 
    RESIZE_WIDTH_THRESHOLD
)

class AutoScrollbar(ttk.Scrollbar):
    """A scrollbar that hides itself when it's not needed."""
    def set(self, lo, hi):
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            self.grid_remove()
        else:
            self.grid()
        ttk.Scrollbar.set(self, lo, hi)

class DynamicGuiBuilder(
    ttk.Frame,
    # Framework Core Logic
    GuiMqttManagerMixin,
    GuiStyleMixin,
    GuiWidgetFactoryMixin,
    GuiFileLoaderMixin,
    GuiRebuilderMixin,
    GuiBatchBuilderMixin,
    TransparencyMixin, 
    # Extracted Modular Mixins
    BuilderContextMenuMixin,
    BuilderBackgroundManagerMixin,
    BuilderSlicingRegistryMixin,
    # Foundation Mixins
    MousewheelScrollMixin,
    HiddenBreakoffManagerMixin,
):
    def __init__(self, parent, json_path=None, tab_name=None, use_grid=False, *args, **kwargs):
        config = kwargs.pop("config", {})
        super().__init__(master=parent)

        self._init_state(json_path, tab_name, config)
        self._init_services(config)
        self._init_scaffolding(use_grid)
        self._setup_context_menu()

    def _init_state(self, json_path, tab_name, config):
        self.tab_name = tab_name
        self.on_complete_callback = config.get("on_complete")
        self.state_mirror_engine = config.get("state_mirror_engine")
        self.subscriber_router = config.get("subscriber_router")
        self.app_instance = config.get("app_instance")
        self.on_focus_widget = config.get("on_focus_widget")
        self.is_editor = config.get("is_editor", False)
        # ⚡ NEW: Control horizontal scrolling
        self.allow_horizontal_scroll = config.get("allow_horizontal_scroll", True)
        
        self.json_filepath = Path(json_path) if json_path else None
        self.config_data = {}
        self.tk_vars = {}
        self.topic_widgets = {}
        self.last_build_hash = None
        self.gui_built = False
        self.panel_bg_image = None
        self.panel_bg_label = None
        self._slicing_registry = []
        self.is_visible = False

    def _init_services(self, config):
        self.tracking_service = UITrackingService()

        self._initialize_mqtt_context(
            self.json_filepath,
            app_constants,
            config.get("base_mqtt_topic_from_path"),
        )
        self._initialize_widget_factory()
        
        self.tracking_service.track(
            self, 
            self.tab_name, 
            self.state_mirror_engine, 
            self.base_mqtt_topic_from_path
        )

    def _init_scaffolding(self, use_grid):
        self.config(style="Dark.TFrame")
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.main_content_frame = ttk.Frame(self, style="Dark.TFrame")
        self.main_content_frame.grid(row=0, column=0, sticky="nsew")
        self.main_content_frame.grid_rowconfigure(0, weight=1)
        self.main_content_frame.grid_columnconfigure(0, weight=1)

        colors = THEMES.get(DEFAULT_THEME, THEMES["dark"])
        # Determine initial background color based on toggle
        initial_bg_color = colors["bg"]
        
        # ⚡ ROBUSTNESS: Use getattr to safely check for show_background_var on app_instance
        show_bg_toggle = getattr(self.app_instance, 'show_background_var', None)
        if show_bg_toggle and not show_bg_toggle.get():
            initial_bg_color = "" # Use empty string for Tkinter transparency/default to parent

        self.canvas = tk.Canvas(
            self.main_content_frame, background=initial_bg_color, bd=0, highlightthickness=0
        )
        self.scroll_frame = tk.Frame(self.canvas, bd=0, highlightthickness=0, bg=initial_bg_color)

        TransparencyManager.apply_transparency(self, self.scroll_frame, {"transparent": True}, self)

        self.scrollbar_v = AutoScrollbar(
            self.main_content_frame, orient=tk.VERTICAL, command=self.canvas.yview
        )
        self.scrollbar_h = AutoScrollbar(
            self.main_content_frame, orient=tk.HORIZONTAL, command=self.canvas.xview
        )

        self.canvas_window_id = self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        
        def _on_scroll_sync():
            self._scroll_timer = None
            if getattr(self, '_is_rebuilding', False): return
            self._trigger_reslice_all()

        def _on_scroll_v(*args):
            self.scrollbar_v.set(*args)
            if getattr(self, '_is_rebuilding', False) or self._resize_timer: return
            if not self._scroll_timer:
                self.after(SCROLL_SYNC_DELAY, _on_scroll_sync)
        
        def _on_scroll_h(*args):
            self.scrollbar_h.set(*args)
            if getattr(self, '_is_rebuilding', False) or self._resize_timer: return
            if not self._scroll_timer:
                self.after(SCROLL_SYNC_DELAY, _on_scroll_sync)

        self.canvas.configure(yscrollcommand=_on_scroll_v, xscrollcommand=_on_scroll_h)

        self._resize_timer = None
        self._scroll_timer = None

        self.scroll_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.bind("<Visibility>", self._on_visibility)

        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar_v.grid(row=0, column=1, sticky="ns")
        self.scrollbar_h.grid(row=1, column=0, sticky="ew")
        
        # ⚡ EDITOR AIDS: Draw grid and center line if in editor mode
        if self.is_editor:
            self._draw_editor_grid()

        if app_constants.RELOAD_CONFIG_DISPLAYED:
            self.button_frame = ttk.Frame(self)
            self.button_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(5, 10), padx=10)
            ttk.Button(
                self.button_frame, text="Reload Config", command=self._force_rebuild_gui
            ).pack(side=tk.LEFT, pady=10)
        else:
            self.button_frame = None

    def start(self):
        """Starts the building process."""
        if self.json_filepath:
            self._load_and_build_from_file()
        else:
            self._rebuild_gui()
            self.gui_built = True

    def _on_frame_configure(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event=None):
        if getattr(self, '_is_rebuilding', False): return
        width = event.width if event else self.canvas.winfo_width()
        last_w = getattr(self, '_last_reported_width', 0)
        if abs(width - last_w) < RESIZE_WIDTH_THRESHOLD: return
        self._last_reported_width = width
        if self._resize_timer:
            self.after_cancel(self._resize_timer)
        self._resize_timer = self.after(RESIZE_THROTTLE_DELAY, self._perform_canvas_resize, width)
        
        # ⚡ EDITOR REDRAW: Ensure grid and center line are redrawn on canvas resize
        if self.is_editor:
            self.after(RESIZE_THROTTLE_DELAY + 10, self._draw_editor_grid)

    def _draw_editor_grid(self):
        """Draws a 100px grid and a center line on the canvas."""
        if not self.is_editor or not self.canvas.winfo_exists():
            return
            
        self.canvas.delete("editor_grid")
        
        w = max(self.canvas.winfo_width(), self.scroll_frame.winfo_reqwidth())
        h = max(self.canvas.winfo_height(), self.scroll_frame.winfo_reqheight())
        
        # 1. 100px Grid
        grid_color = "#333333"
        for x in range(0, w, 100):
            self.canvas.create_line(x, 0, x, h, fill=grid_color, dash=(2, 4), tags="editor_grid")
        for y in range(0, h, 100):
            self.canvas.create_line(0, y, w, y, fill=grid_color, dash=(2, 4), tags="editor_grid")
            
        # 2. Center Lines
        center_x = w // 2
        center_y = h // 2
        self.canvas.create_line(center_x, 0, center_x, h, fill="#FF9900", width=1, dash=(5, 5), tags="editor_grid")
        self.canvas.create_line(0, center_y, w, center_y, fill="#FF00FF", width=1, dash=(5, 5), tags="editor_grid")
        
        # Lower them so they don't cover widgets
        self.canvas.tag_lower("editor_grid")

    def _perform_canvas_resize(self, width):
        self._resize_timer = None
        self._scroll_timer = None
        if width > 1 and self.canvas_window_id: 
            req_width = self.scroll_frame.winfo_reqwidth()
            req_height = self.scroll_frame.winfo_reqheight()
            canvas_height = self.canvas.winfo_height()
            new_width = max(width, req_width)
            new_height = max(canvas_height, req_height)
            
            # ⚡ ROBUSTNESS: Prevent X11 BadValue (0x0) errors by avoiding configuration 
            # of windows with zero dimensions.
            if new_width <= 1 or new_height <= 1:
                return

            if BUILDER_DEBUG:
                matrix_log("gui", "gui_builder", "_perform_canvas_resize", f"📐 [RESIZE] {self.tab_name}: Canvas={width}x{canvas_height}, Req={req_width}x{req_height} -> New={new_width}x{new_height}", "DEBUG")
            
            try:
                # ⚡ HARDENING: Ensure we never send 0x0 to X11 configuration
                w_cfg = max(1, int(new_width))
                h_cfg = max(1, int(new_height))
                self.canvas.itemconfig(self.canvas_window_id, width=w_cfg, height=h_cfg)
                self._trigger_background_sync(force=True)
            except tk.TclError as e:
                matrix_log("gui", "gui_builder", "_perform_canvas_resize", f"⚠️ Canvas item configuration skipped: {e}", "TRACE")

    def _on_visibility(self, event=None):
        if not self.winfo_exists(): return
        if not self.winfo_ismapped(): return
        if not hasattr(self, 'panel_bg_pil') or self.panel_bg_pil is None:
            self._trigger_background_sync(force=True)
        else:
            self._trigger_reslice_all()

    def _get_widget_context(self) -> WidgetContext:
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
        """
        Updates the background of the canvas and scroll_frame based on the
        show_background_var from the app_instance.
        """
        colors = THEMES.get(DEFAULT_THEME, THEMES["dark"])
        target_bg_color = colors["bg"]

        # ⚡ ROBUSTNESS: Use getattr to safely check for show_background_var on app_instance
        show_bg_toggle = getattr(self.app_instance, 'show_background_var', None)
        if show_bg_toggle and not show_bg_toggle.get():
            target_bg_color = "" # Set to transparent/default to parent
        
        try:
            if self.canvas.cget("background") != target_bg_color:
                self.canvas.configure(background=target_bg_color)
        except tk.TclError: pass

        try:
            if self.scroll_frame.cget("bg") != target_bg_color:
                self.scroll_frame.configure(bg=target_bg_color)
        except tk.TclError: pass

        # Force a reslice if background changes, to ensure widgets adapt.
        self._trigger_reslice_all()
