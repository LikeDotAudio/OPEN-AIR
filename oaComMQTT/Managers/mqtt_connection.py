import inspect
from oaLogging.Methods.matrix_gate import matrix_log
# Managers/mqtt_connection.py
# Author: Anthony Peter Kuzub
# Version: 1.1.0
#
# Description: High-level singleton manager for MQTT client lifecycle.
#              Provides a synchronous facade over an asynchronous worker.

import asyncio
import threading
from typing import Optional, Callable

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True
from oaLogging.Core.logger import MQTT_LOGGER

from oaConfiguration.FileReaders.config_reader import Config
from ..Core.mqtt_message import MqttMessage
from ..Workers.mqtt_async_worker import MqttAsyncWorker
from ..Core.mqtt_queue_manager import MqttQueueManager

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
        
        # Instantiate the Queue Manager (Single instance)
        # We pass 'self' as the async_worker_ref. 
        # MqttQueueManager will use our loop/kick_event properties.
        self.queue_manager = MqttQueueManager(async_worker_ref=self)

        # Threading & Worker
        self._thread = None
        self._worker: Optional[MqttAsyncWorker] = None

    @property
    def loop(self):
        """Delegates to the active worker's event loop."""
        return self._worker.loop if self._worker else None

    @property
    def kick_event(self):
        """Delegates to the active worker's kick event."""
        return self._worker.kick_event if self._worker else None

    @property
    def stop_event(self):
        """Delegates to the active worker's stop event."""
        return self._worker.stop_event if self._worker else None

    def is_connected(self):
        """Returns True if the worker is currently connected to the broker."""
        return self._connected

    def get_client_instance(self):
        """shim for backward compatibility. Returns self because we implement publish()."""
        return self

    def publish(self, topic, payload=None, qos=0, retain=False):
        """Thread-safe non-blocking publish (enqueues message)."""
        self.queue_manager.put_publish_message(topic, payload, qos, retain)

    def subscribe(self, topic, qos=0, on_message_callback=None):
        """Thread-safe non-blocking subscribe (enqueues request)."""
        if on_message_callback:
            if self.subscriber_router:
                self.subscriber_router.subscribe_to_topic(topic, on_message_callback)
            else:
                MQTT_LOGGER.warning(f"MQTT: Subscribe with callback for {topic} but no subscriber_router set.")
                self.queue_manager.put_subscribe_request(topic, qos)
        else:
            self.queue_manager.put_subscribe_request(topic, qos)

    def connect_to_broker(self, address=None, port=None, on_message_callback=None, subscriber_router=None):
        """Starts the background worker thread and connects to the broker."""
        if self._thread and self._thread.is_alive(): 
            MQTT_LOGGER.warning("MQTT: Connection attempt while already running.")
            return
        
        self.broker_address = address or app_constants.MQTT_BROKER_ADDRESS
        self.broker_port = port or app_constants.MQTT_BROKER_PORT
        
        # ⚡ ARCHITECTURAL FIX: If sub_router is provided but no callback is set, 
        # use the router's callback by default to ensure messages are routed.
        if subscriber_router and not on_message_callback:
            on_message_callback = subscriber_router.get_on_message_callback()
            
        self.on_message_callback = on_message_callback
        self.subscriber_router = subscriber_router

        self._thread = threading.Thread(target=self._run_worker_thread, daemon=True, name="MQTT-ConnectionWorker")
        self._thread.start()

    def _run_worker_thread(self):
        """Background thread entry point. Manages the asyncio event loop."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Instantiate worker with shared manager and queue_manager
        self._worker = MqttAsyncWorker(manager=self, queue_manager=self.queue_manager)
        
        try:
            loop.run_until_complete(self._worker.run())
        except Exception as e:
            MQTT_LOGGER.error(f"MQTT: Thread Error: {e}")
        finally:
            loop.close()
            self._connected = False
            self._worker = None

    def disconnect(self):
        """Gracefully signals the worker to stop."""
        if self.loop and self.stop_event:
            self.loop.call_soon_threadsafe(self.stop_event.set)
        if LOCAL_DEBUG:
            matrix_log("core", "mqtt", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "MQTT: Disconnection initiated.", "DEBUG")
