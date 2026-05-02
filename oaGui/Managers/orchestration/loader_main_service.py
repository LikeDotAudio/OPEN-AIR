# Managers/loader_main_service.py
#
# Orchestrates the startup, execution, and shutdown of the OPEN-AIR UI service.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Professional services for customizing and tailoring this software to your 
# specific application can be negotiated. There is no charge to use, modify, 
# or fork this software.
#
# Build Log: https://like.audio/category/software/spectrum-scanner/
# Source Code: https://github.com/APKaudio/
# Feature Requests can be emailed to i @ like . audio
#
# Version 20260501.1005.1
#
# This file serves as the main entry point for the UI Partition. It coordinates 
# between high-level managers (Window, Composition, Shutdown) to provide a 
# unified, stable interface while maintaining strict separation from the 
# hardware-focused Core Partition.

import pathlib
import sys
import threading
import inspect

# Ensure root directory is in the search path for cross-module accessibility
current_dir = pathlib.Path(__file__).resolve().parent
project_root = current_dir.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from oaConfigurationManager.FileReaders.config_reader import Config
from oaConfigurationManager.Methods.console_encoder import configure_console_encoding
from oaGui.Managers.bootstrap.loader_bootstrap_engine import LoaderBootstrapEngine
from oaGui.Managers.orchestration.loader_service_composer import LoaderServiceComposer
from oaGui.Managers.lifecycle.loader_shutdown_service import LoaderShutdownService
from oaGui.Interface.viewport.tab_physical_window import TabWindowManager
from oaGuiElements.Methods.splash_screen import SplashScreen
from oaLogging.Core.logger import set_log_directory
from oaLogging.Methods.matrix_gate import matrix_log
from oaOchestration.Core.path_initializer import DATA_LOGS_DIR, initialize_paths

from oaGui.Methods.execution.loader_signal_handler import LoaderSignalHandler
from oaGui.Methods.discovery.ui_resource_manager import UIResourceManager

def main():
    """
    Main orchestration routine for the OPEN-AIR UI subsystem.
    
    This function manages the entire lifecycle of the UI service:
    1. Environment Initialization: Sets up paths, logging, and configuration.
    2. Window Creation: Initializes the Tkinter root and splash screen.
    3. Service Composition: Builds the dependency graph using the 
       Composition Root.
    4. System Coordination: Sets up shutdown handlers and resource management.
    5. Bootstrapping: Launches the asynchronous bootstrap engine and starts 
       the Tkinter mainloop.
    
    Inputs:
        None (Reads global configuration via oaConfigurationManager).
        
    Outputs:
        None (Exits with specific codes on success or failure).
        
    Side Effects:
        - Spawns background threads for bootstrapping and resource cleanup.
        - Modifies global system state (Signal handlers, Logging sinks).
        - Opens a graphical window.
        
    Error Handling:
        - Catches KeyboardInterrupt for graceful shutdown.
        - Catches global Exceptions to log critical failures and clean up 
          resources before exiting with status 1.
    """
    loader_shutdown_service = None
    root = None
    try:
        # 1. Environment Initialization
        initialize_paths()
        set_log_directory(DATA_LOGS_DIR, partition="UI")
        configure_console_encoding()
        app_constants = Config.get_instance()

        matrix_log("ui", "system", "main", "🖥️🎨 [UI] Starting OpenAir UI Service...", "DEBUG")

        # 2. Setup Windows & Visual Feedback
        root = TabWindowManager.create_root_window()
        splash = SplashScreen(root, app_constants.CURRENT_VERSION, app_constants.global_settings["debug_enabled"])
        splash.set_status("Composing Service Graph...")

        # 3. Service Composition (Dependency Injection)
        loader_service_composer = LoaderServiceComposer(root, app_constants)
        shared_services = loader_service_composer.build_services()

        # 4. System Coordination & Resource Management
        loader_shutdown_service = LoaderShutdownService(root, shared_services, True)
        loader_shutdown_service.attach_to_root()
        LoaderSignalHandler.register_shutdown(loader_shutdown_service)
        UIResourceManager.start_periodic_gc(root)

        # 5. Bootstrap & Run (Async startup to keep UI responsive)
        bootstrap_engine = LoaderBootstrapEngine(root, splash, shared_services, app_constants, loader_shutdown_service)
        threading.Thread(target=bootstrap_engine.run, daemon=True).start()

        matrix_log("ui", "system", "main", "🖥️🎨 [UI] Entering Tkinter MainLoop.", "DEBUG")
        root.mainloop()

    except KeyboardInterrupt:
        matrix_log("ui", "system", "main", "🛑 Keyboard Interrupt. Initiating shutdown...", "WARNING")
        if loader_shutdown_service: loader_shutdown_service.shutdown()
        else: sys.exit(0)

    except Exception as e:
        matrix_log("ui", "system", "main", f"💥 Critical Startup Failure: {e}", "ERROR")
        if root: root.destroy()
        sys.exit(1)

    finally:
        # Final cleanup pass to ensure process termination
        if root:
            try: root.destroy()
            except Exception as e:
                matrix_log("UI", "GUI_MANAGER", inspect.currentframe().f_code.co_name, f"Error during root.destroy(): {e}", level="TRACE")
        sys.exit(0)

if __name__ == "__main__":
    main()
