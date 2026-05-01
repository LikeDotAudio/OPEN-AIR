# Managers/open_air_ui.py
# Author: Anthony Peter Kuzub
# Version 20260330.1600.1
#
# Description: Orchestrates the startup, execution, and shutdown of the OPEN-AIR UI service.

import pathlib
import sys
import threading
import inspect

# Ensure root directory is in the search path
current_dir = pathlib.Path(__file__).resolve().parent
project_root = current_dir.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from oaConfigurationManager.FileReaders.config_reader import Config
from oaConfigurationManager.Methods.console_encoder import configure_console_encoding
from oaGui.Managers.bootstrap_sequence import AsyncBootstrapEngine
from oaGui.Managers.composition_root import UICompositionRoot
from oaGui.Managers.shutdown_coordinator import ShutdownCoordinator
from oaGui.Interface.ui_window import UIWindowManager
from oaGuiElements.Methods.splash_screen import SplashScreen
from oaLogging.Core.logger import set_log_directory
from oaLogging.Methods.matrix_gate import matrix_log
from oaOchestration.Core.path_initializer import DATA_LOGS_DIR, initialize_paths

from oaGui.Methods.ui_signal_handler import UISignalHandler
from oaGui.Methods.ui_resource_manager import UIResourceManager

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

        # 2. Setup Windows & Feedback
        root = UIWindowManager.create_root_window()
        splash = SplashScreen(root, app_constants.CURRENT_VERSION, app_constants.global_settings["debug_enabled"])
        splash.set_status("Composing Service Graph...")

        # 3. Service Composition
        composition_root = UICompositionRoot(root, app_constants)
        shared_services = composition_root.build_services()

        # 4. System Coordination
        shutdown_coordinator = ShutdownCoordinator(root, shared_services, True)
        shutdown_coordinator.attach_to_root()
        UISignalHandler.register_shutdown(shutdown_coordinator)
        UIResourceManager.start_periodic_gc(root)

        # 5. Bootstrap & Run
        bootstrap_engine = AsyncBootstrapEngine(root, splash, shared_services, app_constants, shutdown_coordinator)
        threading.Thread(target=bootstrap_engine.run, daemon=True).start()

        matrix_log("ui", "system", "main", "🖥️🎨 [UI] Entering Tkinter MainLoop.", "DEBUG")
        root.mainloop()

    except KeyboardInterrupt:
        matrix_log("ui", "system", "main", "🛑 Keyboard Interrupt. Initiating shutdown...", "WARNING")
        if shutdown_coordinator: shutdown_coordinator.shutdown()
        else: sys.exit(0)

    except Exception as e:
        matrix_log("ui", "system", "main", f"💥 Critical Startup Failure: {e}", "ERROR")
        if root: root.destroy()
        sys.exit(1)

    finally:
        if root:
            try: root.destroy()
            except Exception as e:
                matrix_log("UI", "GUI_MANAGER", inspect.currentframe().f_code.co_name, f"Error during root.destroy(): {e}", level="TRACE")
        sys.exit(0)

if __name__ == "__main__":
    main()
