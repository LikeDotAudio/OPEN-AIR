#!/usr/bin/env python3
# managers/Display/open_air_ui.py
# Modularized Dynamic UI Partition for OPEN-AIR.
# Version 20260315.Modular.1

import sys
import pathlib
import threading
from loguru import logger

# Ensure root directory is in the search path
current_dir = pathlib.Path(__file__).resolve().parent
project_root = current_dir.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from managers.configini.config_reader import Config
from workers.logger.logger import set_log_directory
from workers.initialization.path_initializer import initialize_paths
from managers.configini.console_encoder import configure_console_encoding
from workers.splash_screen.splash_screen import SplashScreen

# --- EXTRACTED CORE MODULES ---
from managers.Display.core.ui_window_manager import UIWindowManager
from managers.Display.core.shutdown_coordinator import ShutdownCoordinator
from managers.Display.core.bootstrap_sequence import AsyncBootstrapEngine

LOCAL_DEBUG = True

def main():
    """Orchestrates the startup, execution, and shutdown of the OPEN-AIR UI."""
    # 1. Environment Initialization
    GLOBAL_PROJECT_ROOT, data_dir = initialize_paths()
    set_log_directory(pathlib.Path(data_dir) / "debug", partition="UI")
    configure_console_encoding()
    app_constants = Config.get_instance()
    
    if LOCAL_DEBUG: logger.debug("🖥️🎨 [UI] Starting OpenAir UI Service...")

    # 2. Tkinter Environment Setup
    root = UIWindowManager.create_root_window()

    # 3. Splash Screen Initiation
    splash = SplashScreen(root, app_constants.CURRENT_VERSION, app_constants.global_settings["debug_enabled"])
    # root.update() # This might be needed to ensure splash screen is drawn immediately

    # MODIFICATION: Reveal the main window after creation and before mainloop
    UIWindowManager.reveal_main_window(root, splash, app_constants.global_settings["debug_enabled"])

    # Shared Manager Registry
    shared_instances = {
        "app": None, "mqtt_conn": None, "state_cache": None,
        "mirror_engine": None, "osc_manager": None, "snmp_manager": None,
        "midi_manager": None, "splinker_manager": None, "protocol_router": None
    }

    # 4. Shutdown Coordinator
    shutdown_coordinator = ShutdownCoordinator(root, shared_instances, LOCAL_DEBUG)
    shutdown_coordinator.attach_to_root()

    # 5. Resource Management
    def _periodic_gc():
        import gc; gc.collect()
        if not getattr(root, '_shutdown', False): root.after(30000, _periodic_gc)
    _periodic_gc()

    # 6. Bootstrap Engine
    bootstrap_engine = AsyncBootstrapEngine(root, splash, shared_instances, app_constants, shutdown_coordinator)
    threading.Thread(target=bootstrap_engine.run, daemon=True).start()
    
    if LOCAL_DEBUG: logger.debug("🖥️🎨 [UI] Entering Tkinter MainLoop.")
    root.mainloop()

if __name__ == "__main__":
    main()
