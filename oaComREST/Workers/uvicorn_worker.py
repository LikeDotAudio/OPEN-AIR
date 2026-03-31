import inspect
from oaLogging.Methods.matrix_gate import matrix_log
# oaComREST/Workers/uvicorn_worker.py
# Author: Anthony Peter Kuzub
# Version: 20260328.1200.1
#
# Description: Background thread for running the Uvicorn ASGI server.

import threading
import sys
try:
    import uvicorn
    UVICORN_AVAILABLE = True
except ImportError:
    UVICORN_AVAILABLE = False

from loguru import logger
from ..Constants.rest_constants import LOCAL_DEBUG

class UvicornWorker(threading.Thread):
    """
    A dedicated thread to run the FastAPI application via Uvicorn.
    """
    def __init__(self, app, host="0.0.0.0", port=8000):
        """
        Initializes the Uvicorn worker thread.
        
        Inputs:
            app (FastAPI): The FastAPI application instance.
            host (str): The host interface to bind to.
            port (int): The port to listen on.
        """
        super().__init__(name="UvicornWorker", daemon=True)
        self.app = app
        self.host = host
        self.port = port
        self.server = None

    def run(self):
        """Executes the Uvicorn server loop."""
        if not UVICORN_AVAILABLE:
            logger.error("📡⚙️🛑 [REST] Uvicorn not found. Worker thread exiting.")
            return

        if LOCAL_DEBUG:
            matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"📡⚙️🚀 [REST] Starting Uvicorn on {self.host}:{self.port}", "DEBUG")
        
        config = uvicorn.Config(
            app=self.app, 
            host=self.host, 
            port=self.port, 
            log_level="info" if LOCAL_DEBUG else "error",
            loop="asyncio"
        )
        self.server = uvicorn.Server(config)
        try:
            self.server.run()
        except (OSError, SystemExit) as e:
            logger.error(f"📡⚙️❌ [REST] Uvicorn failed to start on {self.host}:{self.port}. "
                         f"The port may already be in use. Error: {e}")
            # Ensure the server knows it shouldn't be running
            self.server.should_exit = True

    def stop(self):
        """Signals the Uvicorn server to shut down."""
        if self.server:
            if LOCAL_DEBUG:
                matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "📡⚙️🛑 [REST] Stopping Uvicorn server...", "DEBUG")
            self.server.should_exit = True
