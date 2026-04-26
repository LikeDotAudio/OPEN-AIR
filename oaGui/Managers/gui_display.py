# Managers/gui_display.py
# Author: Anthony Peter Kuzub
# Version: 20260315.Modular.1
#
# Description: This file defines the main Application class, which orchestrates the GUI build process.

from oaLogging.Methods.matrix_gate import is_debug_allowed, matrix_log


def _is_debug():
    return is_debug_allowed(system="UI", element="GUI_SHELL")

from oaConfigurationManager.FileReaders.config_reader import Config

app_constants = Config.get_instance()

import tkinter as tk
from tkinter import ttk

from oaGui.Core.directory import DirectoryBuilderMixin

# --- EXTRACTED CORE MODULES ---
from oaGui.Core.layout_cache import LayoutCacheManager
from oaGui.Core.layout_parser import LayoutParser
from oaGui.Core.navigation import NavigationManagerMixin
from oaGui.Core.tab import TabManagerMixin

# --- Module Imports ---
from oaGui.Core.window import WindowManager
from oaGuiEditorWYSIWYG.Managers.wysiwyg_editor import WysiwygEditor
from oaGui.Core.factory.widget_registry import WidgetRegistry
from oaGui.FileReaders.module_loader import ModuleLoader
from oaOchestration.Constants.project_paths import LAYOUT_CACHE_PATH
from oaStyle.Core.style import DEFAULT_THEME


