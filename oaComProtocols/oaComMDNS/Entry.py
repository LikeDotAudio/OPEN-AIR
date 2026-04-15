# oaComProtocols/oaComMDNS/Entry.py
# Author: Gemini (Collaborator)
# Version: 20260414.1010.1
#
# Description: Gatekeeper for the mDNS Communication Module.
# Orchestrates a standalone Zeroconf listener to publish mDNS data to MQTT.
# Refactored for centralized management by ComProtocolManager, but MQTT is self-contained.

import sys
import time
import signal
import os
import pathlib

current_dir = pathlib.Path(__file__).resolve().parent
project_root = current_dir.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from oaLogging.Methods.matrix_gate import matrix_log
# Core components are now managed externally, except for their own internal MQTT publisher
from oaComProtocols.oaComMDNS.Core.mdns_listener import MDNSListener

_listener = None
_publisher_instance = None

def start(rx_callback=None, tx_callback=None):
    """Initializes and starts the MDNS listener, using its own MQTT publisher."""
    global _listener, _publisher_instance
    if _listener is not None:
        return
    
    # Module manages its own MQTT publisher and connection
    from oaComProtocols.oaComMDNS.Core.mqtt_publisher import StandaloneMqttPublisher
    _publisher_instance = StandaloneMqttPublisher(client_id="MDNS_Standalone", tx_callback=tx_callback)
    _publisher_instance.connect()
    
    _listener = MDNSListener(_publisher_instance, rx_callback=rx_callback)
    _listener.start()
    matrix_log("comms", "mdns", "start", "🚀 [MDNS] Listener and self-contained MQTT publisher started.", "INFO")

def stop():
    """Stops the MDNS listener and disconnects its own MQTT publisher."""
    global _listener, _publisher_instance
    if _listener:
        _listener.stop()
        _listener = None
        matrix_log("comms", "mdns", "stop", "🛑 [MDNS] Listener stopped.", "INFO")
    if _publisher_instance:
        _publisher_instance.disconnect()
        _publisher_instance = None
        matrix_log("comms", "mdns", "stop", "🛑 [MDNS] MQTT publisher disconnected.", "INFO")

def status():
    """Returns the current operational status of the MDNS receiver."""
    return {"running": _listener is not None, "publisher_connected": _publisher_instance is not None and _publisher_instance.is_connected()}

# Standalone main() function is removed.
# def main(): ...

__all__ = ["start", "stop", "status"]
