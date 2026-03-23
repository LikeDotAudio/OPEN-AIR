# oaComMQTT/Tests/test_mqtt_manager.py
# Author: Gemini (Collaborator)
# Version: 20260323.0000.1
#
# Description: Tests for the MqttManager class.

import unittest
from unittest.mock import MagicMock, patch, call
import queue
import time
import orjson

from oaComMQTT.Managers.mqtt_manager import MqttManager
from oaComMQTT.Core.mqtt_message import MqttMessage

class TestMqttManager(unittest.TestCase):

    @patch('threading.Thread')
    def setUp(self, MockThread):
        """Set up the MqttManager with mock services and suppress internal threads."""
        self.mock_router = MagicMock()
        self.mock_client = MagicMock()
        self.mock_cache = MagicMock()
        
        self.manager = MqttManager(
            subscriber_router=self.mock_router,
            mqtt_client=self.mock_client,
            state_cache_manager=self.mock_cache
        )
        
        # Stop threads if they started (MockThread.start() was called)
        self.manager._is_running = False

    def test_initialization(self):
        """Verify initialization and initial subscriptions."""
        self.mock_router.subscribe_to_topic.assert_any_call("OPEN-AIR/System/Control/Broker/Delete/#", self.manager._handle_delete_command)
        self.mock_router.subscribe_to_topic.assert_any_call("OPEN-AIR/System/Control/Broker/Service/#", self.manager._handle_service_command)
        self.mock_router.subscribe_to_topic.assert_any_call("OPEN-AIR/System/Status/Fleet/Complete", self.manager._on_fleet_scan_complete)

    def test_publish_async(self):
        """Verify publish_async correctly queues messages."""
        self.manager._publish_async("test/topic", "payload", retain=True)
        self.assertEqual(self.manager._publish_queue.qsize(), 1)
        item = self.manager._publish_queue.get()
        self.assertEqual(item, ("test/topic", "payload", True))

    @patch('oaComMQTT.Managers.mqtt_manager.delete_open_air_tree')
    def test_handle_delete_command(self, mock_delete):
        """Verify _handle_delete_command calls delete_open_air_tree."""
        msg = MqttMessage("OPEN-AIR/System/Control/Broker/Delete/all", b"{}")
        self.manager._handle_delete_command(msg)
        mock_delete.assert_called_once_with(self.mock_client, self.mock_cache)

    def test_on_fleet_scan_complete_logging(self):
        """Verify scan complete logic executes without error (checks log path)."""
        with patch('oaComMQTT.Managers.mqtt_manager.logger') as mock_logger:
            msg = MqttMessage("topic", b"{}")
            self.manager._on_fleet_scan_complete(msg)
            mock_logger.success.assert_called()

    @patch('oaComMQTT.Managers.mqtt_manager.orjson.dumps')
    def test_publish_worker_loop(self, mock_dumps):
        """
        BUILD: Enqueue a message and mock connected client.
        OPERATE: Call _publish_worker once (via mocking the loop condition).
        CHECK: Assert client.publish is called with correct args.
        """
        self.manager._is_running = True
        self.manager._publish_queue.put(("test/topic", "payload", False))
        self.mock_client.is_connected.return_value = True
        
        # We need a way to break the loop after one iteration
        # Let's mock the queue.get to return once, then raise an exception or set is_running to False
        orig_get = self.manager._publish_queue.get
        def side_effect(*args, **kwargs):
            self.manager._is_running = False # Break after this iteration
            return orig_get(*args, **kwargs)
        
        with patch.object(self.manager._publish_queue, 'get', side_effect=side_effect):
            self.manager._publish_worker()
            
        self.mock_client.publish.assert_called_once_with("test/topic", "payload", retain=False)

    @patch('oaComMQTT.Managers.mqtt_manager.app_paths')
    @patch('oaComMQTT.Managers.mqtt_manager.app_constants')
    def test_system_status_loop_iteration(self, mock_const, mock_paths):
        """
        BUILD: Mock constants, paths, and connected client.
        OPERATE: Call _system_status_loop once.
        CHECK: Assert status messages are queued for publishing.
        """
        mock_const.MQTT_BROKER_ADDRESS = "broker.local"
        mock_const.MQTT_BROKER_PORT = 1883
        mock_paths.GLOBAL_PROJECT_ROOT = "/root"
        self.mock_client.is_connected.return_value = True
        
        # Break loop after first iteration
        self.manager._is_running = True
        with patch('time.sleep', side_effect=lambda x: setattr(self.manager, '_is_running', False)):
            self.manager._system_status_loop()
            
        # Should have queued connection status and paths
        # Note: _publish_async adds to queue
        self.assertGreaterEqual(self.manager._publish_queue.qsize(), 2)
        
        # Check first item in queue (Connection Status)
        item = self.manager._publish_queue.get()
        self.assertEqual(item[0], "OPEN-AIR/System/Status/Broker/Connection")
        payload = orjson.loads(item[1])
        self.assertEqual(payload["val"], "ONLINE")

if __name__ == '__main__':
    unittest.main()