class Application(
    ttk.Frame,
    DirectoryBuilderMixin,
    TabManagerMixin,
    NavigationManagerMixin
):
    """
    The main application class that orchestrates the GUI build process.
    Refactored to use modular components for caching, building, and tab management.
    """

    def __init__(
        self,
        parent,
        root=None,
        mqtt_connection_manager=None,
        subscriber_router=None,
        state_mirror_engine=None,
        state_cache_manager=None,
        osc_manager=None,
        aes70_manager=None,
        snmp_manager=None,
        midi_manager=None,
        visa_proxy=None,
        on_complete=None,
    ):
        super().__init__(parent)
        self.root = root
        self.app_constants = app_constants
        self.on_complete_callback = on_complete

        # --- TOP TOOLBAR ---
        self.top_toolbar = tk.Frame(self, bg="#333333", height=30)
        self.top_toolbar.pack(side="top", fill="x")

        tk.Label(self.top_toolbar, text="OPEN-AIR CORE", bg="#333333", fg="white", font=("Arial", 9, "bold")).pack(side="left", padx=10)

        tk.Button(self.top_toolbar, text="Launch WYSIWYG Editor", bg="#444444", fg="#00FF00",
                  font=("Arial", 8, "bold"), relief="flat", padx=10,
                  command=self._launch_wysiwyg_editor).pack(side="right", padx=10, pady=2)

        # ⚡ AUTO-DISCOVERY
        WidgetRegistry.scan_widgets()

        # ⚡ CACHE MANAGER
        self.cache_manager = LayoutCacheManager(LAYOUT_CACHE_PATH)
        self._layout_cache = self.cache_manager.load()

        matrix_log("ui", "gui_shell", "__init__", "🖥️🚦 The grand orchestrator is waking up!", "DEBUG")

        # Dependency Injection
        self.mqtt_connection_manager = mqtt_connection_manager
        self.subscriber_router = subscriber_router
        self.state_mirror_engine = state_mirror_engine
        self.state_cache_manager = state_cache_manager
        self.osc_manager = osc_manager
        self.aes70_manager = aes70_manager
        self.snmp_manager = snmp_manager
        self.midi_manager = midi_manager
        self.visa_proxy = visa_proxy

        # ⚡ PROTOCOL ROUTER
        from oaComBroker.Core.protocol_router.manager import ProtocolRouter
        ProtocolRouter.get_instance().start()

        # Utility classes
        self.theme_colors = self._apply_styles(theme_name=DEFAULT_THEME)
        self.window_manager = WindowManager(self)
        self.layout_parser = LayoutParser(current_version=app_constants.CURRENT_VERSION)
        self.module_loader = ModuleLoader(
            self.theme_colors,
            state_mirror_engine=self.state_mirror_engine,
            subscriber_router=self.subscriber_router,
            app_instance=self,
        )

        # Storage
        self._notebooks = {}
        self._frames_by_path = {}
        self.last_selected_tab_name = None

        # Display Toggles
        self.show_background_var = tk.BooleanVar(value=True) # Toggle for background visibility

        # Resize Debouncing
        self.global_resizing = False
        self._resize_timer = None
        if self.root:
            self.root.bind("<Configure>", self._on_global_configure)

        try:
            from oaOchestration.Core.path_initializer import GLOBAL_PROJECT_ROOT
            root_dir = GLOBAL_PROJECT_ROOT / "oaGui" / "Assets"

            def _start_build():
                self._build_from_directory(path=root_dir, parent_widget=self,
                                           on_complete=self._on_initial_build_complete)

            self.after(10, _start_build)
        except Exception as e:
            logger.exception(f"🖥️🏗️🎨 [DISPLAY] CRITICAL: App initialization failed: {e}")

    def _on_initial_build_complete(self):
        matrix_log("ui", "gui_builder", "_on_initial_build_complete", "✅🏗️ [BUILDER] Initial GUI build complete. Performing final settle...", "INFO")

        # ⚡ FINAL SETTLE: After all widgets are created and the layout has had a moment
        # to calculate, trigger a final, forced reslice and background sync on all builders.
        # DELAY INCREASED: To 500ms to allow X11 window manager to assign geometry.
        def _final_settle():
            for loader_instance in self.module_loader.get_all_builders():
                if loader_instance and hasattr(loader_instance, 'dynamic_gui') and loader_instance.dynamic_gui.winfo_exists():
                    builder = loader_instance.dynamic_gui
                    builder._trigger_reslice_all(force=True)
                    builder._trigger_background_sync(force=True)

        self.after(500, _final_settle)
        self.after(750, self._trigger_initial_tab_selection)
        if self.state_cache_manager:
            self.after(1250, self.state_cache_manager.initialize_state)
        self.after(2250, lambda: self.cache_manager.save(self._layout_cache))
        if self.on_complete_callback:
            self.on_complete_callback()

    def _on_global_configure(self, event):
        if event.widget == self.root:
            self.global_resizing = True
            if self._resize_timer:
                self.after_cancel(self._resize_timer)
            self._resize_timer = self.after(200, self._on_resize_finished)

    def _on_resize_finished(self):
        self._resize_timer = None
        self.global_resizing = False
        try:
            self.event_generate("<<GlobalResizeDone>>")
        except: pass

    def shutdown(self):
        matrix_log("ui", "gui_shell", "shutdown", "Initiating application shutdown...", "DEBUG")
        if self.mqtt_connection_manager: self.mqtt_connection_manager.disconnect()
        if self.visa_proxy: self.visa_proxy.shutdown()

    def _apply_styles(self, theme_name: str):
        from oaStyle.Managers.theme_applier import apply_theme
        return apply_theme(self, theme_name)

    def print_to_console(self, message: str):
        matrix_log("ui", "gui_shell", "print_to_console", f"🖥️💬 Observer's Log: {message}", "DEBUG")

    def _launch_wysiwyg_editor(self):
        """Launches the WYSIWYG editor for the currently loaded layout or a new one."""
        matrix_log("ui", "gui_shell", "_launch_wysiwyg_editor", "🚀 [EDITOR] Launching WYSIWYG Designer...", "INFO")

        def _rebuild_main_ui(new_data=None):
            """Callback for the editor to test new GUI definitions."""
            matrix_log("ui", "gui_shell", "_rebuild_main_ui", "🏗️ [TEST] Rebuilding main application with editor state...", "INFO")
            # For simplicity, we trigger a clean build from Assets
            from oaOchestration.Core.path_initializer import GLOBAL_PROJECT_ROOT
            root_dir = GLOBAL_PROJECT_ROOT / "oaGui" / "Assets"

            # Wipe current UI (Simplified)
            for child in self.winfo_children():
                if child != self.top_toolbar:
                    child.destroy()

            # Re-initialize storage
            self._notebooks = {}
            self._frames_by_path = {}

            # If new_data is provided, we'd ideally pass it to _build_from_directory
            # to override the disk version.
            self._build_from_directory(path=root_dir, parent_widget=self,
                                       on_complete=self._on_initial_build_complete)

        WysiwygEditor.launch(self.root, on_test_callback=_rebuild_main_ui)
