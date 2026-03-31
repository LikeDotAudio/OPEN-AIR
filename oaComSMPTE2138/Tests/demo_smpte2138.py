# oaComSMPTE2138/Tests/demo_smpte2138.py
#
# A standalone demonstration of the SMPTE2138 Protocol Bridge.
# Simulates internal MQTT actions and observes the external st2138 tree.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Version 20260330.1600.1

import os
import sys
import time
from unittest.mock import MagicMock

# Ensure we can import the local modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from oaComSMPTE2138.Managers.smpte2138_bridge_manager import SMPTE2138BridgeManager
from oaComSMPTE2138.Managers.smpte2138_monitor_manager import SMPTE2138MonitorManager
from oaComSMPTE2138.Interface import param_pb2

class MockMqttMessage:
    def __init__(self, topic, payload):
        self.topic = topic
        self.payload = payload
    def get_json_payload(self):
        import orjson
        return orjson.loads(self.payload)

def run_demo():
    print("🚀 [DEMO] Starting oaComSMPTE2138 & ST 2138 Monitor Demonstration...")
    
    # 1. Mock the MQTT environment
    mock_mqtt = MagicMock()
    mock_router = MagicMock()
    
    # Capture publications
    published_messages = []
    
    # 2. Initialize the Monitor Manager
    monitor = SMPTE2138MonitorManager(mock_mqtt, mock_router)
    
    # Track monitor callbacks
    decoded_packets = []
    def monitor_callback(topic, data):
        decoded_packets.append((topic, data))
        if "oid" in data:
            print(f"🔗 [MONITOR] Decoded packet from {topic}: {data['oid']} = {data['value']}")
        
    SMPTE2138MonitorManager.register_callback(monitor_callback)

    def mock_publish(topic, payload, qos=0, retain=False):
        published_messages.append((topic, payload))
        print(f"📡 [OUTBOUND] Published binary payload to: {topic}")
        # Simulate the loopback to the monitor
        monitor._on_smpte2138_traffic(MockMqttMessage(topic, payload))
        
    mock_mqtt.publish = mock_publish
    mock_mqtt.get_client_instance.return_value = mock_mqtt
    
    # 3. Initialize the Bridge Manager
    bridge = SMPTE2138BridgeManager(mock_mqtt, mock_router)
    
    # 4. Simulate an internal "Action"
    test_topic = "oa/action/sig_gen/frequency"
    test_value = 440.0
    print(f"\n📥 [SIMULATION] Internal Action: {test_topic} -> {test_value}")
    
    # Manually trigger the callback
    bridge._on_internal_action(MockMqttMessage(test_topic, str(test_value)))
    
    # 5. Verify and Decode the Output
    if published_messages:
        # Filter for non-status messages for verification
        traffic = [m for m in published_messages if "st2138" in m[0] and "Bridge" not in m[0]]
        if traffic:
            topic, payload = traffic[0]
            print(f"\n🔍 [VERIFICATION] Outbound message count (traffic): {len(traffic)}")
            print(f"✅ [SUCCESS] Monitor decoded {len([p for p in decoded_packets if p[1].get('_msg_type') != 'HEARTBEAT'])} packet(s).")
        else:
            print("\n🔍 [VERIFICATION] Only status messages detected.")
    else:
        print("❌ [FAILURE] No outbound messages detected.")

if __name__ == "__main__":
    run_demo()
