# oaGui/Workers/builder.py
# Author: Anthony Peter Kuzub
# Version: 20260416.Modular.1
#
# Description: Main Orchestrator for the Dynamic GUI Builder.
# Constructs a pixel-perfect, background-aware industrial UI from JSON state.

import tkinter as tk
from pathlib import Path

from oaConfigurationManager.FileReaders.config_reader import Config
from oaGui.Managers.dynamic_widget_renderer import DynamicWidgetRendererMixin
from oaGui.Hooks.gui_mqtt import GuiMqttManagerMixin
from oaGui.Managers.gui_re import GuiRebuilderMixin
from oaGuiElements.Core.background import BuilderBackgroundManagerMixin
from oaGui.Constants.builder_constants import SCROLL_SYNC_DELAY
from oaGuiElements.Core.breakoff.window_breakoff_manager import WindowBreakoffManagerMixin

# --- MODULAR MIXINS ---
from oaGui.Hooks.context_menu import BuilderContextMenuMixin
from oaGui.Managers.slicing_registry import BuilderSlicingRegistryMixin
from oaGuiElements.Core.input.input_mousewheel_mixin.input_mousewheel_mixin import MousewheelScrollMixin
from oaGui.Core.context.widget_context import WidgetContext
from oaGui.Hooks.gui_widget_factory import GuiWidgetFactoryMixin
from oaGui.Core.telemetry.ui_tracking_service import UITrackingService

# --- ENGINE SERVICES ---
from oaGui.Workers.transparency.transparency import TransparencyManager
from oaGui.Workers.transparency.transparency_mixin import TransparencyMixin
from oaGui.FileReaders.gui_file_loader import GuiFileLoaderMixin

# --- MODULAR COMPONENTS ---
from oaGui.Interface.auto_scrollbar import AutoScrollbar
from oaGui.Interface.builder_footer import BuilderFooter
from oaGui.Managers.builder_layout_manager import BuilderLayoutManager
from oaGuiEditorWYSIWYG.Methods.builder_editor_grid import BuilderEditorGrid

# --- GLOBAL ARCHITECTURE ---
from oaStyle.Core.gui_style import GuiStyleMixin
from oaStyle.Core.style import DEFAULT_THEME, THEMES

