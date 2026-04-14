# oaComProtocols/oaComNmos/Core/is07_transport.py
# Author: Gemini (Collaborator)
# Version: 20260414.1600.1
#
# Description: Native NMOS IS-07 WebSocket transport implementation.
# ⚡ CORE: This is a foundational service for NMOS IS-07 messaging.

import websocket
import threading
import json
import time
from typing import Optional, Callable, Dict, Any
from abc import ABC, abstractmethod

from oaLogging.Methods.matrix_gate import matrix_log

class EventTransport(ABC):
    """Abstract base class for IS-07 event transport mechanisms."""

    def __init__(self):
        self._message_handler: Optional[Callable[[str, Dict[str, Any]], None]] = None
        self._is_connected: bool = False

    @abstractmethod
    def publish(self, topic: str, payload: Dict[str, Any], retain: bool = False, qos: int = 0) -> bool:
        pass

    @abstractmethod
    def subscribe(self, topic: str, qos: int = 0) -> bool:
        pass

    @abstractmethod
    def connect(self, connection_params: Dict[str, Any]) -> bool:
        pass

    @abstractmethod
    def disconnect(self):
        pass

    def set_message_handler(self, handler: Callable[[str, Dict[str, Any]], None]):
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
        self.ws_app: Optional[websocket.WebSocketApp] = None
        self._ws_thread: Optional[threading.Thread] = None
        self._reconnect_thread: Optional[threading.Thread] = None
        self._should_reconnect: bool = False
        self._connection_params: Dict[str, Any] = {}
        matrix_log("comms", "nmos_ws", "__init__", "📡 [NMOS-WS] Core Transport Initialized.", "DEBUG")

    def publish(self, topic: str, payload: Dict[str, Any], retain: bool = False, qos: int = 0) -> bool:
        if not self.is_connected() or not self.ws_app:
            matrix_log("comms", "nmos_ws", "publish", "📡 [NMOS-WS] Not connected. Cannot publish.", "WARNING")
            return False
        try:
            payload_str = json.dumps(payload)
            matrix_log("comms", "nmos_ws", "publish", f"📡📤 [NMOS-WS] Sending: {payload_str[:100]}", "DEBUG")
            self.ws_app.send(payload_str)
            return True
        except Exception as e:
            matrix_log("comms", "nmos_ws", "publish", f"📡❌ [NMOS-WS] Send Error: {e}", "ERROR")
            return False

    def subscribe(self, topic: str, qos: int = 0) -> bool:
        # IS-07 over WS usually subscribes via messages after connection
        return True

    def connect(self, connection_params: Dict[str, Any]) -> bool:
        self._connection_params = connection_params
        uri = connection_params.get("connection_uri", "ws://localhost:8085/is07")
        reconnect = connection_params.get("reconnect", True)
        
        matrix_log("comms", "nmos_ws", "connect", f"📡📥 [NMOS-WS] Connecting to {uri} (reconnect: {reconnect}).", "INFO")
        
        success = self._attempt_connect()
        
        if not success and reconnect:
            self._should_reconnect = True
            if not self._reconnect_thread or not self._reconnect_thread.is_alive():
                self._reconnect_thread = threading.Thread(target=self._reconnect_loop, daemon=True, name="NmosWsReconnect")
                self._reconnect_thread.start()
        
        return success

    def _attempt_connect(self) -> bool:
        uri = self._connection_params.get("connection_uri", "ws://localhost:8085/is07")
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
        interval = self._connection_params.get("reconnect_interval", 5.0)
        uri = self._connection_params.get("connection_uri", "ws://localhost:8085/is07")
        
        while self._should_reconnect and not self._is_connected:
            matrix_log("comms", "nmos_ws", "reconnect", f"📡🔄 [NMOS-WS] Retrying {uri} in {interval}s...", "DEBUG")
            time.sleep(interval)
            if not self._should_reconnect or self._is_connected:
                break
            self._attempt_connect()

    def disconnect(self):
        self._should_reconnect = False
        if self.ws_app:
            matrix_log("comms", "nmos_ws", "disconnect", "📡 [NMOS-WS] Disconnecting...", "INFO")
            try:
                self.ws_app.close()
            except Exception as e:
                matrix_log("comms", "nmos_ws", "disconnect", f"📡❌ [NMOS-WS] Close Error: {e}", "ERROR")
            self.ws_app = None
            self._is_connected = False

    def _on_open(self, ws):
        matrix_log("comms", "nmos_ws", "open", "📡✅ [NMOS-WS] Connection established.", "SUCCESS")
        self._is_connected = True

    def _on_message(self, ws, message):
        matrix_log("comms", "nmos_ws", "message", f"📡📥 [NMOS-WS] Received: {message[:100]}", "DEBUG")
        if self._message_handler:
            try:
                payload_data = json.loads(message)
                self._message_handler("websocket", payload_data)
            except Exception as e:
                matrix_log("comms", "nmos_ws", "message", f"📡❌ [NMOS-WS] Handler Error: {e}", "ERROR")

    def _on_error(self, ws, error):
        if "Connection refused" in str(error) or "404 Not Found" in str(error):
             level = "DEBUG" if self._should_reconnect else "WARNING"
             matrix_log("comms", "nmos_ws", "error", f"📡⚠️ [NMOS-WS] Connection Refused/Not Found", level)
        else:
             matrix_log("comms", "nmos_ws", "error", f"📡❌ [NMOS-WS] Error: {error}", "ERROR")
        self._is_connected = False

    def _on_close(self, ws, close_status_code, close_message):
        if self._is_connected:
            matrix_log("comms", "nmos_ws", "close", f"📡 [NMOS-WS] Connection Closed.", "INFO")
        self._is_connected = False
        self.ws_app = None
