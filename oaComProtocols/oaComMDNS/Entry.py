# oaComProtocols/oaComMDNS/Entry.py
# Author: Gemini (Collaborator)
# Version: 20260414.1010.1
#
# Description: Gatekeeper for the mDNS Communication Module.
# Orchestrates a standalone Zeroconf listener to publish mDNS data to MQTT.

import sys
import time
import signal
import os
import pathlib

current_dir = pathlib.Path(__file__).resolve().parent
project_root = current_dir.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from oaComProtocols.oaComMDNS.Core.mqtt_publisher import StandaloneMqttPublisher
from oaComProtocols.oaComMDNS.Core.mdns_listener import MDNSListener

_listener = None
_publisher = None

def start(rx_callback=None, tx_callback=None):
    """Initializes and starts the MDNS listener and MQTT publisher."""
    global _listener, _publisher
    if _listener is not None:
        return
    _publisher = StandaloneMqttPublisher(client_id="MDNS_Standalone", tx_callback=tx_callback)
    _publisher.connect()
    
    _listener = MDNSListener(_publisher, rx_callback=rx_callback)
    _listener.start()

def stop():
    """Stops the MDNS listener and disconnects from MQTT."""
    global _listener, _publisher
    if _listener:
        _listener.stop()
        _listener = None
    if _publisher:
        _publisher.disconnect()
        _publisher = None

def status():
    """Returns the current operational status of the MDNS receiver."""
    return {"running": _listener is not None}

def main():
    """Standalone entry point for MDNS."""
    print("🚀 [MDNS] Starting Standalone MDNS Receiver with GUI...")
    
    try:
        import tkinter as tk
        from tkinter import ttk
        from oaComProtocols.oaComMDNS.Interface.dashboard_gui import ProtocolDashboard

        root = tk.Tk()
        root.title("OPEN-AIR | mDNS Discovery Hub")
        root.geometry("1100x800")
        root.configure(bg="#2b2b2b")
        
        gui = ProtocolDashboard(root, "mDNS")
        gui.pack(fill=tk.BOTH, expand=True)

        # Thread-safe callbacks to update the GUI
        def rx_cb(source, summary, details):
            root.after(0, gui.log_rx, source, summary, details)

        def tx_cb(topic, summary, details):
            root.after(0, gui.log_tx, topic, summary, details)
            
        start(rx_callback=rx_cb, tx_callback=tx_cb)

        def on_closing():
            print("🛑 [MDNS] Shutting down...")
            stop()
            root.destroy()
            sys.exit(0)

        root.protocol("WM_DELETE_WINDOW", on_closing)
        root.mainloop()

    except ImportError:
        print("⚠️ [MDNS] Tkinter not available. Falling back to headless mode.")
        start()
        def signal_handler(sig, frame):
            stop()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            stop()

if __name__ == "__main__":
    main()

__all__ = ["start", "stop", "status", "main"]