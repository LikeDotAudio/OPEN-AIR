# Core/shutdown_coordinator.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import inspect
import sys
import threading

from loguru import logger

from oaLogging.Methods.matrix_gate import matrix_log


class ShutdownCoordinator:
    """Manages the clean, sequential shutdown of all background services."""

    def __init__(self, root, shared_instances, debug_enabled=True):
        self.root = root
        self.shared_instances = shared_instances
        self.debug_enabled = debug_enabled
        self._shutdown_in_progress = False

    def _stop_all_managers(self):
        """Internal helper to iterate and stop all shared manager instances."""
        for name, instance in self.shared_instances.items():
            if instance:
                try:
                    matrix_log("UI", "GUI_MANAGER", inspect.currentframe().f_code.co_name, f"🛑 Stopping manager: {name}", level="DEBUG")
                    if hasattr(instance, "stop"): instance.stop()
                    elif hasattr(instance, "shutdown"): instance.shutdown()
                    elif hasattr(instance, "disconnect"): instance.disconnect()
                except Exception as e:
                    logger.warning(f"⚠️ Error shutting down {name}: {e}")

        # --- FINAL LOGGING FLUSH ---
        from oaLogging.Core.logger import shutdown_logging
        shutdown_logging()

    def on_closing(self, run_async=True):
        """Gracefully terminates all UI and Communication sub-processes via a thread."""
        if self._shutdown_in_progress:
            return

        # ⚡ V3.1.26 PERSISTENCE: Save window position and size before closing
        from .ui_window import UIWindowManager
        UIWindowManager.save_window_geometry(self.root)

        self._shutdown_in_progress = True

        # ⚡ USER INTENT: Log clearly that the exit was requested by the user
        root_name = getattr(self.root, 'winfo_name', lambda: str(self.root))()
        matrix_log("UI", "GUI_MANAGER", inspect.currentframe().f_code.co_name, f"👋 [EXIT] User is requesting to exit application (Root: {root_name}).", level="INFO")

        # ⚡ DEBUG: Identify who called on_closing
        if self.debug_enabled:
            stack = inspect.stack()
            caller_info = "\n".join([f"  - {s.filename}:{s.lineno} in {s.function}" for s in stack[1:5]])
            matrix_log("UI", "GUI_MANAGER", inspect.currentframe().f_code.co_name, f"🖥️🎨 [UI] Initiating shutdown... Caller stack:\n{caller_info}", level="DEBUG")

        self.root._shutdown = True

        # ⚡ THREADED SHUTDOWN: Run manager stops in a separate thread to prevent UI hang
        def _threaded_shutdown():
            self._stop_all_managers()
            # After managers are signaled to stop, quit the mainloop
            matrix_log("UI", "GUI_MANAGER", inspect.currentframe().f_code.co_name, "🖥️🎨 [UI] Managers signaled to stop. Finalizing logout...", level="DEBUG")
            self.root.after(0, self.root.quit)

        if run_async:
            threading.Thread(target=_threaded_shutdown, daemon=True).start()
        else:
            _threaded_shutdown()

    def shutdown(self):
        """Synchronous shutdown for non-GUI-event-driven termination (e.g., KeyboardInterrupt)."""
        if self._shutdown_in_progress:
            return
        self._shutdown_in_progress = True

        matrix_log("UI", "GUI_MANAGER", inspect.currentframe().f_code.co_name, "🛑 [EXIT] Synchronous shutdown triggered.", level="INFO")
        self._stop_all_managers()
        matrix_log("UI", "GUI_MANAGER", inspect.currentframe().f_code.co_name, "🖥️🎨 [UI] Shutdown complete. Quitting mainloop.", level="DEBUG")

        try:
            self.root.after(0, self.root.quit)
        except Exception:
            # Fallback if root is already dead or mainloop not running
            sys.exit(0)

    def attach_to_root(self):
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
