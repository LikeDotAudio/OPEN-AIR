# oaComProtocols/oaComSNMP/Core/snmp_mqtt_client.py
# Author: Gemini (Collaborator)
# Version: 20260414.1800.1
#
# Description: Native SNMP-specific MQTT client for 100% independence.
# ⚡ STANDALONE: This module manages its own connection and subscriptions.

import paho.mqtt.client as mqtt
import threading
import json
import time
from typing import Optional, Callable, Dict, Any

from oaLogging.Methods.matrix_gate import matrix_log

class SnmpMqttClient:
    """
    A dedicated MQTT client for the SNMP module.
    Ensures zero dependency on the core router or other protocol managers.
    """
    def __init__(self, client_id: str = "SNMP-Standalone"):
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=client_id)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect
        
        self._on_message_callback: Optional[Callable[[str, Any], None]] = None
        self._subscriptions = set()
        self._is_connected = False
        self._host = "localhost"
        self._port = 1883

    def connect(self, host: str = "localhost", port: int = 1883, keepalive: int = 60):
        self._host = host
        self._port = port
        try:
            matrix_log("comms", "snmp_mqtt", "connect", f"📡 [SNMP-MQTT] Connecting to {host}:{port}...", "INFO")
            self.client.connect(host, port, keepalive)
            self.client.loop_start()
            return True
        except Exception as e:
            matrix_log("comms", "snmp_mqtt", "connect", f"📡❌ [SNMP-MQTT] Connection failed: {e}", "ERROR")
            return False

    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()
        matrix_log("comms", "snmp_mqtt", "disconnect", "📡 [SNMP-MQTT] Disconnected.", "INFO")

    def subscribe(self, topic: str, qos: int = 0):
        self._subscriptions.add((topic, qos))
        if self._is_connected:
            self.client.subscribe(topic, qos)
            matrix_log("comms", "snmp_mqtt", "subscribe", f"🎧 [SNMP-MQTT] Subscribed to {topic}", "DEBUG")

    def publish(self, topic: str, payload: Any, retain: bool = False, qos: int = 0):
        if not isinstance(payload, str):
            payload = json.dumps(payload)
        self.client.publish(topic, payload, qos=qos, retain=retain)

    def set_on_message_callback(self, callback: Callable[[str, Any], None]):
        self._on_message_callback = callback

    def _on_connect(self, client, userdata, flags, reason_code, properties=None):
        if reason_code == 0:
            self._is_connected = True
            matrix_log("comms", "snmp_mqtt", "on_connect", "📡✅ [SNMP-MQTT] Connected to broker.", "SUCCESS")
            # Restore subscriptions
            for topic, qos in self._subscriptions:
                self.client.subscribe(topic, qos)
        else:
            matrix_log("comms", "snmp_mqtt", "on_connect", f"📡❌ [SNMP-MQTT] Connection failed with code {reason_code}", "ERROR")

    def _on_message(self, client, userdata, msg):
        if self._on_message_callback:
            try:
                topic = msg.topic
                payload_str = msg.payload.decode()
                try:
                    payload = json.loads(payload_str)
                except:
                    payload = payload_str
                self._on_message_callback(topic, payload)
            except Exception as e:
                matrix_log("comms", "snmp_mqtt", "on_message", f"📡❌ [SNMP-MQTT] Error in message handler: {e}", "ERROR")

    def _on_disconnect(self, client, userdata, flags, reason_code, properties=None):
        self._is_connected = False
        if reason_code != 0:
            matrix_log("comms", "snmp_mqtt", "on_disconnect", f"📡⚠️ [SNMP-MQTT] Unexpected disconnection: {reason_code}", "WARNING")
