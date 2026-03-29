# Workers/osc_rx_server.py
# Author: Gemini Agent
# Version: 1.0.0
#
# Description: Dedicated OSC receiver using python-osc.

import threading
import time
from typing import Any

try:
    from pythonosc.dispatcher import Dispatcher
    from pythonosc.osc_server import BlockingOSCUDPServer
    HAS_OSC = True
except ImportError:
    HAS_OSC = False

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True
from loguru import logger
from oaConfiguration.FileReaders.config_reader import Config
app_constants = Config.get_instance()
osc_logger = logger.bind(category="OSC")

class OscRxServer:
    """
    Receives OSC messages and routes them to the state manager.
    """
    def __init__(self, host: str, port: int, state_callback: Any):
        self.host = host
        self.port = port
        self.state_callback = state_callback
        self.server = None
        self._thread = None
        self._stop_event = threading.Event()

    def _msg_handler(self, address, *args):
        """Dispatches incoming OSC messages to the state manager."""
        if LOCAL_DEBUG:
            osc_logger.debug(f"📥📡📥 [OSC] RX: {address} -> {args}")
        # Typically OSC values are single floats or ints
        val = args[0] if args else None
        self.state_callback(address, val)

    def start(self):
        """Starts the OSC server in a background thread."""
        if not HAS_OSC:
            osc_logger.error(f"❌🚫🛑 [OSC] RX Server: python-osc not installed. "
                             f"Please run 'Check Dependencies'.")
            return

        dispatcher = Dispatcher()
        dispatcher.map("/*", self._msg_handler)

        try:
            # ⚡ OPTIMIZATION: Allow immediate reuse of the port after shutdown
            # This prevents [Errno 98] Address already in use during rapid restarts.
            class ReusableOSCServer(BlockingOSCUDPServer):
                allow_reuse_address = True

            self.server = ReusableOSCServer((self.host, self.port), 
                                               dispatcher)
            self._thread = threading.Thread(target=self.server.serve_forever, 
                                            daemon=True)
            self._thread.start()
            if LOCAL_DEBUG:
                osc_logger.success(f"📡🆗✅ [OSC] RX Server listening on "
                                   f"{self.host}:{self.port}")
        except Exception as e:
            osc_logger.error(f"❌🚫🛑 [OSC] Failed to start RX Server: {e}")

    def stop(self):
        """Stops the OSC server."""
        if self.server:
            self.server.shutdown()
            if self._thread:
                self._thread.join(timeout=2.0)
            if LOCAL_DEBUG:
                osc_logger.debug("🛑📡👋 [OSC] RX Server stopped.")
