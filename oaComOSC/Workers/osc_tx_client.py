# Workers/osc_tx_client.py
# Author: Gemini Agent
# Version: 1.0.0
#
# Description: Dedicated OSC transmitter using python-osc.

from typing import Any

try:
    from pythonosc.udp_client import SimpleUDPClient
    HAS_OSC = True
except ImportError:
    HAS_OSC = False

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = False
from loguru import logger
from oaConfiguration.FileReaders.config_reader import Config
app_constants = Config.get_instance()
osc_logger = logger.bind(category="OSC")

class OscTxClient:
    """
    Transmits OSC messages to target devices.
    """
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.client = None

    def start(self):
        """Initializes the OSC client."""
        if not HAS_OSC:
            osc_logger.error(f"❌🚫🛑 [OSC] TX Client: python-osc not installed. "
                             f"Please run 'Check Dependencies'.")
            return

        try:
            self.client = SimpleUDPClient(self.host, self.port)
            if LOCAL_DEBUG:
                osc_logger.success(f"📤📡✅ [OSC] TX Client ready: "
                                   f"{self.host}:{self.port}")
        except Exception as e:
            osc_logger.error(f"❌🚫🛑 [OSC] Failed to start TX Client: {e}")

    def send_message(self, address: str, value: Any):
        """Sends an OSC message."""
        if self.client:
            try:
                self.client.send_message(address, value)
                if LOCAL_DEBUG:
                    osc_logger.debug(f"📤📡📤 [OSC] TX: {address} -> {value}")
            except Exception as e:
                osc_logger.error(f"❌🚫🛑 [OSC] TX Error: {e}")

    def stop(self):
        """Stops the OSC client."""
        self.client = None
        if LOCAL_DEBUG:
            osc_logger.debug("🛑📡👋 [OSC] TX Client stopped.")
