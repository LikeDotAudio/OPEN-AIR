# Core/mqtt_queue_manager.py
# Author: Gemini (Refactored from MqttConnectionManager)
# Version: 20260324.1.0
#
# Description: Manages message queues for MQTT publishing and subscribing,
#              providing thread-safe operations.

import queue
import threading
from typing import Optional, Callable

# Standard Debug Logging Setup
LOCAL_DEBUG = False
from oaLogging.Core.logger import MQTT_LOGGER

class MqttQueueManager:
    """
    Manages message queues for MQTT publishing and subscribing,
    providing thread-safe operations and coordinating with an async worker.
    """

    def __init__(self, async_worker_ref):
        """
        Initializes the queue manager.
        
        Args:
            async_worker_ref: A reference to the MqttAsyncWorker instance.
                              This is needed to signal the worker for pending operations.
        """
        self._async_worker = async_worker_ref
        
        # Internal Queues & State
        self._publish_queue = queue.Queue()
        self._subscribe_queue = queue.Queue()
        self._pending_subscriptions = set()
        self._pending_lock = threading.Lock() # Lock for managing pending subscriptions

    def kick_worker(self):
        """Signals the async worker to process pending queue items."""
        if self._async_worker and self._async_worker.loop and self._async_worker.kick_event:
            self._async_worker.loop.call_soon_threadsafe(self._async_worker.kick_event.set)

    def put_publish_message(self, topic, payload=None, qos=0, retain=False):
        """Adds a message to the publish queue."""
        # Filter out internal monitor topics to avoid loop or unnecessary traffic
        if "/System/Monitor/" in str(topic): return
        self._publish_queue.put((topic, payload, qos, retain))
        self.kick_worker()

    def put_subscribe_request(self, topic, qos=0):
        """Adds a subscription request to the queue, ensuring uniqueness."""
        with self._pending_lock:
            if topic in self._pending_subscriptions: return
            self._pending_subscriptions.add(topic)
        self._subscribe_queue.put({"topic": topic, "qos": qos})
        self.kick_worker()

    def get_publish_message(self):
        """Retrieves a message from the publish queue. Returns None if empty."""
        try:
            return self._publish_queue.get_nowait()
        except queue.Empty:
            return None

    def get_subscribe_request(self):
        """Retrieves a subscription request from the queue. Returns None if empty."""
        try:
            return self._subscribe_queue.get_nowait()
        except queue.Empty:
            return None

    def task_done(self, queue_type):
        """Marks a task as done for the specified queue."""
        if queue_type == "publish":
            self._publish_queue.task_done()
        elif queue_type == "subscribe":
            self._subscribe_queue.task_done()

    def remove_pending_subscription(self, topic):
        """Removes a topic from the set of pending subscriptions."""
        with self._pending_lock:
            if topic in self._pending_subscriptions:
                self._pending_subscriptions.remove(topic)
