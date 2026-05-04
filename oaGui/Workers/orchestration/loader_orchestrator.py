# oaGui/Workers/loader_orchestrator.py
# Author: Anthony Peter Kuzub
# Version: 20260502.1000.1
#
# Description: Main Orchestrator for the Dynamic GUI Builder.
# Constructs a pixel-perfect, background-aware industrial UI from JSON state.

import tkinter as tk
from oaStyle.Core.style import DEFAULT_THEME, THEMES

# --- ENGINE SERVICES ---
from oaGui.Workers.compositing.sync_behavior import SyncBehavior
from oaGui.Core.context.cache_widget_context import WidgetContext
from oaGui.Workers.compositing.engine_visual_effects import EngineVisualEffects

# --- MODULAR MIXINS ---
from oaGui.Managers.assembler.engine_widget_assembler import EngineWidgetAssemblerMixin
from oaGui.Hooks.events.interaction_mqtt_gateway import InteractionMqttGatewayMixin
from oaGui.Managers.lifecycle.loader_lifecycle_service import LifecycleManagerMixin
from oaGuiElements.Core.background import BuilderBackgroundManagerMixin
from oaGuiElements.Core.breakoff.Core.window_breakoff_manager import WindowBreakoffManagerMixin
from oaGui.Hooks.menu.context_menu import BuilderContextMenuMixin
from oaGui.Managers.refresh.engine_refresh_coordinator import RefreshCoordinatorMixin
from oaGuiElements.Core.input.input_mousewheel_mixin.input_mousewheel_mixin import MousewheelScrollMixin
from oaGui.Hooks.registry.gui_widget_factory import GuiWidgetFactoryMixin
from oaGui.FileReaders.loader.gui_file_loader import GuiFileLoaderMixin
from oaStyle.Core.gui_style import GuiStyleMixin

# --- ORCHESTRATOR MODULES ---
from .builder_initializer import BuilderInitializer
from .scaffolding_builder import ScaffoldingBuilder
from oaGui.Constants.builder_constants import SCROLL_SYNC_DELAY

class LoaderOrchestrator(
    tk.Frame,
    InteractionMqttGatewayMixin,
    GuiStyleMixin,
    GuiWidgetFactoryMixin,
    GuiFileLoaderMixin,
    LifecycleManagerMixin,
    EngineWidgetAssemblerMixin,
    SyncBehavior,
    BuilderContextMenuMixin,
    BuilderBackgroundManagerMixin,
    RefreshCoordinatorMixin,
    MousewheelScrollMixin,
    WindowBreakoffManagerMixin,
):
    """Orchestrates the construction and lifecycle of a dynamic industrial UI."""

    def __init__(self, parent, json_path=None, tab_name=None, use_grid=False, *args, **kwargs):
        config = kwargs.pop("config", {})
        theme = THEMES.get(DEFAULT_THEME, THEMES["dark"])
        super().__init__(master=parent, bg=theme["bg"])

        self.parent_builder = self._find_parent_builder(parent)
        
        # ⚡ MODULAR INITIALIZATION
        BuilderInitializer.initialize_state(self, json_path, tab_name, config, self.parent_builder)
        BuilderInitializer.initialize_services(self, config)
        
        # ⚡ MODULAR SCAFFOLDING
        ScaffoldingBuilder.build(self, use_grid)
        
        self._setup_context_menu()

    def _find_parent_builder(self, parent_widget):
        """Traverses up the widget tree to find a parent LoaderOrchestrator."""
        curr = parent_widget
        while curr:
            if hasattr(curr, 'builder_instance') and curr.builder_instance:
                return curr.builder_instance
            if isinstance(curr, LoaderOrchestrator):
                return curr
            parent_path = curr.winfo_parent()
            if not parent_path: break
            curr = curr.nametowidget(parent_path)
        return None

    def start(self):
        """Triggers the physical UI build sequence."""
        if self.json_filepath:
            self._load_and_build_from_file()
        else:
            self._rebuild_gui()

    def _on_scroll_v(self, *args):
        self.scrollbar_v.set(*args)
        self._trigger_scroll_sync()

    def _on_scroll_h(self, *args):
        self.scrollbar_h.set(*args)
        self._trigger_scroll_sync()

    def _setup_event_bindings(self):
        """Standardizes lifecycle and resizing event handlers."""
        self._scroll_timer = None
        self.canvas.bind("<Configure>", self.layout_manager.on_canvas_configure)
        self.bind("<Visibility>", self._on_visibility)

    def _trigger_scroll_sync(self):
        """Debounces reslicing notifications during continuous scrolling."""
        if self._is_rebuilding or getattr(self.layout_manager, '_resize_timer', None): return
        if not getattr(self, '_scroll_timer', None):
            self._scroll_timer = self.after(SCROLL_SYNC_DELAY, self._perform_scroll_sync)

    def _perform_scroll_sync(self):
        self._scroll_timer = None
        if not self._is_rebuilding: self._trigger_reslice_all()

    def _log_telemetry_tx(self, message):
        if hasattr(self, 'footer') and self.footer: self.footer.log_telemetry_tx(message)

    def _log_command_tx(self, message):
        if hasattr(self, 'footer') and self.footer: self.footer.log_command_tx(message)

    def _on_gui_visible(self, event=None):
        """Ensures background synchronization occurs only when the UI is physical."""
        if not self.winfo_exists() or not self.winfo_ismapped(): return
        self._configure_parent_layout()
        self.update()
        self._handle_initial_resize()
        self._sync_background_state()

    def _configure_parent_layout(self):
        """Ensures the parent widget correctly expands to house the orchestrator."""
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
            transparency_manager=EngineVisualEffects,
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
