# standalone_runner.py
# Author: Anthony Peter Kuzub
# Description: Standalone runner for the REST Hub service.
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
from oaStateCache.Core.state_cache import StateRegistry
from oaComBroker.Core.protocol_router.manager import ProtocolRouter
from oaComProtocols.oaComREST.Managers.rest_manager import RESTManager

from oaLogging.Core.logger import initialize_logging, set_log_directory
from oaOchestration.Core.path_initializer import initialize_paths, DATA_LOGS_DIR

def main():
    print("🚀 [REST-HUB] Starting Standalone REST Hub Service...")
    
    # 1. Environment Setup
    initialize_paths()
    set_log_directory(DATA_LOGS_DIR, partition="REST-HUB")
    
    # 2. Infrastructure
    mqtt_conn = MqttConnectionManager()
    sub_router = MqttSubscriberRouter()
    
    # 3. State & Routing
    state_cache = StateRegistry(mqtt_conn)
    state_cache.subscriber_router = sub_router
    
    protocol_router = ProtocolRouter.get_instance()
    protocol_router.set_mqtt_manager(mqtt_conn)
    protocol_router.set_state_cache(state_cache)
    
    # 4. REST Manager
    rest_manager = RESTManager(state_cache, protocol_router)
    
    # 5. Wildcard Subscription (Anything and Everything)
    # The user wants to subscribe to "#" but NOT REST topics.
    def filtered_mqtt_handler(client, userdata, msg):
        topic = msg.topic
        # ⚡ EXCLUSION: Skip REST-specific control and status topics to avoid loops or noise
        if "REST" in topic.upper():
            return
            
        # Standard state ingestion for everything else
        state_cache.handle_incoming_mqtt(client, userdata, msg)

    # 6. Connect to MQTT
    print("📡 [REST-HUB] Connecting to MQTT Broker and subscribing to ALL (#)...")
    mqtt_conn.connect_to_broker(
        on_message_callback=filtered_mqtt_handler, 
        subscriber_router=sub_router
    )
    
    # Explicitly subscribe to the wildcard for "anything and everything"
    mqtt_conn.subscribe("#")
    
    # 7. Start REST Service
    rest_manager.start()

    # 8. Keep alive
    def signal_handler(sig, frame):
        print("\n🛑 [REST-HUB] Stopping service...")
        rest_manager.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print("✅ [REST-HUB] Service is active and online.")
    
    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()
