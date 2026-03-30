# oaComOSC/Workers/osc_tx_client.py
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
