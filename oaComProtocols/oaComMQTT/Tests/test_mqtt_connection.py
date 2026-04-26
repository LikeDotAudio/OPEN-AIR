# oaComProtocols.oaComMQTT/Tests/test_mqtt_connection.py
# Author: Gemini (Collaborator)
# Version: 20260323.0000.1
#
# Description: Tests for the MqttConnectionManager singleton class.

import queue
import unittest
from unittest.mock import MagicMock, patch

from oaComProtocols.oaComMQTT.Managers.mqtt_connection import MqttConnectionManager


class TestMqttConnectionManager(unittest.TestCase):

    def setUp(self):
        """Reset the singleton instance for each test to ensure isolation."""
        MqttConnectionManager._instance = None
        self.manager = MqttConnectionManager()

    def test_singleton_behavior(self):
        """Verify that MqttConnectionManager is a true singleton."""
        manager2 = MqttConnectionManager()
        self.assertIs(self.manager, manager2)

    def test_initialization(self):
        """Verify the initial state of the manager."""
        self.assertFalse(self.manager.is_connected())
        self.assertIsNone(self.manager.client)
        self.assertIsInstance(self.manager.queue_manager._publish_queue, queue.Queue)
        self.assertIsInstance(self.manager.queue_manager._subscribe_queue, queue.Queue)

    @patch('oaComProtocols.oaComMQTT.Managers.mqtt_connection.MqttAsyncWorker')
    @patch('threading.Thread')
    def test_connect_to_broker(self, MockThread, MockWorker):
        """
        BUILD: Mock MqttAsyncWorker and threading.Thread.
        OPERATE: Call connect_to_broker.
        CHECK: Assert the background thread is started with correct parameters.
        """
        mock_callback = MagicMock()
        mock_router = MagicMock()

        self.manager.connect_to_broker(
            address="1.2.3.4",
            port=1883,
            on_message_callback=mock_callback,
            subscriber_router=mock_router
        )

        self.assertEqual(self.manager.broker_address, "1.2.3.4")
        self.assertEqual(self.manager.broker_port, 1883)
        self.assertEqual(self.manager.on_message_callback, mock_callback)
        self.assertEqual(self.manager.subscriber_router, mock_router)

        MockThread.assert_called_once()
        args, kwargs = MockThread.call_args
        self.assertEqual(kwargs['target'], self.manager._run_worker_thread)
        MockThread.return_value.start.assert_called_once()

    def test_publish_queues_message(self):
        """
        BUILD: Mock worker with loop and event.
        OPERATE: Call publish.
        CHECK: Assert message is added to the queue and worker is 'kicked'.
        """
        mock_worker = MagicMock()
        mock_worker.loop = MagicMock()
        mock_worker.kick_event = MagicMock()
        self.manager._worker = mock_worker

        self.manager.publish("test/topic", payload=b"data", qos=1, retain=True)

        self.assertEqual(self.manager.queue_manager._publish_queue.qsize(), 1)
        item = self.manager.queue_manager._publish_queue.get()
        self.assertEqual(item, ("test/topic", b"data", 1, True))

        # Verify worker kick
        mock_worker.loop.call_soon_threadsafe.assert_called_with(mock_worker.kick_event.set)

    def test_subscribe_queues_message(self):
        """
        BUILD: Mock worker.
        OPERATE: Call subscribe.
        CHECK: Assert topic is added to pending and queue, and worker is kicked.
        """
        mock_worker = MagicMock()
        mock_worker.loop = MagicMock()
        mock_worker.kick_event = MagicMock()
        self.manager._worker = mock_worker

        self.manager.subscribe("test/sub", qos=0)

        self.assertIn("test/sub", self.manager.queue_manager._pending_subscriptions)
        self.assertEqual(self.manager.queue_manager._subscribe_queue.qsize(), 1)
        item = self.manager.queue_manager._subscribe_queue.get()
        self.assertEqual(item, {"topic": "test/sub", "qos": 0})

        # Duplicate subscribe should be ignored
        self.manager.subscribe("test/sub", qos=0)
        self.assertEqual(self.manager.queue_manager._subscribe_queue.qsize(), 0)

    def test_disconnect_signals_worker(self):
        """
        BUILD: Mock worker with stop_event.
        OPERATE: Call disconnect.
        CHECK: Assert stop_event is set via loop.
        """
        mock_worker = MagicMock()
        mock_worker.loop = MagicMock()
        mock_worker.stop_event = MagicMock()
        self.manager._worker = mock_worker

        self.manager.disconnect()

        mock_worker.loop.call_soon_threadsafe.assert_called_with(mock_worker.stop_event.set)

    @patch('oaComProtocols.oaComMQTT.Managers.mqtt_connection.MQTT_LOGGER')
    @patch('threading.Thread')
    def test_multiple_connections_are_handled(self, MockThread, MockLogger):
        """
        BUILD: Mock threading.Thread and the module's logger.
        OPERATE: Call connect_to_broker twice, with the mock thread 'alive'.
        CHECK: Assert that the thread is only started once and a warning is logged.
        """
        # --- First call ---
        self.manager.connect_to_broker(address="1.2.3.4", port=1883)

        # Assert the first call starts the thread
        MockThread.assert_called_once()
        MockThread.return_value.start.assert_called_once()

        # --- Second call ---
        # Simulate the thread being alive
        self.manager._thread = MockThread.return_value
        MockThread.return_value.is_alive.return_value = True

        self.manager.connect_to_broker(address="1.2.3.4", port=1883)

        # Assert start was NOT called again
        MockThread.return_value.start.assert_called_once()

        # Assert that the warning was logged
        MockLogger.warning.assert_called_once_with("MQTT: Connection attempt while already running.")

if __name__ == '__main__':
    unittest.main()
