# oaComOSC/Workers/osc_rx_server.py
#
# High-performance UDP server for receiving OSC bundles.
#
# Author: Anthony Peter Kuzub (Contributor to this project)
# Blog: www.Like.audio
#
# Professional services for customizing and tailoring this software to your specific
# application can be negotiated. There is no charge to use, modify, or fork this software.
#
# Build Log: https://like.audio/category/software/spectrum-scanner/
# Source Code: https://github.com/APKaudio/
# Feature Requests can be emailed to i @ like . audio
#
# Version 20260329.1110.1

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
LOCAL_DEBUG = False
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
