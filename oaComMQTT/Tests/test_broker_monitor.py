# oaComMQTT/Tests/test_broker_monitor.py
# Author: Gemini (Collaborator)
# Version: 20260323.0000.1
#
# Description: Tests for the BrokerMonitor class.

import unittest
from unittest.mock import MagicMock, patch

from oaComMQTT.Workers.broker_monitor import BrokerMonitor
from oaComMQTT.Core.mqtt_message import MqttMessage

class TestBrokerMonitor(unittest.TestCase):

    def setUp(self):
        """Set up the mock subscriber router and the BrokerMonitor instance."""
        self.mock_router = MagicMock()
        self.monitor = BrokerMonitor(subscriber_router=self.mock_router)

    def test_initialization_and_subscription(self):
        """
        BUILD: Instantiate BrokerMonitor with mock router (done in setUp).
        OPERATE: Check initialization state.
        CHECK: Assert it subscribed to $SYS/broker/#
        """
        self.mock_router.subscribe_to_topic.assert_called_once_with("$SYS/broker/#", self.monitor._on_sys_message)
        self.assertEqual(self.monitor.get_stats(), {})
        self.assertEqual(len(self.monitor._observers), 0)

    def test_register_and_unregister_observer(self):
        """
        BUILD: A mock observer callback.
        OPERATE: Register, then unregister.
        CHECK: Assert it's in the list when registered and not when unregistered.
        """
        mock_callback = MagicMock()
        
        # Register
        self.monitor.register_observer(mock_callback)
        self.assertIn(mock_callback, self.monitor._observers)
        
        # Register again (should not duplicate)
        self.monitor.register_observer(mock_callback)
        self.assertEqual(len(self.monitor._observers), 1)
        
        # Unregister
        self.monitor.unregister_observer(mock_callback)
        self.assertNotIn(mock_callback, self.monitor._observers)
        
        # Unregister again (should not error)
        self.monitor.unregister_observer(mock_callback)
        self.assertEqual(len(self.monitor._observers), 0)

    def test_on_sys_message_updates_stats(self):
        """
        BUILD: Create an MqttMessage mimicking a broker stat.
        OPERATE: Call _on_sys_message.
        CHECK: Assert the stats dict is updated correctly.
        """
        msg = MqttMessage(topic="$SYS/broker/clients/connected", payload=b"42")
        
        self.monitor._on_sys_message(msg)
        
        stats = self.monitor.get_stats()
        self.assertIn("clients/connected", stats)
        self.assertEqual(stats["clients/connected"], "42")

    def test_on_sys_message_notifies_observers(self):
        """
        BUILD: Register a mock observer and create a message.
        OPERATE: Call _on_sys_message.
        CHECK: Assert the observer was called with the updated stats.
        """
        mock_callback = MagicMock()
        self.monitor.register_observer(mock_callback)
        
        msg = MqttMessage(topic="$SYS/broker/messages/sent", payload=b"100")
        self.monitor._on_sys_message(msg)
        
        mock_callback.assert_called_once_with({"messages/sent": "100"})

    @patch("oaComMQTT.Workers.broker_monitor.MQTT_LOGGER")
    def test_observer_exception_handled(self, mock_logger):
        """
        BUILD: Register an observer that raises an Exception.
        OPERATE: Call _on_sys_message.
        CHECK: Assert the exception was caught and logged, not propagated.
        """
        mock_callback = MagicMock(side_effect=Exception("Test Exception"))
        self.monitor.register_observer(mock_callback)
        
        msg = MqttMessage(topic="$SYS/broker/test", payload=b"test")
        
        # This should not raise an exception
        self.monitor._on_sys_message(msg)
        
        mock_logger.exception.assert_called_once_with("Error notifying BrokerMonitor observer")

if __name__ == '__main__':
    unittest.main()
