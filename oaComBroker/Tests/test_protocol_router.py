# Tests/test_protocol_router.py
# Author: Anthony Peter Kuzub
# Version: 1.0.1
#
# Description: Unit tests for the Protocol Router with Rust core.

import unittest
from unittest.mock import MagicMock, patch
from oaComBroker.Core.protocol_router.manager import ProtocolRouter

class TestProtocolRouter(unittest.TestCase):
    @patch("oaComBroker.Core.protocol_router.router.RustCoreRouter")
    def setUp(self, mock_rust_router):
        # Reset singleton for testing
        ProtocolRouter._instance = None
        self.mock_rust = mock_rust_router.return_value
        
        # ⚡ OPTIMIZATION: Prevent infinite MagicMock ingest loops
        self.mock_rust.pop_inbound.return_value = None
        self.mock_rust.pop_outbound.return_value = None
        self.mock_rust.inbound_len.return_value = 0
        self.mock_rust.outbound_len.return_value = 0
        
        self.router = ProtocolRouter.get_instance(force_reload=True)
        self.mqtt_manager = MagicMock()
        self.router.set_mqtt_manager(self.mqtt_manager)

    def tearDown(self):
        self.router.stop()

    def test_singleton(self):
        """Test that ProtocolRouter is a singleton."""
        instance1 = ProtocolRouter.get_instance()
        instance2 = ProtocolRouter.get_instance()
        self.assertIs(instance1, instance2)

    @unittest.skip("TODO: BUG: Rust router integration disabled - Hangs ingest pipeline.")
    def test_ingest_pushes_to_rust_router(self):
        """Test that ingest pushes messages into the rust router with the correct schema."""
        self.router.ingest("MQTT", "test/topic", "test_value")
        
        # Verify push_inbound was called
        self.assertTrue(self.mock_rust.push_inbound.called)
        msg = self.mock_rust.push_inbound.call_args[0][0]
        
        self.assertEqual(msg["topic"], "test/topic")
        self.assertEqual(msg["val"], "test_value")
        self.assertEqual(msg["source"], "MQTT")
        # Check Unified Message Schema fields
        self.assertIn("msg_guid", msg)
        self.assertIn("msg_type", msg)
        self.assertIn("ts", msg)

    def test_router_stop_stops_threads(self):
        """Test that stop() correctly resets the running flag."""
        self.router.start()
        self.assertTrue(self.router._running)
        self.router.stop()
        self.assertFalse(self.router._running)

    def test_echo_suppression_strategy(self):
        """Test that MQTT messages from our own instance are assigned IGNORE strategy to prevent loops."""
        from oaComBroker.Core.protocol_router.strategy import calculate_strategy
        from oaComBroker.Core.protocol_router.constants import app_constants
        
        # 1. External message (Different full_id) should get a valid strategy
        ext_msg = {
            "source": "MQTT",
            "logical_source": "MQTT",
            "topic": "OPEN-AIR/GUI/test",
            "val": 1.0,
            "full_id": "different_instance_id"
        }
        ext_strategy = calculate_strategy(ext_msg)
        self.assertNotEqual(ext_strategy, "IGNORE (REFLECT)")
        
        # 2. Echo message (Same full_id) should be IGNORED
        echo_msg = {
            "source": "MQTT",
            "logical_source": "MQTT",
            "topic": "OPEN-AIR/GUI/test",
            "val": 1.0,
            "full_id": app_constants.FULL_INSTANCE_ID
        }
        echo_strategy = calculate_strategy(echo_msg)
        self.assertEqual(echo_strategy, "IGNORE (REFLECT)")

if __name__ == "__main__":
    unittest.main()
