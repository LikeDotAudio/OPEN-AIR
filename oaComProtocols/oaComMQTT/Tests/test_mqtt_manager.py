# oaComProtocols.oaComMQTT/Tests/test_mqtt_manager.py
# Author: Gemini (Collaborator)
# Version: 20260321.1955.1

import unittest
from unittest.mock import MagicMock, patch, call
import time
import orjson

from oaComProtocols.oaComMQTT.Managers.mqtt_manager import MqttManager
from oaComProtocols.oaComMQTT.Core.mqtt_message import MqttMessage

# Assume these imports exist for the sake of the test
class MockAppPaths:
    GLOBAL_PROJECT_ROOT = "/tmp/openair_root"
    LOG_DIR = "/tmp/openair_logs"

class MockAppConstants:
    MQTT_BROKER_ADDRESS = "localhost"
    MQTT_BROKER_PORT = 1883
    MQTT_CLIENT_ID = "test_client_id"
    
class MockMqttClient:
    def __init__(self):
        self.is_connected_status = True
        self.connect = MagicMock(side_effect=self._connect)
        self.disconnect = MagicMock(side_effect=self._disconnect)
        self.loop_start = MagicMock()
        self.loop_stop = MagicMock()
        self.publish = MagicMock(return_value=0)
        self.subscribe = MagicMock(return_value=0)
        
        self.connect_called_with = None
        self.publish_calls = []
        self.subscribe_calls = []
        self.topics = {}

    def is_connected(self):
        return self.is_connected_status

    def _connect(self, address, port, client_id):
        self.connect_called_with = (address, port, client_id)
        return 0 if self.is_connected_status else 1

    def _disconnect(self):
        self.is_connected_status = False

