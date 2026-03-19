import unittest
from unittest.mock import MagicMock, patch
import queue
import time
from oaComBroker.protocol_router import ProtocolRouter

class TestProtocolRouter(unittest.TestCase):
    def setUp(self):
        # Reset singleton for testing
        ProtocolRouter._instance = None
        self.router = ProtocolRouter.get_instance()
        self.mqtt_manager = MagicMock()
        self.router.set_mqtt_manager(self.mqtt_manager)

    def tearDown(self):
        self.router.stop()

    def test_singleton(self):
        """Test that ProtocolRouter is a singleton."""
        instance1 = ProtocolRouter.get_instance()
        instance2 = ProtocolRouter.get_instance()
        self.assertIs(instance1, instance2)

    def test_ingest_puts_to_queue(self):
        """Test that ingest puts messages into the inbound queue with the correct schema."""
        self.router.ingest("MQTT", "test/topic", "test_value")
        self.assertFalse(self.router.inbound_queue.empty())
        
        msg = self.router.inbound_queue.get()
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

if __name__ == "__main__":
    unittest.main()
