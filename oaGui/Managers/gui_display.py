# Managers/gui_display.py
# Author: Anthony Peter Kuzub
# Version: 20260315.Modular.1
#
# Description: This file defines the main Application class.

import tkinter as tk
from tkinter import ttk
from loguru import logger

from oaLogging.Methods.matrix_gate import matrix_log
from oaConfigurationManager.FileReaders.config_reader import Config
from oaGui.Core.directory import DirectoryBuilderMixin
from oaGui.Managers.layout_cache import LayoutCacheManager
from oaGui.FileReaders.layout_parser import LayoutParser
from oaGui.Managers.navigation_manager import NavigationManagerMixin
from oaGui.Managers.tab_manager import TabManagerMixin
from oaGui.Managers.window_manager import WindowManager
from oaGuiEditorWYSIWYG.Managers.wysiwyg_editor import WysiwygEditor
from oaGui.Hooks.widget_registry import WidgetRegistry
from oaGui.FileReaders.module_loader import ModuleLoader
from oaOchestration.Constants.project_paths import LAYOUT_CACHE_PATH
from oaStyle.Core.style import DEFAULT_THEME
from oaGui.Interface.top_toolbar import ApplicationToolbar

app_constants = Config.get_instance()

class Application(
    ttk.Frame,
    DirectoryBuilderMixin,
    TabManagerMixin,
    NavigationManagerMixin
):
    """The main application class that orchestrates the GUI build process."""

    def __init__(self, parent, root=None, **kwargs):
        super().__init__(parent)
        self.root = root
        self.app_constants = app_constants
        self.on_complete_callback = kwargs.get("on_complete")

        # Dependency Injection from kwargs
        self.mqtt_connection_manager = kwargs.get("mqtt_connection_manager")
        self.subscriber_router = kwargs.get("subscriber_router")
        self.state_mirror_engine = kwargs.get("state_mirror_engine")
        self.state_cache_manager = kwargs.get("state_cache_manager")
        self.visa_proxy = kwargs.get("visa_proxy")

        # 1. Top Toolbar
        self.top_toolbar = ApplicationToolbar(self, self._launch_wysiwyg_editor)
        self.top_toolbar.pack(side="top", fill="x")

        # 2. Initialization
        WidgetRegistry.scan_widgets()
        self.cache_manager = LayoutCacheManager(LAYOUT_CACHE_PATH)
        self._layout_cache = self.cache_manager.load()
        matrix_log("ui", "gui_shell", "__init__", "🖥️🚦 The grand orchestrator is waking up!", "DEBUG")

        # 3. Engines
        from oaComBroker.Core.protocol_router.manager import ProtocolRouter
        ProtocolRouter.get_instance().start()

        self.theme_colors = self._apply_styles(theme_name=DEFAULT_THEME)
        self.window_manager = WindowManager(self)
        self.layout_parser = LayoutParser(current_version=app_constants.CURRENT_VERSION)
        self.module_loader = ModuleLoader(
            self.theme_colors, self.state_mirror_engine, self.subscriber_router, self
        )

        # 4. Storage & State
        self._notebooks = {}
        self._frames_by_path = {}
        self.last_selected_tab_name = None
        self.show_background_var = tk.BooleanVar(value=True)

        # 5. Resize Handling
        self.global_resizing = False
        self._resize_timer = None
        if self.root: self.root.bind("<Configure>", self._on_global_configure)

        # 6. Kickoff
        self._start_initial_build()

    def _start_initial_build(self):
        try:
            from oaOchestration.Core.path_initializer import GLOBAL_PROJECT_ROOT
            root_dir = GLOBAL_PROJECT_ROOT / "oaGui" / "Assets"
            self.after(10, lambda: self._build_from_directory(
                path=root_dir, parent_widget=self, on_complete=self._on_initial_build_complete))
        except Exception as e:
            logger.exception(f"🖥️🏗️🎨 [DISPLAY] CRITICAL: App initialization failed: {e}")

    def _on_initial_build_complete(self):
        matrix_log("ui", "gui_builder", "_on_initial_build_complete", "✅🏗️ [BUILDER] Initial GUI build complete.", "INFO")

        def _final_settle():
            for loader in self.module_loader.get_all_builders():
                if hasattr(loader, 'dynamic_gui') and loader.dynamic_gui.winfo_exists():
                    builder = loader.dynamic_gui
                    builder._trigger_reslice_all(force=True)
                    builder._trigger_background_sync(force=True)

        self.after(500, _final_settle)
        self.after(750, self._trigger_initial_tab_selection)
        if self.state_cache_manager: self.after(1250, self.state_cache_manager.initialize_state)
        self.after(2250, lambda: self.cache_manager.save(self._layout_cache))
        if self.on_complete_callback: self.on_complete_callback()

    def _on_global_configure(self, event):
        if event.widget == self.root:
            self.global_resizing = True
            if self._resize_timer: self.after_cancel(self._resize_timer)
            self._resize_timer = self.after(200, self._on_resize_finished)

    def _on_resize_finished(self):
        self._resize_timer = None
        self.global_resizing = False
        try: self.event_generate("<<GlobalResizeDone>>")
        except: pass

    def shutdown(self):
        matrix_log("ui", "gui_shell", "shutdown", "Initiating application shutdown...", "DEBUG")
        if self.mqtt_connection_manager: self.mqtt_connection_manager.disconnect()
        if self.visa_proxy: self.visa_proxy.shutdown()

    def _apply_styles(self, theme_name: str):
        from oaStyle.Managers.theme_applier import apply_theme
        return apply_theme(self, theme_name)

    def _launch_wysiwyg_editor(self):
        """Launches the WYSIWYG editor."""
        def _rebuild_main_ui(new_data=None):
            matrix_log("ui", "gui_shell", "_rebuild_main_ui", "🏗️ [TEST] Rebuilding main application...", "INFO")
            from oaOchestration.Core.path_initializer import GLOBAL_PROJECT_ROOT
            root_dir = GLOBAL_PROJECT_ROOT / "oaGui" / "Assets"

            for child in self.winfo_children():
                if child != self.top_toolbar: child.destroy()

            self._notebooks = {}; self._frames_by_path = {}
            self._build_from_directory(path=root_dir, parent_widget=self, on_complete=self._on_initial_build_complete)

        WysiwygEditor.launch(self.root, on_test_callback=_rebuild_main_ui,
                             subscriber_router=self.subscriber_router, state_mirror_engine=self.state_mirror_engine)
