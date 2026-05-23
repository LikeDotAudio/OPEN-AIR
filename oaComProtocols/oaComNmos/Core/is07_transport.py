# oaComProtocols/oaComNmos/Core/is07_transport.py
# Author: Gemini (Collaborator)
# Version: 20260414.1700.1
#
# Description: Native NMOS IS-07 WebSocket and MQTT transport implementations.
# ⚡ CORE: Foundational services for NMOS IS-07 messaging.

import json
import ssl
import threading
import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

import paho.mqtt.client as mqtt
import websocket

from oaComProtocols.oaComNmos.Constants.nmos_constants import NMOS_IS07_DEFAULT_URI, NMOS_IS07_RECONNECT_INTERVAL
from oaComProtocols.oaComNmos.Core.utils import gen_id
from oaLogging.Methods.matrix_gate import is_debug_allowed, matrix_log


def _is_debug(element="nmos_ws"):
    return is_debug_allowed(system="comms", element=element)

class EventTransport(ABC):
    """Abstract base class for IS-07 event transport mechanisms."""

    def __init__(self):
        self._message_handler: Callable[[str, dict[str, Any]], None] | None = None
        self._is_connected: bool = False

    @abstractmethod
    def publish(self, topic: str, payload: dict[str, Any], retain: bool = False, qos: int = 0) -> bool:
        pass

    @abstractmethod
    def subscribe(self, topic: str, qos: int = 0) -> bool:
        pass

    @abstractmethod
    def unsubscribe(self, topic: str) -> bool:
        pass

    @abstractmethod
    def connect(self, connection_params: dict[str, Any]) -> bool:
        pass

    @abstractmethod
    def disconnect(self):
        pass

    def set_message_handler(self, handler: Callable[[str, dict[str, Any]], None]):
        self._message_handler = handler

    def is_connected(self) -> bool:
        return self._is_connected

