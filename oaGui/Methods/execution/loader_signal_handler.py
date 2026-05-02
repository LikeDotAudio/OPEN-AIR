# Methods/loader_signal_handler.py
# Author: Anthony Peter Kuzub
# Version: 20260501.1000.1
#
# Description: System signal handling for the OPEN-AIR UI service.

import signal
from oaLogging.Methods.matrix_gate import matrix_log

class LoaderSignalHandler:
    """System signal handling for the OPEN-AIR UI service."""
    @staticmethod
    def register_shutdown(loader_shutdown_service):
        """Registers a handler for SIGTERM to initiate a graceful shutdown."""
        def handle_sigterm(signum, frame):
            matrix_log("ui", "system", "sigterm", "🛑 SIGTERM received. Initiating shutdown...", "WARNING")
            loader_shutdown_service.shutdown()

        signal.signal(signal.SIGTERM, handle_sigterm)
