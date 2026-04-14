
import time
import threading
import sys
import os
import pathlib
from unittest.mock import MagicMock

# Ensure project root is in path
project_root = str(pathlib.Path(__file__).resolve().parent.parent.parent)
sys.path.insert(0, project_root)

from oaComBroker.Core.protocol_router.manager import ProtocolRouter
from oaComProtocols.oaComSNMP.Managers.snmp_manager import SNMPManager, BridgeContext, SNMPBridge

import oaComBroker.Core.protocol_router.dispatch as dispatch_mod
original_dispatch_mqtt = dispatch_mod._dispatch_mqtt

def patched_dispatch_mqtt(mqtt_manager, topic, message, val_str):
    print(f"DEBUG: Entering _dispatch_mqtt for topic: {topic}")
    return original_dispatch_mqtt(mqtt_manager, topic, message, val_str)

dispatch_mod._dispatch_mqtt = patched_dispatch_mqtt

def test_router_dispatch():
    router = ProtocolRouter.get_instance()
    
    # 1. Setup Mock MQTT Manager
    mock_mqtt = MagicMock()
    router.set_mqtt_manager(mock_mqtt)
    
    # 2. Enable Ingest and Egress
    router.set_routing_state("SNMP", "MQTT", True)
    
    # 3. Start Router
    router.start()
    time.sleep(1)
    
    # 4. Create and Start SNMP Bridge
    context = BridgeContext(mqtt_connection_manager=mock_mqtt, subscriber_router=MagicMock())
    manager = SNMPBridge(context)
    manager.start()
    time.sleep(1)
    
    print(f"Router Egress Enabled for MQTT: {router.egress_enabled.get('MQTT')}")
    print(f"Router Ingest Enabled for SNMP: {router.ingest_enabled.get('SNMP')}")
    print(f"Routing Matrix (SNMP -> MQTT): {router.routing_matrix.get('SNMP', {}).get('MQTT')}")
    print(f"Routing Matrix (MQTT -> MQTT): {router.routing_matrix.get('MQTT', {}).get('MQTT')}")
    
    # 5. Trigger a notification (Simulate TX_DUMP change)
    # This calls ProtocolRouter.ingest("SNMP", "OPEN-AIR/System/Monitor/SNMP/Activity", ...)
    print(f"[{time.time():.3f}] Triggering SNMP notification...")
    manager._notify_monitor("TX_DUMP", ".1.3.6.1.4.1.65300.1.1", "test_value", "OPEN-AIR/Real/Topic")
    
    # Wait for dispatch
    print(f"[{time.time():.3f}] Waiting for dispatch...")
    time.sleep(5)
    
    print(f"MQTT Publish Call Count: {mock_mqtt.publish.call_count}")
    for i, call in enumerate(mock_mqtt.publish.call_args_list):
        topic = call[0][0] if len(call[0]) > 0 else call[1].get('topic')
        print(f"  Call {i+1} Topic: {topic}")
        if "Activity" in str(topic):
            print("  ✅ SUCCESS: Activity topic found in MQTT publish calls.")
            break
    else:
        print("  ❌ FAILURE: Activity topic NOT found in MQTT publish calls.")

    manager.stop()
    router.stop()

if __name__ == "__main__":
    test_router_dispatch()
