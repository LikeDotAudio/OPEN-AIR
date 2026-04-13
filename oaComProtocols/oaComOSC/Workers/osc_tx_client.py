# oaComProtocols.oaComOSC/Workers/osc_tx_client.py
#
# Dedicated UDP client for transmitting OSC messages to remote surfaces.
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
# Version 20260329.1115.1

from typing import Any

try:
    from oaRustCore.oa_osc_core_rs import OscClient as RustOscClient
    HAS_OSC_RS = True
except ImportError:
    HAS_OSC_RS = False

try:
    from pythonosc.udp_client import SimpleUDPClient
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

class OscTxClient:
    """
    Transmits OSC messages to target devices.
    Leverages Pure Rust for high-throughput transmission if available.
    """
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.client = None
        self._use_rust = HAS_OSC_RS

    def start(self):
        """Initializes the OSC client."""
        if self._use_rust:
            self._start_rust()
        else:
            self._start_legacy()

    def _start_rust(self):
        try:
            self.client = RustOscClient(self.host, self.port)
            self.client.start()
            if _is_debug():
                osc_logger.success(f"📤📡✅ [OSC] Pure Rust TX Client ready: "
                                   f"{self.host}:{self.port}")
        except Exception as e:
            osc_logger.error(f"❌🚫🛑 [OSC] Failed to start Rust TX Client: {e}. Falling back to legacy.")
            self._use_rust = False
            self._start_legacy()

    def _start_legacy(self):
        if not HAS_OSC:
            osc_logger.error(f"❌🚫🛑 [OSC] TX Client: python-osc not installed. "
                             f"Please run 'Check Dependencies'.")
            return

        try:
            self.client = SimpleUDPClient(self.host, self.port)
            if _is_debug():
                osc_logger.success(f"📤📡✅ [OSC] Legacy TX Client ready: "
                                   f"{self.host}:{self.port}")
        except Exception as e:
            osc_logger.error(f"❌🚫🛑 [OSC] Failed to start Legacy TX Client: {e}")

    def send_message(self, address: str, value: Any):
        """Sends an OSC message."""
        if self.client:
            try:
                self.client.send_message(address, value)
                if _is_debug():
                    osc_logger.debug(f"📤📡📤 [OSC] TX: {address} -> {value}")
            except Exception as e:
                osc_logger.error(f"❌🚫🛑 [OSC] TX Error: {e}")

    def stop(self):
        """Stops the OSC client."""
        if self.client:
            if self._use_rust:
                self.client.stop()
            self.client = None
        if _is_debug():
            osc_logger.debug("🛑📡👋 [OSC] TX Client stopped.")
