# oaComProtocols/oaComDNSSD/Entry.py
# Author: Gemini (Collaborator)
# Version: 20260414.1010.1
#
# Description: Gatekeeper for the DNSSD Communication Module.
# Orchestrates a standalone Zeroconf listener to publish DNSSD data to MQTT.
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
from oaComProtocols.oaComDNSSD.Core.mqtt_publisher import StandaloneMqttPublisher
from oaComProtocols.oaComDNSSD.Core.dnssd_listener import DNSSDListener

_listener = None
_publisher = None # Renamed back to _publisher for clarity as it's module-specific

def start(rx_callback=None, tx_callback=None):
    """Initializes and starts the DNSSD listener and its own MQTT publisher."""
    global _listener, _publisher
    if _listener is not None:
        return
    
    # Module manages its own MQTT publisher and connection
    _publisher = StandaloneMqttPublisher(client_id="DNSSD_Standalone", tx_callback=tx_callback)
    _publisher.connect()
    
    _listener = DNSSDListener(_publisher, rx_callback=rx_callback)
    _listener.start()
    matrix_log("comms", "dnssd", "start", "🚀 [DNSSD] Listener and self-contained MQTT publisher started.", "INFO")

def stop():
    """Stops the DNSSD listener and disconnects its own MQTT publisher."""
    global _listener, _publisher
    if _listener:
        _listener.stop()
        _listener = None
        matrix_log("comms", "dnssd", "stop", "🛑 [DNSSD] Listener stopped.", "INFO")
    if _publisher:
        _publisher.disconnect()
        _publisher = None
        matrix_log("comms", "dnssd", "stop", "🛑 [DNSSD] MQTT publisher disconnected.", "INFO")

def status():
    """Returns the current operational status of the DNSSD receiver."""
    return {"running": _listener is not None, "publisher_connected": _publisher is not None and _publisher.is_connected()}

# Standalone main() function is removed.
# def main(): ...

__all__ = ["start", "stop", "status"]
