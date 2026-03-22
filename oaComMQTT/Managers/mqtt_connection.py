# Managers/mqtt_connection.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: High-level singleton manager for MQTT client lifecycle.

import asyncio
import threading
import queue
from typing import Optional, Callable
from loguru import logger

from oaConfiguration.FileReaders.config_reader import Config
from ..Core.mqtt_message import MqttMessage
from ..Workers.mqtt_async_worker import MqttAsyncWorker

app_constants = Config.get_instance()

class MqttConnectionManager:
    """Singleton Manager providing a synchronous API for the asynchronous MQTT worker."""
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "initialized"): return
        self.initialized = True
        self.client = None
        self._connected = False
        
        # Connection Config
        self.broker_address = None
        self.broker_port = None
        self.username = app_constants.MQTT_USERNAME
        self.password = app_constants.MQTT_PASSWORD
        
        # Callbacks & Routing
        self.on_message_callback: Optional[Callable[[MqttMessage], None]] = None
        self.subscriber_router = None
        
        # Internal Queues & State
        self._publish_queue = queue.Queue()
        self._subscribe_queue = queue.Queue()
        self._pending_subscriptions = set()
        self._pending_lock = threading.Lock()
        
        # Threading & Worker
        self._thread = None
        self._worker: Optional[MqttAsyncWorker] = None

    def is_connected(self):
        return self._connected

    def get_client_instance(self):
        return self

    def _kick_worker(self):
        if self._worker and self._worker.loop and self._worker.kick_event:
            self._worker.loop.call_soon_threadsafe(self._worker.kick_event.set)

    def publish(self, topic, payload=None, qos=0, retain=False):
        """Thread-safe publish."""
        if "/System/Monitor/" in str(topic): return
        self._publish_queue.put((topic, payload, qos, retain))
        self._kick_worker()

    def subscribe(self, topic, qos=0):
        """Thread-safe subscribe."""
        with self._pending_lock:
            if topic in self._pending_subscriptions: return
            self._pending_subscriptions.add(topic)
        self._subscribe_queue.put({"topic": topic, "qos": qos})
        self._kick_worker()

    def connect_to_broker(self, address=None, port=None, on_message_callback=None, subscriber_router=None):
        if self._thread and self._thread.is_alive(): return
        
        self.broker_address = address or app_constants.MQTT_BROKER_ADDRESS
        self.broker_port = port or app_constants.MQTT_BROKER_PORT
        self.on_message_callback = on_message_callback
        self.subscriber_router = subscriber_router

        self._thread = threading.Thread(target=self._run_worker_thread, daemon=True)
        self._thread.start()

    def _run_worker_thread(self):
        """Background thread entry point."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self._worker = MqttAsyncWorker(self)
        try:
            loop.run_until_complete(self._worker.run())
        except Exception as e:
            logger.error(f"🚀🚫🛑 [MQTT] Thread Error: {e}")
        finally:
            loop.close()
            self._connected = False

    def disconnect(self):
        """Gracefully signals the worker to stop."""
        if self._worker and self._worker.loop and self._worker.stop_event:
            self._worker.loop.call_soon_threadsafe(self._worker.stop_event.set)
        logger.debug("📡🔗👋 [MQTT] Disconnection initiated.")