class DynamicGuiBuilder(
    tk.Frame,
    GuiMqttManagerMixin,
    GuiStyleMixin,
    GuiWidgetFactoryMixin,
    GuiFileLoaderMixin,
    GuiRebuilderMixin,
    DynamicWidgetRendererMixin,
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
        theme = THEMES.get(DEFAULT_THEME, THEMES["dark"])
        super().__init__(master=parent, bg=theme["bg"])

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
        self.state_mirror_engine = config.get("state_mirror_engine")
        self.subscriber_router = config.get("subscriber_router")
        self.app_instance = config.get("app_instance")
        self.on_focus_widget = config.get("on_focus_widget")
        self.is_editor = config.get("is_editor", False)
        self.allow_horizontal_scroll = config.get("allow_horizontal_scroll", True)
        self.allow_scrolling = config.get("allow_scrolling", True)
        self.is_transparent = config.get("transparent", False) or (self.parent_builder is not None)
        self._render_tier = config.get("render_tier", "high_res")
        self.config_data, self.tk_vars, self.topic_widgets = {}, {}, {}
        self._slicing_registry, self._is_rebuilding = [], False
        self.last_build_hash, self.gui_built = None, False

    def _initialize_builder_services(self, config):
        """Bootstraps telemetry and communication services."""
        self.tracking_service = UITrackingService()
        self._initialize_mqtt_context(self.json_filepath, Config.get_instance(), config.get("base_mqtt_topic_from_path"))
        self._initialize_widget_factory()
        self.layout_manager = BuilderLayoutManager(self)
        self.tracking_service.track(self, self.tab_name, self.state_mirror_engine, self.base_mqtt_topic_from_path)

    def _build_ui_scaffolding(self, use_grid):
        """Orchestrates the physical container hierarchy construction."""
        theme = THEMES.get(DEFAULT_THEME, THEMES["dark"])
        self.config(bg=theme["bg"])
        self.grid_rowconfigure(0, weight=1); self.grid_columnconfigure(0, weight=1)

        self._setup_main_container(theme["bg"])
        self._setup_scroll_system(theme["bg"])
        self._setup_footer_bar()
        self._apply_initial_transparency()
        
        if self.canvas and self.is_editor: 
            BuilderEditorGrid.draw(self.canvas, self.scroll_frame, True)

    def _setup_main_container(self, bg):
        """Creates the primary content frame."""
        self.main_content_frame = tk.Frame(self, bg=bg, bd=0, highlightthickness=0)
        self.main_content_frame.grid(row=0, column=0, sticky="nsew")
        self.main_content_frame.grid_rowconfigure(0, weight=1)
        self.main_content_frame.grid_columnconfigure(0, weight=1)

    def _setup_scroll_system(self, bg):
        """Configures the canvas-based scrolling system or fallback static frame."""
        if self.allow_scrolling:
            self.canvas = tk.Canvas(self.main_content_frame, background=bg, bd=0, highlightthickness=0)
            self.scroll_frame = tk.Frame(self.canvas, bd=0, highlightthickness=0, bg=bg)
            self.canvas_window_id = self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
            self._setup_scrolling_controls()
            self._setup_event_bindings()
            self.canvas.grid(row=0, column=0, sticky="nsew")
        else:
            self.scroll_frame = tk.Frame(self.main_content_frame, bd=0, highlightthickness=0, bg=bg)
            self.scroll_frame.grid(row=0, column=0, sticky="nsew")
            self.canvas, self.canvas_window_id = None, None
            self.scroll_frame.bind("<Configure>", lambda e: self._trigger_background_sync())

    def _setup_scrolling_controls(self):
        """Wires up the industrial scrollbars to the canvas."""
        self.scrollbar_v = AutoScrollbar(self.main_content_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self._on_scroll_v)
        self.scrollbar_v.grid(row=0, column=1, sticky="ns")

        if self.allow_horizontal_scroll:
            self.scrollbar_h = AutoScrollbar(self.main_content_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
            self.canvas.configure(xscrollcommand=self._on_scroll_h)
            self.scrollbar_h.grid(row=1, column=0, sticky="ew")

    def _setup_footer_bar(self):
        """Integrates the builder footer if enabled in configuration."""
        if getattr(Config.get_instance(), 'FOOTER_ENABLED', False):
            self.footer = BuilderFooter(self.main_content_frame)
            self.footer.grid(row=2, column=0, columnspan=2, sticky="ew")
        else:
            self.footer = None

    def _apply_initial_transparency(self):
        """Applies high-res transparency layers to core scaffolding."""
        if not self.is_transparent or not self.parent_builder: return
        TransparencyManager.apply_transparency(self.main_content_frame, None, {"type": "OcaBlock"}, self.parent_builder)
        if self.canvas:
            TransparencyManager.apply_transparency(self.canvas, self.canvas, {"type": "OcaBin"}, self.parent_builder)
        TransparencyManager.apply_transparency(self.scroll_frame, None, {"type": "OcaBlock"}, self.parent_builder)

    def _on_scroll_v(self, *args):
        self.scrollbar_v.set(*args)
        self._trigger_scroll_sync()

    def _on_scroll_h(self, *args):
        self.scrollbar_h.set(*args)
        self._trigger_scroll_sync()

    def _setup_event_bindings(self):
        """Standardizes lifecycle and resizing event handlers."""
        self._scroll_timer = None
        self.scroll_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", self.layout_manager.on_canvas_configure)
        self.bind("<Visibility>", self._on_visibility)

    def start(self):
        """Triggers the physical UI build sequence."""
        if self.json_filepath:
            self._load_and_build_from_file()
        else:
            self._rebuild_gui()

    def _trigger_scroll_sync(self):
        """Debounces reslicing notifications during continuous scrolling."""
        if self._is_rebuilding or getattr(self.layout_manager, '_resize_timer', None): return
        if not getattr(self, '_scroll_timer', None):
            self._scroll_timer = self.after(SCROLL_SYNC_DELAY, self._perform_scroll_sync)

    def _perform_scroll_sync(self):
        self._scroll_timer = None
        if not self._is_rebuilding: self._trigger_reslice_all()

    def _log_telemetry_tx(self, message):
        if self.footer: self.footer.log_telemetry_tx(message)

    def _log_command_tx(self, message):
        if self.footer: self.footer.log_command_tx(message)

    def _on_gui_visible(self, event=None):
        """Ensures background synchronization occurs only when the UI is physical."""
        if not self.winfo_exists() or not self.winfo_ismapped(): return
        self._configure_parent_layout()
        self.update()
        self._handle_initial_resize()
        self._sync_background_state()

    def _configure_parent_layout(self):
        """Ensures the parent widget correctly expands to house the builder."""
        try:
            parent = self.nametowidget(self.winfo_parent())
            parent.grid_rowconfigure(0, weight=1)
            parent.grid_columnconfigure(0, weight=1)
        except Exception: pass

    def _handle_initial_resize(self):
        """Triggers the first geometric layout pass."""
        w, h = self.winfo_width(), self.winfo_height()
        if w > 1 and h > 1:
            self.layout_manager.perform_canvas_resize(w, h)
            self._log_telemetry_tx(f"GEO: {w}x{h}")

    def _sync_background_state(self):
        """Ensures transparency and background slices are synchronized."""
        if not hasattr(self, 'panel_bg_pil') or self.panel_bg_pil is None:
            self._trigger_background_sync(force=True)
        else:
            self._trigger_reslice_all()

    def _on_visibility(self, event=None):
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
        """Synchronizes canvas and frame backgrounds with the global theme."""
        theme_bg = THEMES.get(DEFAULT_THEME, THEMES["dark"])["bg"]
        for w in [getattr(self, 'canvas', None), getattr(self, 'scroll_frame', None)]:
            if w is None: continue
            try:
                bg_key = "bg" if w == getattr(self, 'scroll_frame', None) else "background"
                if w.cget(bg_key) != theme_bg: w.configure(**{bg_key: theme_bg})
            except tk.TclError: pass
        self._trigger_reslice_all()
reslice_all()
