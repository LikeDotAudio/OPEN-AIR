# oaComProtocols/oaComSMPTE2138/standalone_runner.py
# Author: Anthony Peter Kuzub
# Description: Standalone runner for SMPTE 2138 Bridge and Monitor services with GUI.
# Version: 20260412.01

import os
import sys
import time
import signal
import pathlib
import tkinter as tk

# Ensure project root is in sys.path
current_dir = pathlib.Path(__file__).resolve().parent
project_root = current_dir.parent.parent # OPEN-AIR is two levels up from standalone_runner.py
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from oaComProtocols.oaComSMPTE2138.Entry import run_tests
from oaComProtocols.oaComMQTT.Managers.mqtt_connection import MqttConnectionManager
from oaComProtocols.oaComMQTT.Managers.mqtt_subscriber_router import MqttSubscriberRouter
from oaComProtocols.oaComSMPTE2138.Managers.smpte2138_bridge_manager import SMPTE2138BridgeManager
from oaComProtocols.oaComSMPTE2138.Managers.smpte2138_monitor_manager import SMPTE2138MonitorManager
from oaComProtocols.oaComSMPTE2138.Interface.smpte2138_monitor import SMPTE2138MonitorImplementation
from oaLogging.Core.logger import initialize_logging, set_log_directory
from oaOchestration.Core.path_initializer import initialize_paths, DATA_LOGS_DIR

def main():
    # 1. Run Tests
    print("🔍 [ST2138] Running tests before launching service...")
    # We need to be in the project root for tests to run correctly as implemented in Entry.py
    os.chdir(project_root)
    run_tests()
    
    print("\n🚀 [ST2138] Starting Standalone SMPTE 2138 Service...")
    
    # 2. Environment Setup
    initialize_paths()
    set_log_directory(DATA_LOGS_DIR, partition="ST2138")
    
    # 3. Infrastructure
    mqtt_conn = MqttConnectionManager()
    sub_router = MqttSubscriberRouter()
    
    # 4. Managers
    bridge = SMPTE2138BridgeManager(mqtt_conn, sub_router)
    monitor_manager = SMPTE2138MonitorManager(mqtt_conn, sub_router)
    
    # 5. Connect to MQTT
    print("📡 [ST2138] Connecting to MQTT Broker...")
    try:
        mqtt_conn.connect_to_broker(subscriber_router=sub_router)
    except Exception as e:
        print(f"❌ [ST2138] Failed to connect to MQTT: {e}")
        # Continue anyway to show the GUI, though it might be offline

    # 6. Launch GUI
    print("🖥️ [ST2138] Launching Monitor GUI...")
    root = tk.Tk()
    root.title("OPEN-AIR: SMPTE ST 2138 Monitor")
    root.geometry("1000x700")
    
    # The monitor implementation expects a parent widget
    app = SMPTE2138MonitorImplementation(root)
    app.pack(fill=tk.BOTH, expand=True)
    
    # Link monitor_manager to the GUI via the event bus or direct callbacks if needed
    # smpte2138_monitor.py uses event_bus.subscribe("SMPTE2138_TRAFFIC", ...)
    # monitor_manager needs to publish to that event bus.
    
    def on_closing():
        print("\n🛑 [ST2138] Stopping service...")
        bridge.stop()
        monitor_manager.stop()
        root.destroy()
        sys.exit(0)

    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Handle signals
    def signal_handler(sig, frame):
        root.after(0, on_closing)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print("✅ [ST2138] Service is active and online.")
    root.mainloop()

if __name__ == "__main__":
    main()
