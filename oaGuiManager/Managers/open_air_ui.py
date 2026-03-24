# Managers/open_air_ui.py
# Author: Anthony Peter Kuzub
# Version: 20260315.Modular.1
#
# Description: !/usr/bin/env python3

import sys
import pathlib
import threading
from loguru import logger

# Ensure root directory is in the search path
current_dir = pathlib.Path(__file__).resolve().parent
project_root = current_dir.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from oaConfiguration.FileReaders.config_reader import Config
from oaLogging.Core.logger import set_log_directory
from oaOchestration.Core.path_initializer import initialize_paths, DATA_LOGS_DIR
from oaConfiguration.Methods.console_encoder import configure_console_encoding
from oaGuiSplashScreen.Methods.splash_screen import SplashScreen

# --- EXTRACTED CORE MODULES ---
from oaGuiManager.Core.ui_window import UIWindowManager
from oaGuiManager.Core.shutdown_coordinator import ShutdownCoordinator
from oaGuiManager.Core.bootstrap_sequence import AsyncBootstrapEngine
from oaGuiManager.Core.composition_root import UICompositionRoot

LOCAL_DEBUG = False

def main():
    """Orchestrates the startup, execution, and shutdown of the OPEN-AIR UI."""
    # 1. Environment Initialization
    initialize_paths()
    set_log_directory(DATA_LOGS_DIR, partition="UI")
    configure_console_encoding()
    app_constants = Config.get_instance()
    
    if LOCAL_DEBUG: logger.debug("🖥️🎨 [UI] Starting OpenAir UI Service...")

    # 2. Tkinter Environment Setup
    root = UIWindowManager.create_root_window()

    # 3. Composition Root (Orchestrates service creation)
    composition_root = UICompositionRoot(root, app_constants)
    shared_services = composition_root.build_services()

    # 4. Splash Screen Initiation
    splash = SplashScreen(root, app_constants.CURRENT_VERSION, app_constants.global_settings["debug_enabled"])

    # Reveal the main window after creation and before mainloop
    UIWindowManager.reveal_main_window(root, splash, app_constants.global_settings["debug_enabled"])

    # 5. Shutdown Coordinator
    shutdown_coordinator = ShutdownCoordinator(root, shared_services, LOCAL_DEBUG)
    shutdown_coordinator.attach_to_root()

    # 6. Resource Management
    def _periodic_gc():
        import gc; gc.collect()
        if not getattr(root, '_shutdown', False): root.after(30000, _periodic_gc)
    _periodic_gc()

    # 7. Bootstrap Engine (Consumes injected services)
    bootstrap_engine = AsyncBootstrapEngine(root, splash, shared_services, app_constants, shutdown_coordinator)
    threading.Thread(target=bootstrap_engine.run, daemon=True).start()
    
    if LOCAL_DEBUG: logger.debug("🖥️🎨 [UI] Entering Tkinter MainLoop.")
    root.mainloop()
    
    if LOCAL_DEBUG: logger.debug("🖥️🎨 [UI] MainLoop exited. Destroying root...")
    try:
        root.destroy()
    except Exception as e:
        logger.trace(f"Error during root.destroy(): {e}")
    
    sys.exit(0)

if __name__ == "__main__":
    main()
