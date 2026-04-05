# oaComWebsocket/Core/websocket_transport.py
# Author: Gemini (Collaborator)
# Version: 20260405.1548.3

"""
WebSocket transport implementation for IS-07 events.
"""

import websocket # For WebSocket client
import threading
import json
import time
from typing import Optional, Callable, Dict, Any

# Assuming EventTransport is imported from oaComWebsocket.Core.abc
from .abc import EventTransport 

class WebSocketEventTransport(EventTransport):
    """
    Implements IS-07 event transport over WebSocket.
    Requires 'websocket-client' library.
    """
    def __init__(self):
        super().__init__() # Call parent constructor
        self.ws_app: Optional[websocket.WebSocketApp] = None
        self._ws_thread: Optional[threading.Thread] = None
        # _message_handler is managed by the parent class EventTransport
        print("[WebSocketTransport] Initialized.")

    def publish(self, topic: str, payload: Dict[str, Any], retain: bool = False, qos: int = 0) -> bool:
        """Publishes a message to the WebSocket connection."""
        if not self.is_connected() or not self.ws_app:
            print("[WebSocketTransport] Not connected. Cannot publish.")
            return False
        try:
            payload_str = json.dumps(payload)
            print(f"[WebSocketTransport] Sending message (topic '{topic}' is conceptual): {payload_str}")
            self.ws_app.send(payload_str)
            return True
        except Exception as e:
            print(f"[WebSocketTransport] Error sending message: {e}")
            return False

    def subscribe(self, topic: str, qos: int = 0) -> bool:
        """
        For WebSocket, subscription is typically managed by sending a specific
        subscription message after connection. This method is a placeholder.
        'topic' here might represent a source ID for subscription.
        """
        print(f"[WebSocketTransport] Subscription to '{topic}' is handled via sending a specific message after connection.")
        # This would typically involve sending a JSON message like:
        # {"command": "subscription", "sources": ["topic"]}
        # This logic might be better placed in the router or a dedicated client handler.
        return True # Assume success for now, actual message sending is a publish action

    def unsubscribe(self, topic: str) -> bool:
        """
        Unsubscribes from a WebSocket endpoint. Similar to subscribe, handled via messages.
        'topic' here might represent a source ID for unsubscription.
        """
        print(f"[WebSocketTransport] Unsubscription from '{topic}' is handled via sending a specific message.")
        # This would typically involve sending a JSON message like:
        # {"command": "unsubscribe", "sources": ["topic"]}
        return True # Assume success for now

    def connect(self, connection_params: Dict[str, Any]) -> bool:
        """Connects to the WebSocket server."""
        uri = connection_params.get("connection_uri", "ws://localhost:8080")
        auth = connection_params.get("connection_authorization", False)
        # headers = ... # For authentication
        
        print(f"[WebSocketTransport] Attempting to connect to WebSocket server at {uri} (auth: {auth}).")
        
        try:
            # Basic setup for websocket-client.
            # Actual error handling, reconnection, and advanced params would be needed.
            self.ws_app = websocket.WebSocketApp(uri,
                                                on_open=self._on_open,
                                                on_message=self._on_message,
                                                on_error=self._on_error,
                                                on_close=self._on_close)
            
            self._ws_thread = threading.Thread(target=self.ws_app.run_forever)
            self._ws_thread.daemon = True # Allow main thread to exit
            self._ws_thread.start()
            
            # Give the thread a moment to establish connection
            time.sleep(1) 
            return self._is_connected # Return status after connection attempt
        except Exception as e:
            print(f"[WebSocketTransport] Connection failed: {e}")
            self.ws_app = None
            self._is_connected = False
            return False

    def disconnect(self):
        """Disconnects from the WebSocket server."""
        if self.ws_app:
            print("[WebSocketTransport] Disconnecting from WebSocket server.")
            try:
                self.ws_app.close()
                # Optionally wait for thread to finish, but daemon threads exit automatically
                # if self._ws_thread:
                #     self._ws_thread.join()
            except Exception as e:
                print(f"[WebSocketTransport] Error closing WebSocket: {e}")
            self.ws_app = None
            self._is_connected = False
        else:
            print("[WebSocketTransport] Not connected.")

    # set_message_handler is inherited from EventTransport

    def _on_open(self, ws):
        """Callback for WebSocket connection open."""
        print("[WebSocketTransport] WebSocket connection opened.")
        self._is_connected = True
        # Usually, subscription messages are sent here after connection is established.

    def _on_message(self, ws, message):
        """Callback for received WebSocket messages."""
        print(f"[WebSocketTransport] Received message: {message}")
        if self._message_handler:
            try:
                payload_data = json.loads(message)
                # The handler expects a Message or EventCore object, so we need to parse it.
                # For now, passing the raw payload dictionary.
                self._message_handler("websocket", payload_data) # Transport type is conceptual for WS
            except json.JSONDecodeError:
                print(f"[WebSocketTransport] Failed to decode JSON message.")
            except Exception as e:
                print(f"[WebSocketTransport] Error processing received message: {e}")

    def _on_error(self, ws, error):
        """Callback for WebSocket errors."""
        print(f"[WebSocketTransport] WebSocket error: {error}")
        self._is_connected = False

    def _on_close(self, ws, close_status_code, close_msg):
        """Callback for WebSocket connection close."""
        print(f"[WebSocketTransport] WebSocket connection closed (Code: {close_status_code}, Msg: {close_msg}).")
        self._is_connected = False
        self.ws_app = None
