# oaComProtocols/oaComSAP/Entry.py
# Author: Gemini (Collaborator)
# Version: 20260414.1010.1
#
# Description: Gatekeeper for the SAP Communication Module.
# Orchestrates a standalone SAP multicast receiver to publish discovered streams to MQTT.
# Refactored for centralized management by ComProtocolManager.

import sys
import time
import signal
import os
import pathlib

current_dir = pathlib.Path(__file__).resolve().parent
project_root = current_dir.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Core components are now managed externally
from oaLogging.Methods.matrix_gate import matrix_log
from oaComProtocols.oaComSAP.Core.sap_listener import SAPListener

_listener = None
_publisher_instance = None

def start(mqtt_publisher=None, rx_callback=None):
    """Initializes and starts the SAP listener, using a provided MQTT publisher."""
    global _listener, _publisher_instance
    if _listener is not None:
        return
    
    # Use provided or handle missing publisher
    _publisher_instance = mqtt_publisher
    if _publisher_instance is None:
        # matrix_log("comms", "sap", "start", "⚠️ No MQTT publisher provided. SAP listener will not bridge events.", "WARNING")
        pass
    
    _listener = SAPListener(_publisher_instance, rx_callback=rx_callback)
    _listener.start()
    matrix_log("comms", "sap", "start", "🚀 [SAP] Listener started.", "INFO")

def stop():
    """Stops the SAP listener. MQTT publisher disconnect handled externally."""
    global _listener, _publisher_instance
    if _listener:
        _listener.stop()
        _listener = None
        matrix_log("comms", "sap", "stop", "🛑 [SAP] Listener stopped.", "INFO")
    # MQTT publisher disconnect handled by manager.

def status():
    """Returns the current operational status of the SAP receiver."""
    return {"running": _listener is not None}

# Standalone main() function is removed.
# def main(): ...

__all__ = ["start", "stop", "status"]
