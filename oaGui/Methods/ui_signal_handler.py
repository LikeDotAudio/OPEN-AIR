# Methods/ui_signal_handler.py
# Author: Anthony Peter Kuzub
# Version: 20260501.1000.1
#
# Description: System signal handling for the OPEN-AIR UI service.

import signal
from oaLogging.Methods.matrix_gate import matrix_log

class UISignalHandler:
    """System signal handling for the OPEN-AIR UI service."""
    @staticmethod
    def register_shutdown(shutdown_coordinator):
        """Registers a handler for SIGTERM to initiate a graceful shutdown."""
        def handle_sigterm(signum, frame):
            matrix_log("ui", "system", "sigterm", "🛑 SIGTERM received. Initiating shutdown...", "WARNING")
            shutdown_coordinator.shutdown()

        signal.signal(signal.SIGTERM, handle_sigterm)
