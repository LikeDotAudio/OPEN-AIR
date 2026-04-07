# standalone_runner.py
# Author: Anthony Peter Kuzub
# Description: Standalone runner for SMPTE 2138 Bridge and Monitor services.
# Version: 20260407.01

import os
import sys
import time
import signal
import pathlib

# Ensure project root is in sys.path
current_dir = pathlib.Path(__file__).resolve().parent
project_root = current_dir.parent.parent # OPEN-AIR is two levels up from standalone_runner.py
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from oaComProtocols.oaComMQTT.Managers.mqtt_connection import MqttConnectionManager
from oaComProtocols.oaComMQTT.Managers.mqtt_subscriber_router import MqttSubscriberRouter
from oaComProtocols.oaComSMPTE2138.Managers.smpte2138_bridge_manager import SMPTE2138BridgeManager
from oaComProtocols.oaComSMPTE2138.Managers.smpte2138_monitor_manager import SMPTE2138MonitorManager
from oaLogging.Core.logger import initialize_logging, set_log_directory
from oaOchestration.Core.path_initializer import initialize_paths, DATA_LOGS_DIR

def main():
    print("🚀 [ST2138] Starting Standalone SMPTE 2138 Service...")
    
    # 1. Environment Setup
    initialize_paths()
    set_log_directory(DATA_LOGS_DIR, partition="ST2138")
    
    # 2. Infrastructure
    mqtt_conn = MqttConnectionManager()
    sub_router = MqttSubscriberRouter()
    
    # 3. Managers
    bridge = SMPTE2138BridgeManager(mqtt_conn, sub_router)
    monitor = SMPTE2138MonitorManager(mqtt_conn, sub_router)
    
    # Enable monitor even without GUI observers if we want it "always online"
    # Although the bridge is the most important part for "online" presence.
    # We can add a dummy observer to start the monitor thread if needed.
    def dummy_observer(topic, data):
        pass
    monitor.add_observer(dummy_observer)

    # 4. Connect to MQTT
    print("📡 [ST2138] Connecting to MQTT Broker...")
    mqtt_conn.connect_to_broker(subscriber_router=sub_router)
    
    # 5. Keep alive
    def signal_handler(sig, frame):
        print("\n🛑 [ST2138] Stopping service...")
        bridge.stop()
        monitor.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print("✅ [ST2138] Service is active and online.")
    
    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()
