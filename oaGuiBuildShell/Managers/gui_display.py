# Managers/gui_display.py
# Author: Anthony Peter Kuzub
# Version: 20260315.Modular.1
#
# Description: This file defines the main Application class, which orchestrates the GUI build process.

LOCAL_DEBUG = False    
from oaLogging.Core.logger import initialize_logging, set_log_directory
from loguru import logger

from oaConfiguration.FileReaders.config_reader import Config
app_constants = Config.get_instance()

import os
import tkinter as tk
from tkinter import ttk
import pathlib

# --- Module Imports ---
from oaGuiBuildShell.Core.window import WindowManager
from oaGuiManager.FileReaders.module_loader import ModuleLoader
from oaGuiManager.Core.parser.layout_parser import LayoutParser
from oaStyle.Core.style import THEMES, DEFAULT_THEME
from oaOchestration.Constants.project_paths import LAYOUT_CACHE_PATH
from oaGuiManager.Core.factory.widget_registry import WidgetRegistry

# --- EXTRACTED CORE MODULES ---
from oaGuiBuildShell.Core.layout_cache import LayoutCacheManager
from oaGuiBuildShell.Core.directory import DirectoryBuilderMixin
from oaGuiBuildShell.Core.tab import TabManagerMixin
from oaGuiBuildShell.Core.navigation import NavigationManagerMixin

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

        # ⚡ AUTO-DISCOVERY
        WidgetRegistry.scan_widgets()

        # ⚡ CACHE MANAGER
        self.cache_manager = LayoutCacheManager(LAYOUT_CACHE_PATH)
        self._layout_cache = self.cache_manager.load()

        if LOCAL_DEBUG: logger.debug("🖥️🚦 The grand orchestrator is waking up!")

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
        
        # Resize Debouncing
        self.global_resizing = False
        self._resize_timer = None
        if self.root:
            self.root.bind("<Configure>", self._on_global_configure)

        try:
            from oaOchestration.Core.path_initializer import GLOBAL_PROJECT_ROOT
            root_dir = GLOBAL_PROJECT_ROOT / "oaGuiDefinitions"
            
            def _start_build():
                self._build_from_directory(path=root_dir, parent_widget=self, 
                                           on_complete=self._on_initial_build_complete)

            self.after(10, _start_build)
        except Exception as e:
            logger.exception(f"🖥️🏗️🎨 [DISPLAY] CRITICAL: App initialization failed: {e}")

    def _on_initial_build_complete(self):
        if LOCAL_DEBUG: logger.debug("🖥️🏗️🎨 [DISPLAY] Initial build pass finished.")
        self.after(500, self._trigger_initial_tab_selection)
        if self.state_cache_manager:
            self.after(1000, self.state_cache_manager.initialize_state)
        self.after(2000, lambda: self.cache_manager.save(self._layout_cache))
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
        if LOCAL_DEBUG: logger.debug("Initiating application shutdown...")
        if self.mqtt_connection_manager: self.mqtt_connection_manager.disconnect()
        if self.visa_proxy: self.visa_proxy.shutdown()

    def _apply_styles(self, theme_name: str):
        from oaStyle.Managers.theme_applier import apply_theme
        return apply_theme(self, theme_name)
    
    def print_to_console(self, message: str):
        if LOCAL_DEBUG: logger.debug(f"🖥️💬 Observer's Log: {message}")
