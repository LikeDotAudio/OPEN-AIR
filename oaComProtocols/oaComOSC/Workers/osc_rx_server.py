# oaComProtocols.oaComOSC/Workers/osc_rx_server.py
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
    from oaosccore_rs import OscServer
    HAS_OSC_RS = True
except ImportError:
    HAS_OSC_RS = False

try:
    from pythonosc.dispatcher import Dispatcher
    from pythonosc.osc_server import BlockingOSCUDPServer
    HAS_OSC = True
except ImportError:
    HAS_OSC = False

# --- Standard Debug Logging Setup ---
from oaLogging.Methods.matrix_gate import is_debug_allowed
def _is_debug():
    return is_debug_allowed(system="comms", element="osc")

from oaLogging.Core.logger import get_logger
from oaConfigurationManager.FileReaders.config_reader import Config
app_constants = Config.get_instance()
osc_logger = get_logger("OSC")

class OscRxServer:
    """
    Receives OSC messages and routes them to the state manager.
    Leverages Pure Rust for high-frequency data ingestion if available.
    """
    def __init__(self, host: str, port: int, state_callback: Any):
        self.host = host
        self.port = port
        self.state_callback = state_callback
        self.server = None
        self._thread = None
        self._stop_event = threading.Event()
        self._use_rust = HAS_OSC_RS

    def _msg_handler(self, address, args):
        """Dispatches incoming OSC messages to the state manager."""
        if _is_debug():
            osc_logger.debug(f"📥📡📥 [OSC-RS] RX: {address} -> {args}")
        # Typically OSC values are single floats or ints
        val = args[0] if args else None
        self.state_callback(address, val)

    def _legacy_msg_handler(self, address, *args):
        """Legacy handler for python-osc."""
        if _is_debug():
            osc_logger.debug(f"📥📡📥 [OSC-PY] RX: {address} -> {args}")
        val = args[0] if args else None
        self.state_callback(address, val)

    def start(self):
        """Starts the OSC server."""
        if self._use_rust:
            self._start_rust()
        else:
            self._start_legacy()

    def _start_rust(self):
        """Starts the Pure Rust OSC server."""
        try:
            self.server = OscServer()
            self.server.start(self.host, self.port, self._msg_handler)
            if _is_debug():
                osc_logger.success(f"📡🆗✅ [OSC] Pure Rust RX Server listening on "
                                   f"{self.host}:{self.port}")
        except Exception as e:
            osc_logger.error(f"❌🚫🛑 [OSC] Failed to start Rust RX Server: {e}. Falling back to legacy.")
            self._use_rust = False
            self._start_legacy()

    def _start_legacy(self):
        """Starts the legacy python-osc server in a background thread."""
        if not HAS_OSC:
            osc_logger.error(f"❌🚫🛑 [OSC] RX Server: python-osc not installed. "
                             f"Please run 'Check Dependencies'.")
            return

        dispatcher = Dispatcher()
        dispatcher.map("/*", self._legacy_msg_handler)

        try:
            class ReusableOSCServer(BlockingOSCUDPServer):
                allow_reuse_address = True

            self.server = ReusableOSCServer((self.host, self.port), 
                                               dispatcher)
            self._thread = threading.Thread(target=self.server.serve_forever, 
                                            daemon=True)
            self._thread.start()
            if _is_debug():
                osc_logger.success(f"📡🆗✅ [OSC] Legacy RX Server listening on "
                                   f"{self.host}:{self.port}")
        except Exception as e:
            osc_logger.error(f"❌🚫🛑 [OSC] Failed to start Legacy RX Server: {e}")

    def stop(self):
        """Stops the OSC server."""
        if self.server:
            if self._use_rust:
                self.server.stop()
            else:
                self.server.shutdown()
                if self._thread:
                    self._thread.join(timeout=2.0)
            if _is_debug():
                osc_logger.debug("🛑📡👋 [OSC] RX Server stopped.")
