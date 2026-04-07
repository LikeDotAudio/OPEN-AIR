# oaComProtocols.oaComVisa/Tests/test_logic_mqtt_listen.py
# Author: Gemini (Collaborator)
# Version: 20260323.0000.1
#
# Description: Tests for the VisaMqttListener class.

import unittest
from unittest.mock import MagicMock, patch
import orjson
import threading

from oaComProtocols.oaComVisa.Workers.logic_mqtt_listen import VisaMqttListener, MQTT_TOPIC_SEARCH_TRIGGER, MQTT_TOPIC_DEVICE_SELECT

class TestVisaMqttListener(unittest.TestCase):

    def setUp(self):
        """Set up the mock services and the VisaMqttListener instance."""
        self.mock_router = MagicMock()
        self.mock_searcher = MagicMock()
        self.mock_connector = MagicMock()
        self.mock_disconnector = MagicMock()
        self.mock_publisher = MagicMock()
        
        self.listener = VisaMqttListener(
            subscriber_router=self.mock_router,
            searcher=self.mock_searcher,
            connector=self.mock_connector,
            disconnector=self.mock_disconnector,
            gui_publisher=self.mock_publisher
        )

    def test_initialization_and_subscriptions(self):
        """Verify that all topics are subscribed to during initialization."""
        # Check if subscribe_to_topic was called for each expected topic
        # (The exact topics are defined as constants in the module)
        self.assertEqual(self.mock_router.subscribe_to_topic.call_count, 5)

    def test_on_search_request_valid(self):
        """
        BUILD: Mock searcher to return resources.
        OPERATE: Call _on_search_request with val=True.
        CHECK: Assert searcher is called and GUI is updated.
        """
        self.mock_searcher.search_resources.return_value = ["DEV1", "DEV2"]
        payload = orjson.dumps({"val": True})
        
        self.listener._on_search_request(MQTT_TOPIC_SEARCH_TRIGGER, payload)
        
        self.mock_searcher.search_resources.assert_called_once()
        self.mock_publisher._update_found_devices_gui.assert_called_with(["DEV1", "DEV2"])
        self.assertEqual(self.listener.found_resources, ["DEV1", "DEV2"])

    def test_on_device_select(self):
        """
        BUILD: Populate found_resources.
        OPERATE: Call _on_device_select with a specific index.
        CHECK: Assert the correct resource is selected.
        """
        self.listener.found_resources = ["RES1", "RES2", "RES3"]
        # Topic format: .../options/<index>/selected. Let's pick index 2 (1-based is 2, 0-based is 1)
        topic = "OPEN-AIR/Device/Instrument_Connection/Search_and_Connect/Found_devices/options/2/selected"
        payload = orjson.dumps({"value": True})
        
        self.listener._on_device_select(topic, payload)
        
        self.assertEqual(self.listener.selected_device_resource, "RES2")

    @patch('threading.Thread')
    def test_on_gui_connect_request(self, MockThread):
        """
        BUILD: Set selected_device_resource.
        OPERATE: Call _on_gui_connect_request.
        CHECK: Assert a thread is started to handle the connection.
        """
        self.listener.selected_device_resource = "TCPIP::1.2.3.4::INSTR"
        payload = orjson.dumps({"value": True})
        
        self.listener._on_gui_connect_request("topic", payload)
        
        MockThread.assert_called_once()
        args, kwargs = MockThread.call_args
        self.assertEqual(kwargs['target'], self.listener._connect_and_get_inst)
        self.assertEqual(kwargs['args'], ("TCPIP::1.2.3.4::INSTR",))
        MockThread.return_value.start.assert_called_once()

    @patch('threading.Thread')
    def test_on_gui_disconnect_request(self, MockThread):
        """
        BUILD: Set active instrument.
        OPERATE: Call _on_gui_disconnect_request.
        CHECK: Assert a thread is started to handle the disconnection.
        """
        mock_inst = MagicMock()
        self.listener.inst = mock_inst
        payload = orjson.dumps({"value": True})
        
        self.listener._on_gui_disconnect_request("topic", payload)
        
        MockThread.assert_called_once()
        args, kwargs = MockThread.call_args
        self.assertEqual(kwargs['target'], self.mock_disconnector.disconnect_instrument_logic)
        self.assertEqual(kwargs['args'], (mock_inst,))
        MockThread.return_value.start.assert_called_once()
        self.assertIsNone(self.listener.inst)

    @patch('threading.Thread')
    def test_on_connect_request_direct(self, MockThread):
        """
        BUILD: Create a direct connect request payload.
        OPERATE: Call _on_connect_request.
        CHECK: Assert a thread is started for the specific resource.
        """
        payload = orjson.dumps({"resource": "GPIB0::7::INSTR"})
        
        self.listener._on_connect_request("topic", payload)
        
        MockThread.assert_called_once()
        args, kwargs = MockThread.call_args
        self.assertEqual(kwargs['args'], ("GPIB0::7::INSTR",))

if __name__ == '__main__':
    unittest.main()
