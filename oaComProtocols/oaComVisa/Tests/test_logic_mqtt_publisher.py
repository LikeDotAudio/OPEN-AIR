# oaComProtocols.oaComVisa/Tests/test_logic_mqtt_publisher.py
# Author: Gemini (Collaborator)
# Version: 20260323.0000.1
#
# Description: Tests for the VisaGuiPublisher class.

import unittest
from unittest.mock import MagicMock, patch
import orjson
import time

from oaComProtocols.oaComVisa.Workers.logic_mqtt_publisher import VisaGuiPublisher, MAX_GUI_DEVICE_SLOTS

class TestVisaGuiPublisher(unittest.TestCase):

    def setUp(self):
        """Set up the mock MQTT controller and the VisaGuiPublisher instance."""
        self.mock_mqtt = MagicMock()
        self.mock_client = MagicMock()
        self.mock_mqtt.get_client_instance.return_value = self.mock_client
        
        self.publisher = VisaGuiPublisher(mqtt_controller=self.mock_mqtt)

    def test_initialization(self):
        """Verify initialization and GUID generation."""
        self.assertEqual(self.publisher.mqtt_util, self.mock_mqtt)
        self.assertIsNotNone(self.publisher.GUID)
        self.assertEqual(len(self.publisher.GUID), 4)

    def test_publish_status(self):
        """
        BUILD: Mock MQTT utility.
        OPERATE: Call _publish_status.
        CHECK: Assert the correct topic and payload (with GUID and origin) are published.
        """
        self.publisher._publish_status("connected", True)
        
        expected_topic = "OPEN-AIR/Device/Instrument_Connection/Search_and_Connect/Device_status/connected"
        self.mock_client.publish.assert_called_once()
        args, kwargs = self.mock_client.publish.call_args
        
        self.assertEqual(kwargs['topic'], expected_topic)
        payload = orjson.loads(kwargs['payload'])
        self.assertEqual(payload["value"], True)
        self.assertEqual(payload["src"], "VISA")
        self.assertEqual(payload["GUID"], self.publisher.GUID)
        self.assertTrue(kwargs['retain'])

    def test_publish_proxy_status(self):
        """
        BUILD: Mock MQTT utility.
        OPERATE: Call _publish_proxy_status.
        CHECK: Assert the proxy status and timestamp are published correctly.
        """
        self.publisher._publish_proxy_status("CONNECTED")
        
        expected_topic = "OPEN-AIR/Proxy/Status"
        self.mock_client.publish.assert_called_once()
        args, kwargs = self.mock_client.publish.call_args
        
        self.assertEqual(kwargs['topic'], expected_topic)
        payload = orjson.loads(kwargs['payload'])
        self.assertEqual(payload["status"], "CONNECTED")
        self.assertIn("timestamp", payload)

    def test_update_found_devices_gui(self):
        """
        BUILD: A list of 2 resources.
        OPERATE: Call _update_found_devices_gui.
        CHECK: Assert bulk publish to options/all and first device auto-selection.
        """
        resources = ["TCPIP::1.1.1.1::INSTR", "USB::1234::5678::INSTR"]
        self.publisher._update_found_devices_gui(resources)
        
        # 1. Check bulk publish call
        # 2. Check auto-selection call
        total_expected_calls = 2
        self.assertEqual(self.mock_client.publish.call_count, total_expected_calls)
        
        # Check bulk population
        self.mock_client.publish.assert_any_call(
            topic="OPEN-AIR/Device/Instrument_Connection/Search_and_Connect/Found_devices/options/all",
            payload=unittest.mock.ANY,
            qos=0,
            retain=False
        )
        
        # Check first device auto-selection
        self.mock_client.publish.assert_any_call(
            topic="OPEN-AIR/Device/Instrument_Connection/Search_and_Connect/Found_devices/options/1/selected",
            payload=unittest.mock.ANY,
            qos=0,
            retain=False
        )

if __name__ == '__main__':
    unittest.main()