class Is07WebSocketTransport(EventTransport):
    """
    Native NMOS implementation of IS-07 event transport over WebSocket.
    ⚡ CORE: Foundational transport for IS-07 within the NMOS module.
    """
    def __init__(self):
        super().__init__()
        self.ws_app: websocket.WebSocketApp | None = None
        self._ws_thread: threading.Thread | None = None
        self._reconnect_thread: threading.Thread | None = None
        self._should_reconnect: bool = False
        self._connection_params: dict[str, Any] = {}
        matrix_log("comms", "nmos_ws", "__init__", "📡 [NMOS-WS] Core Transport Initialized.", "DEBUG")

    def publish(self, topic: str, payload: dict[str, Any], retain: bool = False, qos: int = 0) -> bool:
        if not self.is_connected() or not self.ws_app:
            matrix_log("comms", "nmos_ws", "publish", "📡 [NMOS-WS] Not connected. Cannot publish.", "WARNING")
            return False
        try:
            payload_str = json.dumps(payload)
            if _is_debug("nmos_ws"):
                matrix_log("comms", "nmos_ws", "publish", f"📡📤 [NMOS-WS] Sending: {payload_str[:100]}", "DEBUG")
            self.ws_app.send(payload_str)
            return True
        except Exception as e:
            matrix_log("comms", "nmos_ws", "publish", f"📡❌ [NMOS-WS] Send Error: {e}", "ERROR")
            return False

    def subscribe(self, topic: str, qos: int = 0) -> bool:
        # IS-07 over WS usually subscribes via messages after connection
        return True

    def unsubscribe(self, topic: str) -> bool:
        # Conceptual for WebSocket
        return True

    def connect(self, connection_params: dict[str, Any]) -> bool:
        self._connection_params = connection_params
        uri = connection_params.get("connection_uri", NMOS_IS07_DEFAULT_URI)
        reconnect = connection_params.get("reconnect", True)

        if _is_debug("nmos_ws"):
            matrix_log("comms", "nmos_ws", "connect", f"📡📥 [NMOS-WS] Connecting to {uri} (reconnect: {reconnect}).", "INFO")

        success = self._attempt_connect()

        if not success and reconnect:
            self._should_reconnect = True
            if not self._reconnect_thread or not self._reconnect_thread.is_alive():
                self._reconnect_thread = threading.Thread(target=self._reconnect_loop, daemon=True, name="NmosWsReconnect")
                self._reconnect_thread.start()

        return success

    def _attempt_connect(self) -> bool:
        uri = self._connection_params.get("connection_uri", NMOS_IS07_DEFAULT_URI)
        try:
            if self.ws_app:
                try: self.ws_app.close()
                except: pass

            self.ws_app = websocket.WebSocketApp(uri,
                                                on_open=self._on_open,
                                                on_message=self._on_message,
                                                on_error=self._on_error,
                                                on_close=self._on_close)

            self._ws_thread = threading.Thread(target=self.ws_app.run_forever)
            self._ws_thread.daemon = True
            self._ws_thread.start()

            # Wait for connection or timeout
            start_time = time.time()
            while time.time() - start_time < 2.0:
                if self._is_connected:
                    return True
                if not self._ws_thread.is_alive():
                    break
                time.sleep(0.1)

            return self._is_connected
        except Exception as e:
            matrix_log("comms", "nmos_ws", "connect", f"📡❌ [NMOS-WS] Connection exception: {e}", "ERROR")
            self.ws_app = None
            self._is_connected = False
            return False

    def _reconnect_loop(self):
        interval = self._connection_params.get("reconnect_interval", NMOS_IS07_RECONNECT_INTERVAL)
        uri = self._connection_params.get("connection_uri", NMOS_IS07_DEFAULT_URI)

        while self._should_reconnect and not self._is_connected:
            if _is_debug("nmos_ws"):
                matrix_log("comms", "nmos_ws", "reconnect", f"📡🔄 [NMOS-WS] Retrying {uri} in {interval}s...", "TRACE")
            time.sleep(interval)
            if not self._should_reconnect or self._is_connected:
                break
            self._attempt_connect()

    def disconnect(self):
        self._should_reconnect = False
        if self.ws_app:
            if _is_debug("nmos_ws"):
                matrix_log("comms", "nmos_ws", "disconnect", "📡 [NMOS-WS] Disconnecting...", "INFO")
            try:
                self.ws_app.close()
            except Exception as e:
                matrix_log("comms", "nmos_ws", "disconnect", f"📡❌ [NMOS-WS] Close Error: {e}", "ERROR")
            self.ws_app = None
            self._is_connected = False

    def _on_open(self, ws):
        if _is_debug("nmos_ws"):
            matrix_log("comms", "nmos_ws", "open", "📡✅ [NMOS-WS] Connection established.", "SUCCESS")
        self._is_connected = True

    def _on_message(self, ws, message):
        if _is_debug("nmos_ws"):
            matrix_log("comms", "nmos_ws", "message", f"📡📥 [NMOS-WS] Received: {message[:100]}", "DEBUG")
        if self._message_handler:
            try:
                payload_data = json.loads(message)
                self._message_handler("websocket", payload_data)
            except Exception as e:
                matrix_log("comms", "nmos_ws", "message", f"📡❌ [NMOS-WS] Handler Error: {e}", "ERROR")

    def _on_error(self, ws, error):
        if "Connection refused" in str(error) or "404 Not Found" in str(error):
             level = "TRACE" if self._should_reconnect else "WARNING"
             if _is_debug("nmos_ws") or level == "WARNING":
                 matrix_log("comms", "nmos_ws", "error", "📡⚠️ [NMOS-WS] Connection Refused/Not Found", level)
        else:
             matrix_log("comms", "nmos_ws", "error", f"📡❌ [NMOS-WS] Error: {error}", "ERROR")
        self._is_connected = False

    def _on_close(self, ws, close_status_code, close_message):
        if self._is_connected:
            if _is_debug("nmos_ws"):
                matrix_log("comms", "nmos_ws", "close", "📡 [NMOS-WS] Connection Closed.", "INFO")
        self._is_connected = False
        self.ws_app = None

