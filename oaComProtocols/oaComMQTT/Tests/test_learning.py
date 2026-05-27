# Tests/test_learning.py
# Author: Gemini CLI
# Version: 20260404.2250.1
#
# Description: Learning tests for third-party libraries (paho-mqtt, pyvisa).

import unittest
from unittest.mock import MagicMock

import paho.mqtt.client as mqtt


class TestLearningThirdParty(unittest.TestCase):
    # --- 5. "Learning Tests" for Third-Party Libraries ---
    def test_paho_mqtt_client_callbacks(self):
        """Clean Code: Learning Tests (Verify paho-mqtt behavior)"""
        # Ensure our understanding of the paho-mqtt callback structure is correct
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        mock_on_connect = MagicMock()
        client.on_connect = mock_on_connect

        # Test basic attribute assignment
        self.assertEqual(client.on_connect, mock_on_connect)

    def test_paho_mqtt_topic_matching(self):
        """Learning Test: Verify MQTT wildcard matching assumptions"""
        # This tests our understanding of topic_matches_sub
        self.assertTrue(mqtt.topic_matches_sub('OpenAir/+/status', 'OpenAir/Device1/status'))
        self.assertTrue(mqtt.topic_matches_sub('OpenAir/#', 'OpenAir/any/nested/topic'))
        self.assertFalse(mqtt.topic_matches_sub('OpenAir/+/status', 'OpenAir/Device1/error'))

if __name__ == "__main__":
    unittest.main()
