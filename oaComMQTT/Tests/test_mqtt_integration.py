# oaComMQTT/Tests/test_mqtt_integration.py
# Author: Anthony Peter Kuzub
# Version: 20260328.0.1
#
# Description: Integration test to publish, read, and clear MQTT messages.

import unittest
import time
import socket
import paho.mqtt.client as mqtt
from unittest.mock import MagicMock
import os
import sys

# Ensure project root is in path for MQTTSweeper
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from oaTests.Workers.CleanupApps.ClearMQTT import MQTTSweeper

def is_mqtt_broker_reachable(host="localhost", port=1883):
    """Check if the MQTT broker is reachable."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False

@unittest.skipUnless(is_mqtt_broker_reachable(), "Local MQTT broker (Mosquitto) is not reachable.")
class TestMQTTIntegration(unittest.TestCase):
    """
    Integration tests for MQTT messaging and cleanup.
    Requires a running Mosquitto broker on localhost:1883.
    """

    def setUp(self):
        self.host = "localhost"
        self.port = 1883
        self.test_topic_root = "OPEN-AIR/INTEGRATION-TEST"
        self.client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
        self.received_messages = []

    def on_message(self, client, userdata, msg):
        self.received_messages.append((msg.topic, msg.payload.decode()))

    def test_publish_subscribe_clear(self):
        """
        Flow: 
        1. Subscribe to test topic.
        2. Publish test messages.
        3. Verify messages are received.
        4. Use MQTTSweeper to clear the topics.
        5. Verify topics are cleared.
        """
        # 1. Connect and Subscribe
        self.client.on_message = self.on_message
        self.client.connect(self.host, self.port)
        self.client.subscribe(f"{self.test_topic_root}/#")
        self.client.loop_start()

        # 2. Publish
        test_payloads = {
            f"{self.test_topic_root}/sensor1": "value1",
            f"{self.test_topic_root}/sensor2": "value2"
        }
        for topic, payload in test_payloads.items():
            self.client.publish(topic, payload, retain=True)

        # 3. Wait and Verify
        timeout = time.time() + 2
        while len(self.received_messages) < 2 and time.time() < timeout:
            time.sleep(0.1)

        self.client.loop_stop()
        self.client.disconnect()

        self.assertEqual(len(self.received_messages), 2, "Should have received 2 test messages.")
        received_dict = dict(self.received_messages)
        for topic, payload in test_payloads.items():
            self.assertIn(topic, received_dict)
            self.assertEqual(received_dict[topic], payload)

        # 4. Clear the topics using MQTTSweeper
        sweeper = MQTTSweeper(self.host, self.port, self.test_topic_root)
        sweeper.sweep()

        # 5. Verify they are gone (by trying to read again)
        # Retained messages should be gone after sweep()
        self.received_messages = []
        self.client.connect(self.host, self.port)
        self.client.subscribe(f"{self.test_topic_root}/#")
        
        # Give it a short moment to receive any potentially remaining retained messages
        self.client.loop_start()
        time.sleep(1.0)
        self.client.loop_stop()
        self.client.disconnect()

        self.assertEqual(len(self.received_messages), 0, "Topics should have been cleared by the sweeper.")

if __name__ == "__main__":
    unittest.main()
