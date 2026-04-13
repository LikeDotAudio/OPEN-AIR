# oaComProtocols.oaComWebsocket/Tests/test_websocket_transport.py
# Author: Anthony Peter Kuzub
# Version: 20260410.1000.1
#
# Description: Unit tests for WebSocketEventTransport ensuring Hub-and-Spoke integrity, 
# and standardized standalone behavior.

import unittest
from unittest.mock import MagicMock, patch
import json

# --- Target Module ---
from oaComProtocols.oaComWebsocket.Core.websocket_transport import WebSocketEventTransport

class TestWebSocketTransport(unittest.TestCase):
    """
    Architectural Integrity Tests for WebSocket Protocol Spoke.
    Follows BUILD -> OPERATE -> CHECK pattern.
    """

    def setUp(self):
        """BUILD: Initialize mocks and transport in isolation."""
        # Patch the websocket library to prevent real network IO
        self.patcher_ws = patch("websocket.WebSocketApp")
        self.mock_ws_app_class = self.patcher_ws.start()
        
        self.transport = WebSocketEventTransport()
        self.mock_handler = MagicMock()
        self.transport.set_message_handler(self.mock_handler)

    def tearDown(self):
        """Cleanup patches."""
        self.transport.disconnect()
        self.patcher_ws.stop()

    def test_spoke_connect_lifecycle(self):
        """CHECK: Verify connection lifecycle and internal state."""
        params = {"connection_uri": "ws://mock-server:8080", "reconnect": False}
        
        # OPERATE
        self.transport.connect(params)
        
        # CHECK: WebSocketApp was initialized with correct URI
        self.mock_ws_app_class.assert_called()
        args, kwargs = self.mock_ws_app_class.call_args
        self.assertEqual(args[0], "ws://mock-server:8080")

    def test_hub_to_spoke_publish(self):
        """OPERATE: Simulate Hub broadcasting to WebSocket Spoke."""
        # BUILD: Force connected state
        self.transport._is_connected = True
        self.transport.ws_app = MagicMock()
        
        test_payload = {"value": 42, "topic": "test/path"}
        
        # OPERATE
        self.transport.publish("test/path", test_payload)
        
        # CHECK: Transmitted to WebSocket Spoke
        self.transport.ws_app.send.assert_called_with(json.dumps(test_payload))

    def test_spoke_to_hub_ingest(self):
        """OPERATE: Simulate incoming WebSocket data (Spoke -> Hub)."""
        # BUILD
        test_message = json.dumps({"value": 100, "topic": "remote/fader"})
        
        # OPERATE: Manually trigger the _on_message callback
        self.transport._on_message(None, test_message)
        
        # CHECK: Data passed to the system handler (Hub)
        self.mock_handler.assert_called_with("websocket", {"value": 100, "topic": "remote/fader"})

if __name__ == "__main__":
    unittest.main()
