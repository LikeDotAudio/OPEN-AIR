import sys

import inspect
from oaLogging.Methods.matrix_gate import matrix_log
# oaComREST/Workers/uvicorn_worker.py
# Author: Anthony Peter Kuzub
# Version: 20260328.1200.1
#
# Description: Background thread for running the Uvicorn ASGI server.

import threading
import time
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
        """Executes the Uvicorn server loop with retry logic for port collisions."""
        if not UVICORN_AVAILABLE:
            logger.error("📡⚙️🛑 [REST] Uvicorn not found. Worker thread exiting.")
            return

        max_retries = 3
        retry_delay = 2.0
        current_port = self.port

        for attempt in range(max_retries):
            if LOCAL_DEBUG:
                matrix_log("comms", "rest", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"📡⚙️🚀 [REST] Starting Uvicorn on {self.host}:{current_port} (Attempt {attempt + 1})", "DEBUG")
            
            config = uvicorn.Config(
                app=self.app, 
                host=self.host, 
                port=current_port, 
                log_level="info" if LOCAL_DEBUG else "error",
                loop="asyncio"
            )
            self.server = uvicorn.Server(config)
            
            try:
                # server.run() is blocking
                self.server.run()
                break # Success!
            except (OSError, SystemExit) as e:
                # Check for "Address already in use" (Errno 98)
                if isinstance(e, OSError) and e.errno == 98:
                    logger.warning(f"📡⚙️⚠️ [REST] Port {current_port} in use. Retrying with incremented port...")
                    current_port += 1
                    time.sleep(retry_delay)
                    continue
                
                logger.error(f"📡⚙️❌ [REST] Uvicorn failed to start on {self.host}:{current_port}. Error: {e}")
                if self.server:
                    self.server.should_exit = True
                break
            except Exception as e:
                logger.error(f"📡⚙️❌ [REST] Unexpected Uvicorn error: {e}")
                break

    def stop(self):
        """Signals the Uvicorn server to shut down."""
        if self.server:
            if LOCAL_DEBUG:
                matrix_log("comms", "rest", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "📡⚙️🛑 [REST] Stopping Uvicorn server...", "DEBUG")
            self.server.should_exit = True