# oaComProtocols.oaComWebsocket/Core/websocket_transport.py
# Author: Gemini (Collaborator)
# Version: 20260405.1548.3

"""
WebSocket transport implementation for IS-07 events.
"""

import json
import threading
import time
from typing import Any

import websocket  # For WebSocket client

from oaLogging.Methods.matrix_gate import matrix_log

# Assuming EventTransport is imported from oaComProtocols.oaComWebsocket.Core.abc
from .abc import EventTransport


class WebSocketEventTransport(EventTransport):
    """
    Implements IS-07 event transport over WebSocket.
    Requires 'websocket-client' library.
    """
    def __init__(self):
        super().__init__() # Call parent constructor
        self.ws_app: websocket.WebSocketApp | None = None
        self._ws_thread: threading.Thread | None = None
        self._reconnect_thread: threading.Thread | None = None
        self._should_reconnect: bool = False
        self._connection_params: dict[str, Any] = {}
        # _message_handler is managed by the parent class EventTransport
        matrix_log("comms", "websocket", "__init__", "📡 [WebSocketTransport] Initialized.", "DEBUG")

    def publish(self, topic: str, payload: dict[str, Any], retain: bool = False, qos: int = 0) -> bool:
        """Publishes a message to the WebSocket connection."""
        if not self.is_connected() or not self.ws_app:
            matrix_log("comms", "websocket", "publish", "📡 [WebSocketTransport] Not connected. Cannot publish.", "WARNING")
            return False
        try:
            payload_str = json.dumps(payload)
            matrix_log("comms", "websocket", "publish", f"📡📤 [WebSocketTransport] Sending message: {payload_str}", "DEBUG")
            self.ws_app.send(payload_str)
            return True
        except Exception as e:
            matrix_log("comms", "websocket", "publish", f"📡❌ [WebSocketTransport] Error sending message: {e}", "ERROR")
            return False

    def subscribe(self, topic: str, qos: int = 0) -> bool:
        """
        For WebSocket, subscription is typically managed by sending a specific
        subscription message after connection. This method is a placeholder.
        """
        matrix_log("comms", "websocket", "subscribe", f"📡 [WebSocketTransport] Subscription to '{topic}' conceptual.", "DEBUG")
        return True

    def unsubscribe(self, topic: str) -> bool:
        """
        Unsubscribes from a WebSocket endpoint.
        """
        matrix_log("comms", "websocket", "unsubscribe", f"📡 [WebSocketTransport] Unsubscription from '{topic}' conceptual.", "DEBUG")
        return True

    def connect(self, connection_params: dict[str, Any]) -> bool:
        """Connects to the WebSocket server."""
        self._connection_params = connection_params
        uri = connection_params.get("connection_uri", "ws://localhost:8080")
        auth = connection_params.get("connection_authorization", False)
        reconnect = connection_params.get("reconnect", True)

        matrix_log("comms", "websocket", "connect", f"📡📥 [WebSocketTransport] Attempting connection to {uri} (auth: {auth}, reconnect: {reconnect}).", "INFO")

        success = self._attempt_connect()

        if not success and reconnect:
            self._should_reconnect = True
            if not self._reconnect_thread or not self._reconnect_thread.is_alive():
                self._reconnect_thread = threading.Thread(target=self._reconnect_loop, daemon=True, name="WebSocketReconnect")
                self._reconnect_thread.start()

        return success

    def _attempt_connect(self) -> bool:
        """Internal helper to perform a single connection attempt."""
        uri = self._connection_params.get("connection_uri", "ws://localhost:8080")
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

            # Wait for either connection success or thread exit
            start_time = time.time()
            while time.time() - start_time < 2.0:
                if self._is_connected:
                    return True
                if not self._ws_thread.is_alive():
                    break
                time.sleep(0.1)

            return self._is_connected
        except Exception as e:
            matrix_log("comms", "websocket", "connect", f"📡❌ [WebSocketTransport] Connection exception: {e}", "ERROR")
            self.ws_app = None
            self._is_connected = False
            return False

    def _reconnect_loop(self):
        """Background loop for handling reconnections."""
        interval = self._connection_params.get("reconnect_interval", 5.0)
        uri = self._connection_params.get("connection_uri", "ws://localhost:8080")

        while self._should_reconnect and not self._is_connected:
            matrix_log("comms", "websocket", "_reconnect_loop", f"📡🔄 [WebSocketTransport] Retrying connection to {uri} in {interval}s...", "DEBUG")
            time.sleep(interval)
            if not self._should_reconnect or self._is_connected:
                break
            self._attempt_connect()

    def disconnect(self):
        """Disconnects from the WebSocket server."""
        self._should_reconnect = False
        if self.ws_app:
            matrix_log("comms", "websocket", "disconnect", "📡 [WebSocketTransport] Disconnecting...", "INFO")
            try:
                self.ws_app.close()
            except Exception as e:
                matrix_log("comms", "websocket", "disconnect", f"📡❌ [WebSocketTransport] Error closing: {e}", "ERROR")
            self.ws_app = None
            self._is_connected = False

    def _on_open(self, ws):
        """Callback for WebSocket connection open."""
        matrix_log("comms", "websocket", "_on_open", "📡✅ [WebSocketTransport] Connection opened.", "SUCCESS")
        self._is_connected = True

    def _on_message(self, ws, message):
        """Callback for received WebSocket messages."""
        matrix_log("comms", "websocket", "_on_message", f"📡📥 [WebSocketTransport] Received: {message[:100]}...", "DEBUG")
        if self._message_handler:
            try:
                payload_data = json.loads(message)
                self._message_handler("websocket", payload_data)
            except json.JSONDecodeError:
                matrix_log("comms", "websocket", "_on_message", "📡❌ [WebSocketTransport] Failed to decode JSON.", "ERROR")
            except Exception as e:
                matrix_log("comms", "websocket", "_on_message", f"📡❌ [WebSocketTransport] Handler Error: {e}", "ERROR")

    def _on_error(self, ws, error):
        """Callback for WebSocket errors."""
        # ⚡ SUPPRESSION: Demote 'Connection refused' to DEBUG if we are in reconnect mode
        if "Connection refused" in str(error):
             level = "DEBUG" if self._should_reconnect else "WARNING"
             matrix_log("comms", "websocket", "_on_error", f"📡⚠️ [WebSocketTransport] Connection Refused (Server down at {ws.url if hasattr(ws, 'url') else 'target'})", level)
        else:
             matrix_log("comms", "websocket", "_on_error", f"📡❌ [WebSocketTransport] Error: {error}", "ERROR")
        self._is_connected = False

    def _on_close(self, ws, close_status_code, close_message):
        """Callback for WebSocket connection close."""
        if self._is_connected:
            matrix_log("comms", "websocket", "_on_close", f"📡 [WebSocketTransport] Closed (Code: {close_status_code}, Message: {close_message}).", "INFO")

        self._is_connected = False
        # If it was an unexpected close, trigger reconnect if enabled
        if self._should_reconnect and not self._is_connected:
             if not self._reconnect_thread or not self._reconnect_thread.is_alive():
                self._reconnect_thread = threading.Thread(target=self._reconnect_loop, daemon=True, name="WebSocketReconnect")
                self._reconnect_thread.start()
        self.ws_app = None
