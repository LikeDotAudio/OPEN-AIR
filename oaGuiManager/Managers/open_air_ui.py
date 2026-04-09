# Managers/open_air_ui.py
#
# Orchestrates the startup, execution, and shutdown of the OPEN-AIR UI service.
# Manages the Tkinter main loop and coordinates the bootstrap sequence.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Professional services for customizing and tailoring this software to your specific
# application can be negotiated. There is no charge to use, modify, or fork this software.
#
# Build Log: https://like.audio/category/software/spectrum-scanner/
# Source Code: https://github.com/APKaudio/
# Feature Requests can be emailed to i @ like . audio
#
# Version 20260330.1600.1

import sys
import pathlib
import threading
from loguru import logger

# Ensure root directory is in the search path
current_dir = pathlib.Path(__file__).resolve().parent
project_root = current_dir.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from oaConfigurationManager.FileReaders.config_reader import Config
from oaLogging.Core.logger import set_log_directory
from oaOchestration.Core.path_initializer import initialize_paths, DATA_LOGS_DIR
from oaConfigurationManager.Methods.console_encoder import configure_console_encoding
from oaGuiSplashScreen.Methods.splash_screen import SplashScreen
from oaLogging.Methods.matrix_gate import matrix_log
import inspect

# --- EXTRACTED CORE MODULES ---
from oaGuiManager.Core.ui_window import UIWindowManager
from oaGuiManager.Core.shutdown_coordinator import ShutdownCoordinator
from oaGuiManager.Core.bootstrap_sequence import AsyncBootstrapEngine
from oaGuiManager.Core.composition_root import UICompositionRoot

def main():
    """Orchestrates the startup, execution, and shutdown of the OPEN-AIR UI."""
    shutdown_coordinator = None
    root = None
    try:
        # 1. Environment Initialization
        initialize_paths()
        set_log_directory(DATA_LOGS_DIR, partition="UI")
        configure_console_encoding()
        app_constants = Config.get_instance()
        
        matrix_log("ui", "system", "main", "🖥️🎨 [UI] Starting OpenAir UI Service...", "DEBUG")

        # 2. Tkinter Environment Setup
        root = UIWindowManager.create_root_window()

        # 3. Splash Screen Initiation (IMMEDIATE)
        # Launch splash screen first to provide instant user feedback.
        splash = SplashScreen(root, app_constants.CURRENT_VERSION, app_constants.global_settings["debug_enabled"])
        splash.set_status("Composing Service Graph...")

        # 4. Composition Root (Orchestrates service creation)
        composition_root = UICompositionRoot(root, app_constants)
        shared_services = composition_root.build_services()

        # 5. Shutdown Coordinator
        shutdown_coordinator = ShutdownCoordinator(root, shared_services, True)
        shutdown_coordinator.attach_to_root()

        # ⚡ V3.1.28 TERMINATION: Handle SIGTERM (from supervisor) via ShutdownCoordinator
        import signal
        def handle_sigterm(signum, frame):
            matrix_log("ui", "system", "main", "🛑 SIGTERM received in UI partition. Initiating shutdown...", "WARNING")
            shutdown_coordinator.shutdown()
        
        signal.signal(signal.SIGTERM, handle_sigterm)

        # 6. Resource Management
        def _periodic_gc():
            import gc; gc.collect()
            if not getattr(root, '_shutdown', False): root.after(30000, _periodic_gc)
        _periodic_gc()

        # 7. Bootstrap Engine (Consumes injected services)
        bootstrap_engine = AsyncBootstrapEngine(root, splash, shared_services, app_constants, shutdown_coordinator)
        threading.Thread(target=bootstrap_engine.run, daemon=True).start()
        
        matrix_log("ui", "system", "main", "🖥️🎨 [UI] Entering Tkinter MainLoop.", "DEBUG")
        root.mainloop()
        
    except KeyboardInterrupt:
        matrix_log("ui", "system", "main", "🛑 Keyboard Interrupt detected in UI partition. Initiating shutdown...", "WARNING")
        if shutdown_coordinator:
            shutdown_coordinator.shutdown()
        else:
            sys.exit(0)
    
    matrix_log("ui", "system", "main", "🖥️🎨 [UI] MainLoop exited. Finalizing...", "DEBUG")
    if root:
        try:
            root.destroy()
        except Exception as e:
            matrix_log("UI", "GUI_MANAGER", inspect.currentframe().f_code.co_name, f"Error during root.destroy(): {e}", level="TRACE")
    
    sys.exit(0)

if __name__ == "__main__":
    main()
