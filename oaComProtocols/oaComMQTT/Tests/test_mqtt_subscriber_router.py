# Tests/test_mqtt_subscriber_router.py
# Author: Anthony Peter Kuzub
# Version: 1.0.1
#
# Description: Unit tests for the Mqtt Subscriber Router with Rust core.

import unittest
from unittest.mock import MagicMock, patch
from oaComProtocols.oaComMQTT.Managers.mqtt_subscriber_router import MqttSubscriberRouter
from oaComProtocols.oaComMQTT.Core.mqtt_message import MqttMessage

class TestMqttSubscriberRouter(unittest.TestCase):
    @patch("oaComProtocols.oaComMQTT.Managers.mqtt_subscriber_router.MqttRouter")
    @patch("oaComProtocols.oaComMQTT.Managers.mqtt_connection.MqttConnectionManager")
    def setUp(self, mock_conn, mock_router):
        self.mock_router = mock_router.return_value
        self.router = MqttSubscriberRouter()

    def test_subscribe_exact_topic(self):
        """Test exact topic subscription."""
        callback = MagicMock()
        topic = "test/exact"
        self.router.subscribe_to_topic(topic, callback)
        
        # Verify Rust router was called
        self.mock_router.subscribe.assert_called_once_with(topic, callback)
        
        # Simulate message
        message = MqttMessage(topic=topic, payload="hello", qos=0, retain=False)
        self.mock_router.match_topic.return_value = [callback]
        
        self.router._on_message(None, None, message)
        
        callback.assert_called_once_with(message)

    def test_subscribe_wildcard_topic(self):
        """Test wildcard topic subscription."""
        callback = MagicMock()
        filter = "test/#"
        self.router.subscribe_to_topic(filter, callback)
        
        # Simulate message matching wildcard
        message = MqttMessage(topic="test/anything", payload="hello", qos=0, retain=False)
        self.mock_router.match_topic.return_value = [callback]
        
        self.router._on_message(None, None, message)
        
        callback.assert_called_once_with(message)

    def test_multiple_subscribers(self):
        """Test multiple subscribers for the same topic."""
        cb1 = MagicMock()
        cb2 = MagicMock()
        topic = "test/multi"
        self.router.subscribe_to_topic(topic, cb1)
        self.router.subscribe_to_topic(topic, cb2)
        
        message = MqttMessage(topic=topic, payload="data", qos=0, retain=False)
        self.mock_router.match_topic.return_value = [cb1, cb2]
        
        self.router._on_message(None, None, message)
        
        cb1.assert_called_once_with(message)
        cb2.assert_called_once_with(message)

if __name__ == "__main__":
    unittest.main()
