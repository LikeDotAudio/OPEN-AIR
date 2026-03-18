import unittest
from unittest.mock import MagicMock, patch
from oaComOSC.osc import OSCManager

class TestOSCManager(unittest.TestCase):
    def setUp(self):
        self.state_cache_manager = MagicMock()
        self.mqtt_connection_manager = MagicMock()
        # Mock servers to avoid socket binding
        with patch("oaComOSC.osc.OscRxServer"), \
             patch("oaComOSC.osc.OscTxClient"):
            self.manager = OSCManager(
                state_cache_manager=self.state_cache_manager,
                mqtt_connection_manager=self.mqtt_connection_manager,
                run_bridge=True
            )

    def test_initialization(self):
        """Test OSCManager initialization."""
        self.assertFalse(self.manager._running)
        self.assertEqual(len(self.manager.osc_to_topic), 0)

    def test_register_route(self):
        """Test registering a route between OSC and MQTT."""
        self.manager.register_route("/test/osc", "OPEN-AIR/test/topic")
        self.assertEqual(self.manager.osc_to_topic["/test/osc"], "OPEN-AIR/test/topic")
        self.assertEqual(self.manager.topic_to_osc["OPEN-AIR/test/topic"], "/test/osc")

    def test_handle_incoming_osc(self):
        """Test handling of incoming OSC messages."""
        self.manager.register_route("/test/osc", "OPEN-AIR/test/topic")
        
        # Simulate incoming OSC message
        self.manager.handle_incoming_osc("/test/osc", 0.5)
        
        # Verify state_cache_manager was notified
        self.state_cache_manager.handle_external_update.assert_any_call(
            "OPEN-AIR/test/topic", 0.5, source="OSC", metadata=unittest.mock.ANY
        )

    def test_monitor_callbacks(self):
        """Test that monitor callbacks are triggered."""
        callback = MagicMock()
        self.manager.add_monitor_callback(callback)
        
        self.manager.handle_incoming_osc("/test/osc", 0.75)
        
        callback.assert_called_with("RX", "/test/osc", 0.75, unittest.mock.ANY)

if __name__ == "__main__":
    unittest.main()
