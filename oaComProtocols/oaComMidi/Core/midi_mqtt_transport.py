# oaComProtocols/oaComMidi/Core/midi_mqtt_transport.py
# Author: Gemini (Collaborator)
# Version: 20260414.1800.1
#
# Description: Native MIDI event transport over MQTT.
# ⚡ CORE: Foundational transport for MIDI within the module.

import threading
import json
import ssl
import os
import random
import paho.mqtt.client as mqtt
from typing import Optional, Callable, Dict, Any
from .abc import EventTransport
from oaLogging.Methods.matrix_gate import matrix_log
from oaConfigurationManager.FileReaders.config_reader import Config

class MidiMqttTransport(EventTransport):
    """
    Native MIDI implementation of event transport over MQTT.
    ⚡ CORE: Foundational transport for MIDI within the module.
    """
    def __init__(self):
        super().__init__()
        self.config = Config.get_instance()
        self.client: Optional[mqtt.Client] = None
        self._thread: Optional[threading.Thread] = None
        matrix_log("comms", "midi_mqtt", "__init__", "📡 [MIDI-MQTT] Core Transport Initialized.", "DEBUG")

    def publish(self, topic: str, payload: Any, retain: bool = False, qos: int = 0) -> bool:
        if not self.is_connected() or not self.client:
            # Demote to TRACE to avoid log flooding during startup handshake
            matrix_log("comms", "midi_mqtt", "publish", "📡 [MIDI-MQTT] Not connected. Cannot publish.", "TRACE")
            return False
        try:
            # ⚡ EFFICIENT ENCODING: Use json for core transport compatibility
            if isinstance(payload, dict) and "meta" not in payload:
                # Inject local identity for echo prevention if not already there
                payload["meta"] = payload.get("meta", {})
                payload["meta"]["src"] = self.config.FULL_INSTANCE_ID
                payload["meta"]["full_id"] = self.config.FULL_INSTANCE_ID

            payload_str = json.dumps(payload)
            matrix_log("comms", "midi_mqtt", "publish", f"📡📤 [MIDI-MQTT] Sending to {topic}: {payload_str[:100]}", "TRACE")
            info = self.client.publish(topic, payload_str, qos=qos, retain=retain)
            return info.rc == mqtt.MQTT_ERR_SUCCESS
        except Exception as e:
            matrix_log("comms", "midi_mqtt", "publish", f"📡❌ [MIDI-MQTT] Send Error: {e}", "ERROR")
            return False

    def subscribe(self, topic: str, qos: int = 0) -> bool:
        if not self.is_connected() or not self.client:
            matrix_log("comms", "midi_mqtt", "subscribe", "📡 [MIDI-MQTT] Not connected. Cannot subscribe.", "TRACE")
            return False
        try:
            matrix_log("comms", "midi_mqtt", "subscribe", f"📡📥 [MIDI-MQTT] Subscribing to {topic}", "INFO")
            result, mid = self.client.subscribe(topic, qos=qos)
            return result == mqtt.MQTT_ERR_SUCCESS
        except Exception as e:
            matrix_log("comms", "midi_mqtt", "subscribe", f"📡❌ [MIDI-MQTT] Subscribe Error: {e}", "ERROR")
            return False

    def unsubscribe(self, topic: str) -> bool:
        if not self.is_connected() or not self.client:
            return False
        try:
            matrix_log("comms", "midi_mqtt", "unsubscribe", f"📡📥 [MIDI-MQTT] Unsubscribing from {topic}", "INFO")
            result, mid = self.client.unsubscribe(topic)
            return result == mqtt.MQTT_ERR_SUCCESS
        except Exception as e:
            matrix_log("comms", "midi_mqtt", "unsubscribe", f"📡❌ [MIDI-MQTT] Unsubscribe Error: {e}", "ERROR")
            return False

    def connect(self, connection_params: Dict[str, Any]) -> bool:
        host = connection_params.get("destination_host", self.config.MQTT_BROKER_ADDRESS)
        port = connection_params.get("destination_port", self.config.MQTT_BROKER_PORT)
        username = connection_params.get("username", self.config.MQTT_USERNAME)
        password = connection_params.get("password", self.config.MQTT_PASSWORD)
        
        # ⚡ UNIQUE IDENTITY: Prevent Client ID collisions in multi-partition environments
        partition_id = os.environ.get("OPEN_AIR_PARTITION_ID", "SUP")
        random_suffix = f"{random.getrandbits(16):04x}"
        default_client_id = f"OPENAIR-{partition_id}-MIDI-{os.getpid()}-{random_suffix}"
        client_id = connection_params.get("client_id", default_client_id)

        matrix_log("comms", "midi_mqtt", "connect", f"📡📥 [MIDI-MQTT] Connecting to {host}:{port} as {client_id}.", "INFO")

        self.client = mqtt.Client(client_id=client_id)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect

        if connection_params.get("use_tls", False):
            self.client.tls_set(tls_version=ssl.PROTOCOL_TLS)
        if username and password:
            self.client.username_pw_set(username, password)
        
        try:
            self.client.connect(host, port, 60)
            self.client.loop_start()
            
            # Wait for connection
            import time
            start_time = time.time()
            while time.time() - start_time < 2.0:
                if self._is_connected:
                    return True
                time.sleep(0.1)
                
            return self._is_connected
        except Exception as e:
            matrix_log("comms", "midi_mqtt", "connect", f"📡❌ [MIDI-MQTT] Connection Error: {e}", "ERROR")
            self.client = None
            self._is_connected = False
            return False

    def disconnect(self):
        if self.client:
            matrix_log("comms", "midi_mqtt", "disconnect", "📡 [MIDI-MQTT] Disconnecting...", "INFO")
            self.client.loop_stop()
            self.client.disconnect()
            self.client = None
            self._is_connected = False

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            matrix_log("comms", "midi_mqtt", "connect", "📡✅ [MIDI-MQTT] Connection established.", "SUCCESS")
            self._is_connected = True
        else:
            matrix_log("comms", "midi_mqtt", "connect", f"📡❌ [MIDI-MQTT] Connection Failed (RC: {rc})", "ERROR")
            self._is_connected = False

    def _on_disconnect(self, client, userdata, rc, properties=None):
        if self._is_connected:
            matrix_log("comms", "midi_mqtt", "disconnect", f"📡 [MIDI-MQTT] Connection Closed (RC: {rc})", "INFO")
        self._is_connected = False

    def _on_message(self, client, userdata, message):
        if self._message_handler:
            try:
                payload_str = message.payload.decode()
                try:
                    payload_data = json.loads(payload_str)
                except json.JSONDecodeError:
                    payload_data = payload_str
                
                # Echo prevention check moved here for transport layer
                if isinstance(payload_data, dict):
                    meta = payload_data.get("meta", {})
                    src = meta.get("src") or meta.get("full_id")
                    if src == self.config.FULL_INSTANCE_ID:
                        return

                self._message_handler(message.topic, payload_data)
            except Exception as e:
                matrix_log("comms", "midi_mqtt", "message", f"📡❌ [MIDI-MQTT] Handler Error: {e}", "ERROR")
