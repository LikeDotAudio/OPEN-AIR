# FolderName/FileName.py
# Author: Gemini (Collaborator)
# Version: 20260414.1730.1
#
# Description: Unit tests for NMOS IS-07 Core Transports.

import unittest
from unittest.mock import MagicMock, patch
from oaComProtocols.oaComNmos.Core.is07_transport import Is07WebSocketTransport, Is07MqttTransport

class TestIs07Transports(unittest.TestCase):

    def test_ws_transport_init(self):
        transport = Is07WebSocketTransport()
        self.assertFalse(transport.is_connected())

    def test_mqtt_transport_init(self):
        transport = Is07MqttTransport()
        self.assertFalse(transport.is_connected())

    @patch('paho.mqtt.client.Client')
    def test_mqtt_transport_connect(self, mock_client):
        # Mocking Client
        mock_instance = mock_client.return_value
        transport = Is07MqttTransport()
        
        # Simulate connection success
        def mock_connect(*args, **kwargs):
            transport._is_connected = True
            return 0
        
        mock_instance.connect.side_effect = mock_connect
        
        params = {
            "destination_host": "localhost",
            "destination_port": 1883
        }
        
        success = transport.connect(params)
        self.assertTrue(success)
        self.assertTrue(transport.is_connected())
        mock_instance.loop_start.assert_called_once()

    @patch('paho.mqtt.client.Client')
    def test_mqtt_transport_publish(self, mock_client):
        mock_instance = mock_client.return_value
        transport = Is07MqttTransport()
        transport._is_connected = True
        transport.client = mock_instance
        
        # Mock publish result
        mock_info = MagicMock()
        mock_info.rc = 0 # mqtt.MQTT_ERR_SUCCESS
        mock_instance.publish.return_value = mock_info
        
        success = transport.publish("test/topic", {"val": True})
        self.assertTrue(success)
        mock_instance.publish.assert_called_once()

if __name__ == '__main__':
    unittest.main()
