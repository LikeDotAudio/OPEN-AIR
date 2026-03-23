# oaComMQTT/Tests/test_mqtt_async_worker.py
# Author: Gemini (Collaborator)
# Version: 20260323.0000.1
#
# Description: Tests for the MqttAsyncWorker class.

import asyncio
import unittest
from unittest.mock import MagicMock, AsyncMock, patch
import queue
import aiomqtt

from oaComMQTT.Workers.mqtt_async_worker import MqttAsyncWorker
from oaComMQTT.Core.mqtt_message import MqttMessage

class TestMqttAsyncWorker(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.mock_manager = MagicMock()
        self.mock_manager.broker_address = "localhost"
        self.mock_manager.broker_port = 1883
        self.mock_manager.username = None
        self.mock_manager.password = None
        self.mock_manager._connected = False
        self.mock_manager.subscriber_router = AsyncMock()
        self.mock_manager._subscribe_queue = queue.Queue()
        self.mock_manager._publish_queue = queue.Queue()
        self.mock_manager._pending_subscriptions = set()
        self.mock_manager._pending_lock = MagicMock() # Lock context manager won't directly work with standard mock, we can just replace the lock with a dummy context manager

        # Fake lock context manager
        class DummyLock:
            def __enter__(self): pass
            def __exit__(self, exc_type, exc_val, exc_tb): pass
        self.mock_manager._pending_lock = DummyLock()
        
        self.worker = MqttAsyncWorker(self.mock_manager)

    def test_parse_publish_item(self):
        """Test the _parse_publish_item method correctly parses different formats."""
        # Tuple
        item_tuple = ("test/topic", b"payload", 1, True)
        self.assertEqual(self.worker._parse_publish_item(item_tuple), item_tuple)

        # MqttMessage
        msg = MqttMessage("test/topic", b"payload", 2, False)
        self.assertEqual(self.worker._parse_publish_item(msg), ("test/topic", b"payload", 2, False))

        # Dict
        item_dict = {"topic": "test/topic", "payload": b"payload", "qos": 1, "retain": True}
        self.assertEqual(self.worker._parse_publish_item(item_dict), ("test/topic", b"payload", 1, True))

        # Dict with defaults
        item_dict_default = {"topic": "test/topic", "payload": b"payload"}
        self.assertEqual(self.worker._parse_publish_item(item_dict_default), ("test/topic", b"payload", 0, False))

    async def test_receiver_task(self):
        """Test _receiver_task consumes messages and calls manager's callback."""
        mock_client = AsyncMock()
        
        # Create a mock message iterator
        class MockMessageIterator:
            def __init__(self):
                self.messages = [
                    MagicMock(topic="test/topic1", payload=b"payload1", qos=0, retain=False),
                    MagicMock(topic="test/topic2", payload=b"payload2", qos=1, retain=True)
                ]
            def __aiter__(self): return self
            async def __anext__(self):
                if not self.messages:
                    raise StopAsyncIteration
                return self.messages.pop(0)

        mock_client.messages = MockMessageIterator()
        
        self.mock_manager.on_message_callback = MagicMock()
        
        task = asyncio.create_task(self.worker._receiver_task(mock_client))
        await asyncio.sleep(0.1) # Let the task run briefly
        task.cancel() # Cancel to avoid infinite loop (though iterator stops)
        
        # Should have called callback twice
        self.assertEqual(self.mock_manager.on_message_callback.call_count, 2)
        
        # Check args of first call
        args, _ = self.mock_manager.on_message_callback.call_args_list[0]
        self.assertEqual(args[0], mock_client) # client
        self.assertIsNone(args[1])             # userdata (None)
        self.assertIsInstance(args[2], MqttMessage)
        self.assertEqual(args[2].topic, "test/topic1")
        self.assertEqual(args[2].payload, b"payload1")

    async def test_queue_task_subscriptions(self):
        """Test _queue_task processes subscriptions."""
        mock_client = AsyncMock()
        self.worker.stop_event = asyncio.Event()
        self.worker.kick_event = asyncio.Event()

        # Add a subscription job
        self.mock_manager._subscribe_queue.put({"topic": "test/sub", "qos": 1})
        self.mock_manager._pending_subscriptions.add("test/sub")
        
        self.worker.kick_event.set() # Kick to process

        # Run for a tiny bit
        task = asyncio.create_task(self.worker._queue_task(mock_client))
        await asyncio.sleep(0.1)
        self.worker.stop_event.set()
        await task

        mock_client.subscribe.assert_called_once_with("test/sub", qos=1)
        self.assertNotIn("test/sub", self.mock_manager._pending_subscriptions)

    async def test_queue_task_publications(self):
        """Test _queue_task processes publications."""
        mock_client = AsyncMock()
        self.worker.stop_event = asyncio.Event()
        self.worker.kick_event = asyncio.Event()

        # Add a publication job
        self.mock_manager._publish_queue.put({"topic": "test/pub", "payload": b"data", "qos": 0, "retain": False})
        
        self.worker.kick_event.set() # Kick to process

        # Run for a tiny bit
        task = asyncio.create_task(self.worker._queue_task(mock_client))
        await asyncio.sleep(0.1)
        self.worker.stop_event.set()
        await task

        mock_client.publish.assert_called_once_with("test/pub", payload=b"data", qos=0, retain=False)

if __name__ == '__main__':
    unittest.main()
