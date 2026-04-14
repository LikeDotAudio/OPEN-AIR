# oaComProtocols/oaComREST/Core/rest_mqtt_transport.py
# Author: Gemini (Collaborator)
# Version: 20260414.2000.1
#
# Description: Native REST event transport over MQTT.
# ⚡ CORE: Foundational transport for REST within the module.

import threading
import json
import ssl
import paho.mqtt.client as mqtt
from typing import Optional, Callable, Dict, Any
from .abc import EventTransport
from oaLogging.Methods.matrix_gate import matrix_log
from oaConfigurationManager.FileReaders.config_reader import Config

class RestMqttTransport(EventTransport):
    """
    Native REST implementation of event transport over MQTT.
    ⚡ CORE: Foundational transport for REST within the module.
    """
    def __init__(self):
        super().__init__()
        self.config = Config.get_instance()
        self.client: Optional[mqtt.Client] = None
        matrix_log("comms", "rest_mqtt", "__init__", "📡 [REST-MQTT] Core Transport Initialized.", "DEBUG")

    def publish(self, topic: str, payload: Any, retain: bool = False, qos: int = 0) -> bool:
        if not self.is_connected() or not self.client:
            return False
        try:
            payload_str = json.dumps(payload)
            matrix_log("comms", "rest_mqtt", "publish", f"📡📤 [REST-MQTT] Sending to {topic}: {payload_str[:100]}", "TRACE")
            info = self.client.publish(topic, payload_str, qos=qos, retain=retain)
            return info.rc == mqtt.MQTT_ERR_SUCCESS
        except Exception as e:
            matrix_log("comms", "rest_mqtt", "publish", f"📡❌ [REST-MQTT] Send Error: {e}", "ERROR")
            return False

    def subscribe(self, topic: str, qos: int = 0) -> bool:
        if not self.is_connected() or not self.client:
            return False
        try:
            matrix_log("comms", "rest_mqtt", "subscribe", f"📡📥 [REST-MQTT] Subscribing to {topic}", "INFO")
            result, mid = self.client.subscribe(topic, qos=qos)
            return result == mqtt.MQTT_ERR_SUCCESS
        except Exception as e:
            matrix_log("comms", "rest_mqtt", "subscribe", f"📡❌ [REST-MQTT] Subscribe Error: {e}", "ERROR")
            return False

    def unsubscribe(self, topic: str) -> bool:
        if not self.is_connected() or not self.client:
            return False
        try:
            matrix_log("comms", "rest_mqtt", "unsubscribe", f"📡📥 [REST-MQTT] Unsubscribing from {topic}", "INFO")
            result, mid = self.client.unsubscribe(topic)
            return result == mqtt.MQTT_ERR_SUCCESS
        except Exception as e:
            matrix_log("comms", "rest_mqtt", "unsubscribe", f"📡❌ [REST-MQTT] Unsubscribe Error: {e}", "ERROR")
            return False

    def connect(self, connection_params: Dict[str, Any]) -> bool:
        host = connection_params.get("destination_host", "localhost")
        port = connection_params.get("destination_port", 1883)
        username = connection_params.get("username")
        password = connection_params.get("password")
        client_id = connection_params.get("client_id", f"oaRestCore_{int(threading.get_ident())}")

        matrix_log("comms", "rest_mqtt", "connect", f"📡📥 [REST-MQTT] Connecting to {host}:{port}.", "INFO")

        # Support both Paho v1.x and v2.x
        if hasattr(mqtt, 'CallbackVersion'):
            self.client = mqtt.Client(callback_api_version=mqtt.CallbackVersion.VERSION2, client_id=client_id)
        else:
            self.client = mqtt.Client(client_id=client_id)

        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect

        if connection_params.get("use_tls", False):
            self.client.tls_set(tls_version=ssl.PROTOCOL_TLS)
        if username and password:
            self.client.username_pw_set(username, password)
        
        try:
            self.client.connect_async(host, port, 60)
            self.client.loop_start()
            
            import time
            start_time = time.time()
            while time.time() - start_time < 2.0:
                if self._is_connected:
                    return True
                time.sleep(0.1)
                
            return self._is_connected
        except Exception as e:
            matrix_log("comms", "rest_mqtt", "connect", f"📡❌ [REST-MQTT] Connection Error: {e}", "ERROR")
            self.client = None
            self._is_connected = False
            return False

    def disconnect(self):
        if self.client:
            matrix_log("comms", "rest_mqtt", "disconnect", "📡 [REST-MQTT] Disconnecting...", "INFO")
            self.client.loop_stop()
            self.client.disconnect()
            self.client = None
            self._is_connected = False

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            matrix_log("comms", "rest_mqtt", "connect", "📡✅ [REST-MQTT] Connection established.", "SUCCESS")
            self._is_connected = True
        else:
            matrix_log("comms", "rest_mqtt", "connect", f"📡❌ [REST-MQTT] Connection Failed (RC: {rc})", "ERROR")
            self._is_connected = False

    def _on_disconnect(self, client, userdata, rc, properties=None):
        if self._is_connected:
            matrix_log("comms", "rest_mqtt", "disconnect", f"📡 [REST-MQTT] Connection Closed (RC: {rc})", "INFO")
        self._is_connected = False

    def _on_message(self, client, userdata, message):
        if self._message_handler:
            try:
                payload_str = message.payload.decode()
                try:
                    payload_data = json.loads(payload_str)
                except json.JSONDecodeError:
                    payload_data = payload_str
                self._message_handler(message.topic, payload_data)
            except Exception as e:
                matrix_log("comms", "rest_mqtt", "message", f"📡❌ [REST-MQTT] Handler Error: {e}", "ERROR")