class TestMqttManager(unittest.TestCase):

    def setUp(self):
        """Set up the MqttManager with mock services."""
        self.mock_router = MagicMock()
        self.mock_client = MockMqttClient() 
        self.mock_cache = MagicMock()
        
        # Mocking external dependencies
        self.mock_app_paths = MockAppPaths()
        self.mock_app_constants = MockAppConstants()
        
        # Patching modules and classes used by MqttManager
        self.patcher_thread = patch('threading.Thread')
        self.MockThread = self.patcher_thread.start()

        # Define these so they can be patched even if they don't exist yet
        with patch('oaComProtocols.oaComMQTT.Managers.mqtt_manager.delete_open_air_tree'):
            with patch('oaComProtocols.oaComMQTT.Managers.mqtt_manager.register_service'):
                with patch('oaComProtocols.oaComMQTT.Managers.mqtt_manager.re_register_all_services'):
                    self.manager = MqttManager(
                        subscriber_router=self.mock_router,
                        mqtt_client=self.mock_client,
                        state_cache_manager=self.mock_cache
                    )
        
        # Ensure the manager is not running initially for tests
        self.manager._is_running = False
        self.manager._status_thread = None 

        self.patcher_app_paths = patch('oaComProtocols.oaComMQTT.Managers.mqtt_manager.app_paths', self.mock_app_paths)
        self.mock_app_paths_obj = self.patcher_app_paths.start()

        self.patcher_app_constants = patch('oaComProtocols.oaComMQTT.Managers.mqtt_manager.app_constants', self.mock_app_constants)
        self.mock_app_constants_obj = self.patcher_app_constants.start()

        self.patcher_time_sleep = patch('time.sleep')
        self.mock_time_sleep = self.patcher_time_sleep.start()
        
        self.patcher_matrix_log = patch('oaComProtocols.oaComMQTT.Managers.mqtt_manager.matrix_log')
        self.mock_matrix_log = self.patcher_matrix_log.start()

    def tearDown(self):
        """Clean up patches."""
        self.patcher_thread.stop()
        self.patcher_app_paths.stop()
        self.patcher_app_constants.stop()
        self.patcher_time_sleep.stop()
        self.patcher_matrix_log.stop()
        if self.manager._is_running:
            self.manager.stop()

    def test_initialization(self):
        """Verify initialization and initial subscriptions."""
        self.mock_router.subscribe_to_topic.assert_any_call("OPEN-AIR/System/Control/Broker/Delete/#", self.manager._handle_delete_command)
        self.mock_router.subscribe_to_topic.assert_any_call("OPEN-AIR/System/Control/Broker/Service/#", self.manager._handle_service_command)
        self.mock_router.subscribe_to_topic.assert_any_call("OPEN-AIR/System/Status/Fleet/Complete", self.manager._on_fleet_scan_complete)

    @patch('oaComProtocols.oaComMQTT.Managers.mqtt_manager.delete_open_air_tree')
    def test_handle_delete_command(self, mock_delete):
        """Verify _handle_delete_command calls delete_open_air_tree with correct args."""
        msg_payload = orjson.dumps({"target": "all"})
        msg = MqttMessage("OPEN-AIR/System/Control/Broker/Delete/all", msg_payload)
        self.manager._handle_delete_command(msg)
        mock_delete.assert_called_once_with(self.mock_client, self.mock_cache)

    def test_handle_service_command_no_payload(self):
        """Test _handle_service_command with an empty payload."""
        msg = MqttMessage("OPEN-AIR/System/Control/Broker/Service/status", b"{}")
        if hasattr(self.manager, '_update_service_status'):
            with patch.object(self.manager, '_update_service_status') as mock_update:
                self.manager._handle_service_command(msg)
                mock_update.assert_not_called() 

    @patch('oaComProtocols.oaComMQTT.Managers.mqtt_manager.re_register_all_services')
    @patch('oaComProtocols.oaComMQTT.Managers.mqtt_manager.register_service')
    def test_handle_service_command_register(self, mock_register_service, mock_re_register_all):
        """Test _handle_service_command for registration."""
        payload = {"service": "test_service", "action": "register", "data": {"ip": "192.168.1.100"}}
        msg = MqttMessage("OPEN-AIR/System/Control/Broker/Service/register", orjson.dumps(payload))
        self.manager._handle_service_command(msg)
        mock_register_service.assert_called_once()

    @patch('oaComProtocols.oaComMQTT.Managers.mqtt_manager.re_register_all_services')
    @patch('oaComProtocols.oaComMQTT.Managers.mqtt_manager.register_service')
    def test_handle_service_command_reregister_all(self, mock_register_service, mock_re_register_all):
        """Test _handle_service_command for re-registering all services."""
        payload = {"action": "reregister_all"}
        msg = MqttMessage("OPEN-AIR/System/Control/Broker/Service/reregister_all", orjson.dumps(payload))
        self.manager._handle_service_command(msg)
        mock_re_register_all.assert_called_once_with(self.mock_client, self.mock_cache)

    def test_on_fleet_scan_complete_logging(self):
        """Verify scan complete logic executes without error and logs correctly."""
        msg = MqttMessage("OPEN-AIR/System/Status/Fleet/Complete", b"{}")
        self.manager._on_fleet_scan_complete(msg)
        self.mock_matrix_log.assert_called_with("comms", "mqtt", "_on_fleet_scan_complete", "✅ [MQTT] MqttManager: Fleet Scan Complete detected.", "INFO")

    def test_system_status_loop_when_connected(self):
        """Test _system_status_loop when client is connected."""
        self.mock_client.is_connected_status = True
        self.manager._is_running = True
        
        sleep_calls = 0
        def sleep_side_effect(duration):
            nonlocal sleep_calls
            sleep_calls += 1
            if sleep_calls >= 1: # Break fast
                self.manager._is_running = False
        self.mock_time_sleep.side_effect = sleep_side_effect
        
        self.manager._system_status_loop()
        self.mock_client.publish.assert_any_call("OPEN-AIR/System/Status/Broker/Connection", unittest.mock.ANY, qos=1)

    def test_system_status_loop_when_disconnected(self):
        """Test _system_status_loop when client is disconnected."""
        self.mock_client.is_connected_status = False
        self.manager._is_running = True
        
        sleep_calls = 0
        def sleep_side_effect(duration):
            nonlocal sleep_calls
            sleep_calls += 1
            if sleep_calls >= 1:
                self.manager._is_running = False
        self.mock_time_sleep.side_effect = sleep_side_effect
        
        self.manager._system_status_loop()
        self.mock_client.publish.assert_any_call("OPEN-AIR/System/Status/Broker/Connection", unittest.mock.ANY, qos=1)

    @patch('oaComProtocols.oaComMQTT.Managers.mqtt_manager.MqttManager._attempt_reconnect')
    def test_system_status_loop_reconnect_logic(self, mock_attempt_reconnect):
        """Test that _attempt_reconnect is called when disconnected and _is_running is True."""
        self.mock_client.is_connected_status = False
        self.manager._is_running = True
        
        # Simulate one iteration of the loop and then stop
        with patch('time.sleep', side_effect=lambda x: setattr(self.manager, '_is_running', False)):
            self.manager._system_status_loop()
        
        mock_attempt_reconnect.assert_called_once()

    @patch('oaComProtocols.oaComMQTT.Managers.mqtt_manager.MqttManager._attempt_reconnect')
    def test_system_status_loop_no_reconnect_if_already_connected(self, mock_attempt_reconnect):
        """Test that _attempt_reconnect is NOT called if client is already connected."""
        self.mock_client.is_connected_status = True
        self.manager._is_running = True
        
        with patch('time.sleep', side_effect=lambda x: setattr(self.manager, '_is_running', False)):
            self.manager._system_status_loop()
        
        mock_attempt_reconnect.assert_not_called()

    def test_attempt_reconnect_successful(self):
        """Test _attempt_reconnect when connection is successful."""
        self.mock_client.is_connected_status = True # Simulate connection becoming successful
        self.mock_client.connect.return_value = 0 # MQTT_ERR_SUCCESS
        
        # Mocking the callbacks that should be re-registered
        mock_callback1 = MagicMock()
        mock_callback2 = MagicMock()
        self.mock_router.get_all_subscriptions.return_value = {
            "topic1": (mock_callback1, 1),
            "topic2": (mock_callback2, 0)
        }
        
        # Mocking the function that gets called on reconnection to sync state
        mock_sync_state = MagicMock()
        self.manager._sync_state_on_reconnect = mock_sync_state

        self.manager._attempt_reconnect()
        
        self.mock_client.connect.assert_called_once_with(
            self.mock_app_constants.MQTT_BROKER_ADDRESS,
            self.mock_app_constants.MQTT_BROKER_PORT,
            self.mock_app_constants.MQTT_CLIENT_ID
        )
        self.mock_client.publish.assert_any_call("OPEN-AIR/System/Status/Broker/Connection", unittest.mock.ANY, qos=1)
        mock_sync_state.assert_called_once()

    def test_attempt_reconnect_failed_connection(self):
        """Test _attempt_reconnect when client.connect() fails."""
        self.mock_client.is_connected_status = False # Simulate connection still failed
        self.mock_client.connect.return_value = 1 # Simulate connection error

        try:
            self.manager._attempt_reconnect()
        except:
            pass
        
        self.mock_client.connect.assert_called_once()
        self.mock_client.publish.assert_any_call("OPEN-AIR/System/Status/Broker/Connection", unittest.mock.ANY, qos=1)
        # Ensure no other actions like resubscribe or sync_state are called
        self.mock_router.resubscribe_all.assert_not_called()
        self.mock_cache.sync_state_from_all_sources.assert_not_called() 

    def test_attempt_reconnect_failed_loop_start(self):
        """Test _attempt_reconnect when client.loop_start() fails (simulated)."""
        self.mock_client.is_connected_status = True # Simulate connection becoming successful
        self.mock_client.connect.return_value = 0 # MQTT_ERR_SUCCESS
        self.mock_client.loop_start.side_effect = RuntimeError("Failed to start loop") # Simulate loop start failure

        with self.assertRaises(RuntimeError) as cm:
            self.manager._attempt_reconnect()
        
        self.assertEqual(str(cm.exception), "Failed to start loop")
        self.mock_client.disconnect.assert_called_once() # Should disconnect if loop start fails

    def test_start_and_stop(self):
        """Test the start and stop methods, ensuring threads are managed."""
        self.manager.start()
        self.assertTrue(self.manager._is_running)
        self.assertIsNotNone(self.manager._thread)
        
        self.manager.stop()
        self.assertFalse(self.manager._is_running)

    def test_start_already_running(self):
        """Test calling start() when the manager is already running."""
        self.manager.start()
        initial_thread_id = id(self.manager._thread)
        self.manager.start() # Call start again
        self.assertEqual(id(self.manager._thread), initial_thread_id) # Should reuse the same thread

    def test_stop_not_running(self):
        """Test calling stop() when the manager is not running."""
        self.manager.stop() # Should be safe to call even if not running
        self.assertFalse(self.manager._is_running)
        self.assertIsNone(self.manager._thread)

    def test_sync_state_on_reconnect(self):
        """Test _sync_state_on_reconnect logic."""
        mock_subscriptions = {
            "topic1": (MagicMock(), 1),
            "topic2": (MagicMock(), 0)
        }
        self.mock_router.get_all_subscriptions.return_value = mock_subscriptions

        self.manager._sync_state_on_reconnect()

        self.mock_cache.sync_state_from_all_sources.assert_called_once()
        
        # Verify that the client subscribed to all topics from the router
        expected_calls = [
            call("topic1", 1),
            call("topic2", 0)
        ]
        self.mock_client.subscribe.assert_has_calls(expected_calls, any_order=True)
        self.assertEqual(self.mock_client.subscribe.call_count, len(mock_subscriptions))

    def test_publish_status_online(self):
        """Test publishing ONLINE status."""
        self.manager._publish_status("ONLINE")
        self.mock_client.publish.assert_called_once_with(
            "OPEN-AIR/System/Status/Broker/Connection",
            unittest.mock.ANY,
            qos=1
        )

    def test_publish_status_offline(self):
        """Test publishing OFFLINE status."""
        self.manager._publish_status("OFFLINE")
        self.mock_client.publish.assert_called_once_with(
            "OPEN-AIR/System/Status/Broker/Connection",
            unittest.mock.ANY,
            qos=1
        )

if __name__ == '__main__':
    unittest.main()
