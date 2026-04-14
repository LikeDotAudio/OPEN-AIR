# oaComProtocols/oaComSAP/Core/mqtt_publisher.py
# Author: Gemini (Collaborator)
# Version: 20260414.1010.1

import paho.mqtt.client as mqtt
import json
import time

class StandaloneMqttPublisher:
    """
    A standalone MQTT publisher that bridges external discovered protocols
    back to the OPEN-AIR system MQTT Hub.
    """
    def __init__(self, broker_ip="localhost", broker_port=1883, client_id="SAP_Standalone", tx_callback=None):
        self.broker_ip = broker_ip
        self.broker_port = broker_port
        self.client_id = client_id
        self.tx_callback = tx_callback
        self.client = mqtt.Client(client_id=self.client_id)
        self.connected = False

    def connect(self):
        try:
            self.client.connect(self.broker_ip, self.broker_port, 60)
            self.client.loop_start()
            self.connected = True
            print(f"📡 [MQTT] Connected to {self.broker_ip}:{self.broker_port}")
        except Exception as e:
            print(f"🛑 [MQTT] Failed to connect: {e}")

    def publish(self, topic, payload):
        if not self.connected:
            return
        try:
            if self.tx_callback:
                self.tx_callback(topic, "Published to MQTT", payload)
            if isinstance(payload, dict):
                payload = json.dumps(payload)
            self.client.publish(topic, payload)
        except Exception as e:
            print(f"🛑 [MQTT] Publish error: {e}")

    def disconnect(self):
        if self.connected:
            self.client.loop_stop()
            self.client.disconnect()
            self.connected = False
            print("📡 [MQTT] Disconnected.")