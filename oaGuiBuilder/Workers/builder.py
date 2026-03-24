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
LOCAL_DEBUG = False    
from oaLogging.Core.logger import initialize_logging, set_log_directory, builder_logger
from loguru import logger

from oaConfiguration.FileReaders.config_reader import Config
app_constants = Config.get_instance()

from oaStyle.Core.style import DEFAULT_THEME, THEMES

# --- 1. CORE MIXINS ---
from oaStyle.Core.gui_style import GuiStyleMixin
from oaGuiManager.Core.factory.gui_widget_factory import GuiWidgetFactoryMixin
from oaGuiBuildShell.Managers.gui_mqtt import GuiMqttManagerMixin
from oaGuiManager.FileReaders.gui_file_loader import GuiFileLoaderMixin
from oaGuiBuildShell.Managers.gui_re import GuiRebuilderMixin
from oaGuiBuildShell.Managers.gui_batch import GuiBatchBuilderMixin
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

        # State Initialization
        self.tab_name = tab_name
        self.on_complete_callback = config.get("on_complete")
        self.state_mirror_engine = config.get("state_mirror_engine")
        self.subscriber_router = config.get("subscriber_router")
        self.app_instance = config.get("app_instance")
        self.on_focus_widget = config.get("on_focus_widget")
        self.is_editor = config.get("is_editor", False)
        
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
        
        self.tracking_service = UITrackingService()

        # 1. Initialize Core Components
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

        # 2. GUI Scaffolding
        self.config(style="Dark.TFrame")
        if not use_grid:
            self.pack(fill=tk.BOTH, expand=True)
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.main_content_frame = ttk.Frame(self, style="Dark.TFrame")
        self.main_content_frame.grid(row=0, column=0, sticky="nsew")
        self.main_content_frame.grid_rowconfigure(0, weight=1)
        self.main_content_frame.grid_columnconfigure(0, weight=1)

        colors = THEMES.get(DEFAULT_THEME, THEMES["dark"])
        self.canvas = tk.Canvas(
            self.main_content_frame, background=colors["bg"], bd=0, highlightthickness=0
        )
        # ⚡ FIX: scroll_frame MUST be a Frame for grid propagation to work with Canvas scrolling.
        self.scroll_frame = tk.Frame(self.canvas, bd=0, highlightthickness=0, bg=colors["bg"])

        TransparencyManager.apply_transparency(self, self.scroll_frame, {"transparent": True}, self)


        self.scrollbar_v = AutoScrollbar(
            self.main_content_frame, orient=tk.VERTICAL, command=self.canvas.yview
        )
        self.scrollbar_h = AutoScrollbar(
            self.main_content_frame, orient=tk.HORIZONTAL, command=self.canvas.xview
        )

        self.canvas_window_id = self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        
        # Scroll sync internal handlers
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
        
        # 3. Reload Button
        if app_constants.RELOAD_CONFIG_DISPLAYED:
            self.button_frame = ttk.Frame(self)
            self.button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(5, 10), padx=10)
            ttk.Button(
                self.button_frame, text="Reload Config", command=self._force_rebuild_gui
            ).pack(side=tk.LEFT, pady=10)
        else:
            self.button_frame = None

        # 4. Context Menu via Mixin
        self._setup_context_menu()

        # 5. Trigger Build
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

    def _perform_canvas_resize(self, width):
        self._resize_timer = None
        self._scroll_timer = None
        if width > 1 and self.canvas_window_id: 
            req_width = self.scroll_frame.winfo_reqwidth()
            req_height = self.scroll_frame.winfo_reqheight()
            canvas_height = self.canvas.winfo_height()
            new_width = max(width, req_width)
            new_height = max(canvas_height, req_height)
            self.canvas.itemconfig(self.canvas_window_id, width=new_width, height=new_height)
            self._trigger_background_sync()

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
