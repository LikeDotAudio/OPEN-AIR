# Core/shutdown_coordinator.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import sys
from oaLogging.Methods.matrix_gate import matrix_log
import inspect
import threading
from loguru import logger

class ShutdownCoordinator:
    """Manages the clean, sequential shutdown of all background services."""

    def __init__(self, root, shared_instances, debug_enabled=True):
        self.root = root
        self.shared_instances = shared_instances
        self.debug_enabled = debug_enabled
        self._shutdown_in_progress = False

    def on_closing(self):
        """Gracefully terminates all UI and Communication sub-processes."""
        if self._shutdown_in_progress:
            return
        self._shutdown_in_progress = True
        
        matrix_log("UI", "GUI_MANAGER", inspect.currentframe().f_code.co_name, "🖥️🎨 [UI] Initiating shutdown...", level="DEBUG")
        self.root._shutdown = True
        
        # ⚡ THREADED SHUTDOWN: Run manager stops in a separate thread to prevent UI hang
        def _stop_managers():
            for name, instance in self.shared_instances.items():
                if instance:
                    try:
                        matrix_log("UI", "GUI_MANAGER", inspect.currentframe().f_code.co_name, f"🛑 Stopping manager: {name}", level="DEBUG")
                        if hasattr(instance, "stop"): instance.stop()
                        elif hasattr(instance, "shutdown"): instance.shutdown()
                        elif hasattr(instance, "disconnect"): instance.disconnect()
                    except Exception as e:
                        logger.warning(f"⚠️ Error shutting down {name}: {e}")
            
            # After managers are signaled to stop, quit the mainloop
            matrix_log("UI", "GUI_MANAGER", inspect.currentframe().f_code.co_name, "🖥️🎨 [UI] Managers signaled to stop. Quitting mainloop...", level="DEBUG")
            self.root.after(0, self.root.quit)

        threading.Thread(target=_stop_managers, daemon=True).start()

    def attach_to_root(self):
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
