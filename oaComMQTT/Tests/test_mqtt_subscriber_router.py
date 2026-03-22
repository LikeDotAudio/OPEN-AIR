# Tests/test_mqtt_subscriber_router.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import unittest
from unittest.mock import MagicMock
from oaComMQTT.Managers.mqtt_subscriber_router import MqttSubscriberRouter
from oaComMQTT.Core.mqtt_message import MqttMessage

class TestMqttSubscriberRouter(unittest.TestCase):
    def setUp(self):
        self.router = MqttSubscriberRouter()

    def test_subscribe_exact_topic(self):
        """Test exact topic subscription."""
        callback = MagicMock()
        topic = "test/exact"
        self.router.subscribe_to_topic(topic, callback)
        
        # Simulate message
        msg = MqttMessage(topic=topic, payload="hello", qos=0, retain=False)
        self.router._on_message(None, None, msg)
        
        callback.assert_called_once_with(msg)

    def test_subscribe_wildcard_topic(self):
        """Test wildcard topic subscription."""
        callback = MagicMock()
        filter = "test/#"
        self.router.subscribe_to_topic(filter, callback)
        
        # Simulate message matching wildcard
        msg = MqttMessage(topic="test/anything", payload="hello", qos=0, retain=False)
        self.router._on_message(None, None, msg)
        
        callback.assert_called_once_with(msg)

    def test_multiple_subscribers(self):
        """Test multiple subscribers for the same topic."""
        cb1 = MagicMock()
        cb2 = MagicMock()
        topic = "test/multi"
        self.router.subscribe_to_topic(topic, cb1)
        self.router.subscribe_to_topic(topic, cb2)
        
        msg = MqttMessage(topic=topic, payload="data", qos=0, retain=False)
        self.router._on_message(None, None, msg)
        
        cb1.assert_called_once_with(msg)
        cb2.assert_called_once_with(msg)

    def test_match_cache(self):
        """Test that matching results are cached."""
        callback = MagicMock()
        filter = "sensors/+/temp"
        self.router.subscribe_to_topic(filter, callback)
        
        topic = "sensors/room1/temp"
        msg = MqttMessage(topic=topic, payload="22", qos=0, retain=False)
        
        # First call (cache miss)
        self.router._on_message(None, None, msg)
        self.assertEqual(len(self.router._match_cache), 1)
        
        # Second call (cache hit)
        self.router._on_message(None, None, msg)
        self.assertEqual(callback.call_count, 2)

if __name__ == "__main__":
    unittest.main()