class Is07MqttTransport(EventTransport):
    """
    Native NMOS implementation of IS-07 event transport over MQTT.
    ⚡ CORE: Foundational transport for IS-07 within the NMOS module.
    """
    def __init__(self):
        super().__init__()
        self.client: mqtt.Client | None = None
        if _is_debug("nmos_mqtt"):
            matrix_log("comms", "nmos_mqtt", "__init__", "📡 [NMOS-MQTT] Core Transport Initialized.", "DEBUG")

    def publish(self, topic: str, payload: dict[str, Any], retain: bool = False, qos: int = 0) -> bool:
        if not self.is_connected() or not self.client:
            matrix_log("comms", "nmos_mqtt", "publish", "📡 [NMOS-MQTT] Not connected. Cannot publish.", "WARNING")
            return False
        try:
            payload_str = json.dumps(payload)
            if _is_debug("nmos_mqtt"):
                matrix_log("comms", "nmos_mqtt", "publish", f"📡📤 [NMOS-MQTT] Sending to {topic}: {payload_str[:100]}", "DEBUG")
            info = self.client.publish(topic, payload_str, qos=qos, retain=retain)
            return info.rc == mqtt.MQTT_ERR_SUCCESS
        except Exception as e:
            matrix_log("comms", "nmos_mqtt", "publish", f"📡❌ [NMOS-MQTT] Send Error: {e}", "ERROR")
            return False

    def subscribe(self, topic: str, qos: int = 0) -> bool:
        if not self.is_connected() or not self.client:
            matrix_log("comms", "nmos_mqtt", "subscribe", "📡 [NMOS-MQTT] Not connected. Cannot subscribe.", "WARNING")
            return False
        try:
            if _is_debug("nmos_mqtt"):
                matrix_log("comms", "nmos_mqtt", "subscribe", f"📡📥 [NMOS-MQTT] Subscribing to {topic}", "INFO")
            result, mid = self.client.subscribe(topic, qos=qos)
            return result == mqtt.MQTT_ERR_SUCCESS
        except Exception as e:
            matrix_log("comms", "nmos_mqtt", "subscribe", f"📡❌ [NMOS-MQTT] Subscribe Error: {e}", "ERROR")
            return False

    def unsubscribe(self, topic: str) -> bool:
        if not self.is_connected() or not self.client:
            matrix_log("comms", "nmos_mqtt", "unsubscribe", "📡 [NMOS-MQTT] Not connected. Cannot unsubscribe.", "WARNING")
            return False
        try:
            if _is_debug("nmos_mqtt"):
                matrix_log("comms", "nmos_mqtt", "unsubscribe", f"📡📥 [NMOS-MQTT] Unsubscribing from {topic}", "INFO")
            result, mid = self.client.unsubscribe(topic)
            return result == mqtt.MQTT_ERR_SUCCESS
        except Exception as e:
            matrix_log("comms", "nmos_mqtt", "unsubscribe", f"📡❌ [NMOS-MQTT] Unsubscribe Error: {e}", "ERROR")
            return False

    def connect(self, connection_params: dict[str, Any]) -> bool:
        host = connection_params.get("destination_host", "localhost")
        port = connection_params.get("destination_port", 1883)
        protocol = connection_params.get("broker_protocol", "mqtt")
        username = connection_params.get("username")
        password = connection_params.get("password")
        client_id = connection_params.get("client_id", gen_id())

        if _is_debug("nmos_mqtt"):
            matrix_log("comms", "nmos_mqtt", "connect", f"📡📥 [NMOS-MQTT] Connecting to {host}:{port}.", "INFO")

        self.client = mqtt.Client(client_id=client_id)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect

        if protocol == "secure-mqtt":
            self.client.tls_set(tls_version=ssl.PROTOCOL_TLS)
        if username and password:
            self.client.username_pw_set(username, password)

        try:
            self.client.connect(host, port, 60)
            self.client.loop_start()

            # Wait for connection
            start_time = time.time()
            while time.time() - start_time < 2.0:
                if self._is_connected:
                    return True
                time.sleep(0.1)

            return self._is_connected
        except Exception as e:
            matrix_log("comms", "nmos_mqtt", "connect", f"📡❌ [NMOS-MQTT] Connection Error: {e}", "ERROR")
            self.client = None
            self._is_connected = False
            return False

    def disconnect(self):
        if self.client:
            if _is_debug("nmos_mqtt"):
                matrix_log("comms", "nmos_mqtt", "disconnect", "📡 [NMOS-MQTT] Disconnecting...", "INFO")
            self.client.loop_stop()
            self.client.disconnect()
            self.client = None
            self._is_connected = False

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            if _is_debug("nmos_mqtt"):
                matrix_log("comms", "nmos_mqtt", "connect", "📡✅ [NMOS-MQTT] Connection established.", "SUCCESS")
            self._is_connected = True
        else:
            matrix_log("comms", "nmos_mqtt", "connect", f"📡❌ [NMOS-MQTT] Connection Failed (RC: {rc})", "ERROR")
            self._is_connected = False

    def _on_disconnect(self, client, userdata, rc, properties=None):
        if self._is_connected:
            if _is_debug("nmos_mqtt"):
                matrix_log("comms", "nmos_mqtt", "disconnect", f"📡 [NMOS-MQTT] Connection Closed (RC: {rc})", "INFO")
        self._is_connected = False

    def _on_message(self, client, userdata, message):
        if _is_debug("nmos_mqtt"):
            matrix_log("comms", "nmos_mqtt", "message", f"📡📥 [NMOS-MQTT] Received on {message.topic}", "DEBUG")
        if self._message_handler:
            try:
                payload_str = message.payload.decode()
                try:
                    payload_data = json.loads(payload_str)
                except json.JSONDecodeError:
                    payload_data = payload_str
                self._message_handler(message.topic, payload_data)
            except Exception as e:
                matrix_log("comms", "nmos_mqtt", "message", f"📡❌ [NMOS-MQTT] Handler Error: {e}", "ERROR")
