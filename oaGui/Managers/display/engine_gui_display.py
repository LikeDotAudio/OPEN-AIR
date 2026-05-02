# Managers/engine_gui_display.py
# Author: Anthony Peter Kuzub
# Version: 20260502.1000.1
#
# Description: This file defines the main EngineGuiDisplay class.

import tkinter as tk
from tkinter import ttk

from oaLogging.Methods.matrix_gate import matrix_log
from oaConfigurationManager.FileReaders.config_reader import Config
from oaGui.FileReaders.scanner.folder_recursive_scanner import FolderRecursiveScannerMixin
from oaGui.Managers.persistence.cache_layout_store import CacheLayoutStore
from oaGui.FileReaders.scanner.folder_layout_interpreter import FolderLayoutInterpreter
from oaGui.Managers.interaction.interaction_navigation import InteractionNavigationMixin
from oaGui.Managers.tabs.tab_orchestrator import TabOrchestratorMixin
from oaGui.Managers.display.tab_window_manager import TabWindowManager
from oaGuiEditorWYSIWYG.Managers.wysiwyg_editor import WysiwygEditor
from oaGui.Hooks.registry.registry_widget_store import RegistryWidgetStore
from oaGui.FileReaders.loader.loader_facade import LoaderFacade
from oaOchestration.Constants.project_paths import LAYOUT_CACHE_PATH
from oaStyle.Core.style import DEFAULT_THEME
from oaGui.Interface.controls.top_toolbar import ApplicationToolbar

# --- ATOMIC SERVICES ---
from .app_igniter import ignite_application_build
from .post_build_finalizer import finalize_gui_settlement
from .resize_handler import handle_global_resize
from .app_shutdown_service import orchestrate_app_shutdown

app_constants = Config.get_instance()

class EngineGuiDisplay(
    ttk.Frame,
    FolderRecursiveScannerMixin,
    TabOrchestratorMixin,
    InteractionNavigationMixin
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
        RegistryWidgetStore.scan_widgets()
        self.cache_manager = CacheLayoutStore(LAYOUT_CACHE_PATH)
        self._layout_cache = self.cache_manager.load()
        matrix_log("ui", "gui_shell", "__init__", "🖥️🚦 The grand orchestrator is waking up!", "DEBUG")

        # 3. Engines
        from oaComBroker.Core.protocol_router.manager import ProtocolRouter
        ProtocolRouter.get_instance().start()

        self.theme_colors = self._apply_styles(theme_name=DEFAULT_THEME)
        self.tab_window_manager = TabWindowManager(self)
        self.layout_parser = FolderLayoutInterpreter(current_version=app_constants.CURRENT_VERSION)
        self.loader_facade = LoaderFacade(
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
        """Kickoff handled by atomic service."""
        from oaOchestration.Core.path_initializer import GLOBAL_PROJECT_ROOT
        ignite_application_build(self, GLOBAL_PROJECT_ROOT / "oaGui" / "Assets")

    def _on_initial_build_complete(self):
        """Finalization handled by atomic service."""
        finalize_gui_settlement(self)

    def _on_global_configure(self, event):
        """Resize lifecycle handled by atomic service."""
        handle_global_resize(self, event)

    def shutdown(self):
        """Shutdown orchestrated by atomic service."""
        orchestrate_app_shutdown(self)

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
