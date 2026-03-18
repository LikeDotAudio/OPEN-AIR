# mqtt/mqtt_connection_manager.py
#
# Manages the singleton MQTT client connection using aiomqtt (asyncio wrapper for paho).
# Bridges the async MQTT loop with the synchronous Tkinter application using a background thread.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
# Version 20260218.AioMqtt.2

import asyncio
import threading
import aiomqtt
import queue
import time
import sys
from typing import Optional, Callable

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True # ⚡ OPTIMIZATION
from oaLogging.logger import initialize_logging, set_log_directory
from loguru import logger

from oaConfiguration.config_reader import Config
from oaComMQTT.mqtt_message import MqttMessage

app_constants = Config.get_instance()

class MqttConnectionManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "initialized"):
            return
        self.client = None
        self.initialized = True
        self.broker_address = None
        self.broker_port = None
        self.on_message_callback: Optional[Callable[[MqttMessage], None]] = None
        self.subscriber_router = None
        
        # Async Bridge State
        self._loop = None
        self._thread = None
        self._stop_event = None # Initialized in loop
        self._connected = False
        self._publish_queue = queue.Queue() # Outbound messages
        self._subscribe_queue = queue.Queue() # Outbound subscriptions
        self._pending_subscriptions = set()
        self._pending_lock = threading.Lock()
        
        # ⚡ OPTIMIZATION: Signal event to wake up the async worker
        self._worker_kick_event: Optional[asyncio.Event] = None

    def is_connected(self):
        return self._connected

    def _kick_worker(self):
        """Signals the async loop that there is work to do."""
        if self._loop and self._worker_kick_event:
            self._loop.call_soon_threadsafe(self._worker_kick_event.set)

    def get_client_instance(self):
        """Returns self as a proxy for publishing and subscribing."""
        return self

    def publish(self, topic, payload=None, qos=0, retain=False):
        """Thread-safe publish proxy."""
        # ⚡ ICE: Completely ignore specific system monitoring topics
        if "/System/Monitor/" in str(topic):
            return

        # ⚡ OPTIMIZATION: Put raw data in queue to avoid early object creation
        self._publish_queue.put((topic, payload, qos, retain))
        self._kick_worker()

    def subscribe(self, topic, qos=0):
        """Thread-safe subscribe proxy. Queues the request for the async loop."""
        with self._pending_lock:
            if topic in self._pending_subscriptions:
                return
            self._pending_subscriptions.add(topic)
            
        self._subscribe_queue.put({
            "topic": topic,
            "qos": qos
        })
        self._kick_worker()

    def connect_to_broker(self, address=None, port=None, on_message_callback=None, subscriber_router=None):
        """Starts the async MQTT loop in a background thread."""
        if self._thread and self._thread.is_alive():
            return

        self.broker_address = address or app_constants.MQTT_BROKER_ADDRESS
        self.broker_port = port or app_constants.MQTT_BROKER_PORT
        self.on_message_callback = on_message_callback
        self.subscriber_router = subscriber_router

        self._thread = threading.Thread(target=self._run_async_loop, daemon=True)
        self._thread.start()

    def _run_async_loop(self):
        """Entry point for the background thread."""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._stop_event = asyncio.Event()
        self._worker_kick_event = asyncio.Event()
        
        # We allow exceptions to bubble up here, which will terminate the thread.
        # In the Partitioned Core, we want the Supervisor to handle restarts.
        try:
            self._loop.run_until_complete(self._mqtt_main_loop())
        except Exception as e:
            # Gravity of Errors: Non-gated failure reporting.
            logger.error(
                f"🚀🚫🛑 [MQTT] ERROR: aiomqtt loop terminated: {e}"
            )
        finally:
            self._loop.close()
            self._connected = False
            if LOCAL_DEBUG:
                logger.debug("📡🔗✅ [MQTT] aiomqtt: Async loop closed.")

    async def _mqtt_main_loop(self):
        """Main async coroutine for handling connection, messages, and traffic."""
        # Configure client
        kwargs = {
            "hostname": self.broker_address,
            "port": self.broker_port,
            "timeout": 10,
            "will": aiomqtt.Will("OPEN-AIR/status", payload="OFFLINE", 
                                 qos=1, retain=True)
        }
        
        if app_constants.MQTT_USERNAME and app_constants.MQTT_PASSWORD:
            kwargs["username"] = app_constants.MQTT_USERNAME
            kwargs["password"] = app_constants.MQTT_PASSWORD

        # Wrap the connection in a try/except to ensure state is updated if it fails to start.
        try:
            async with aiomqtt.Client(**kwargs) as client:
                self.client = client
                self._connected = True
                
                if LOCAL_DEBUG:
                    logger.success("🚀🆗✅ [SUCCESS] aiomqtt: Connected to broker.")
                
                # 1. Re-subscribe existing topics via router
                if self.subscriber_router:
                    await self.subscriber_router.resubscribe_all_topics(client)

                # 2. Start tasks
                receiver_task = asyncio.create_task(self._message_receiver_task(client))
                worker_task = asyncio.create_task(self._queue_worker_task(client))
                stop_waiter = asyncio.create_task(self._stop_event.wait())

                # Wait for any task to finish (e.g. stop event or connection loss)
                done, pending = await asyncio.wait(
                    [receiver_task, worker_task, stop_waiter],
                    return_when=asyncio.FIRST_COMPLETED
                )

                # Cancel remaining tasks
                for task in pending:
                    task.cancel()
                
                # Allow tasks to cleanup
                await asyncio.gather(*pending, return_exceptions=True)
                
                if LOCAL_DEBUG:
                    logger.debug("📡🔗👋 [MQTT] aiomqtt: Disconnecting from broker...")
        except Exception as e:
            self._connected = False
            logger.error(f"🚀🚫🛑 [MQTT] ERROR: aiomqtt main loop error: {e}")

    async def _message_receiver_task(self, client):
        """Listens for incoming messages and dispatches them to the callback."""
        try:
            async for message in client.messages:
                if LOCAL_DEBUG:
                    logger.trace(
                        f"📥📡📥 [MQTT] Received message on {message.topic}"
                    )
                
                if self.on_message_callback:
                    # Wrap in MqttMessage dataclass
                    msg = MqttMessage(
                        topic=str(message.topic),
                        payload=message.payload,
                        qos=message.qos,
                        retain=message.retain
                    )
                    self.on_message_callback(client, None, msg)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            # Gravity of Errors: Non-gated failure reporting.
            logger.error(f"🚀🚫🛑 [MQTT] ERROR: aiomqtt receiver failed: {e}")

    async def _queue_worker_task(self, client):
        """Processes the thread-safe publish and subscribe queues."""
        try:
            while not self._stop_event.is_set():
                # ⚡ OPTIMIZATION: Wait for a signal that there is work to do
                # Use a combined waiter for efficiency
                try:
                    await asyncio.wait_for(
                        self._worker_kick_event.wait(),
                        timeout=5.0
                    )
                except asyncio.TimeoutError:
                    pass
                
                # Clear BEFORE processing to catch signals during the loop
                self._worker_kick_event.clear()
                
                if self._stop_event.is_set():
                    break

                # 1. Process Subscriptions
                while not self._subscribe_queue.empty():
                    try:
                        job = self._subscribe_queue.get_nowait()
                        try:
                            await client.subscribe(job["topic"], qos=job["qos"])
                        except Exception as e:
                            # Gravity of Errors
                            logger.error(
                                f"🚀🚫🛑 [MQTT] ERROR: Subscribe Failed for "
                                f"'{job['topic']}': {e}"
                            )
                        finally:
                            with self._pending_lock:
                                self._pending_subscriptions.discard(job["topic"])
                    except queue.Empty:
                        break
                
                # 2. Process Publications
                while not self._publish_queue.empty():
                    try:
                        item = self._publish_queue.get_nowait()
                        
                        if isinstance(item, tuple):
                            topic, payload, qos, retain = item
                        elif isinstance(item, MqttMessage):
                            topic, payload, qos, retain = item.topic, item.payload, item.qos, item.retain
                        else:
                            # Legacy dict support
                            topic = item.get("topic")
                            payload = item.get("payload")
                            qos = item.get("qos", 0)
                            retain = item.get("retain", False)

                        # ⚡ OPTIMIZATION: Lazy evaluation to avoid string work
                        if LOCAL_DEBUG:
                            def _lazy_log(t=topic, p=payload):
                                p_str = p.decode('utf-8', errors='replace') if isinstance(p, (bytes, bytearray)) else str(p)
                                return f"🚀📤📢 [MQTT] {t} 📨 {p_str[:100]}"
                            logger.opt(lazy=True).trace("{}", _lazy_log)

                        try:
                            await client.publish(
                                topic, 
                                payload=payload, 
                                qos=qos, 
                                retain=retain
                            )
                        except Exception as e:
                            # Gravity of Errors
                            logger.error(
                                f"🚀🚫🛑 [MQTT] ERROR: Publish Failed for "
                                f"'{topic}': {e}"
                            )
                    except queue.Empty:
                        break

        except asyncio.CancelledError:
            pass
        except Exception as e:
            # Gravity of Errors: Non-gated failure reporting.
            logger.error(f"🚀🚫🛑 [MQTT] ERROR: aiomqtt worker failed: {e}")

    def disconnect(self):
        """Triggers graceful shutdown of the async loop."""
        if self._stop_event and self._loop:
            self._loop.call_soon_threadsafe(self._stop_event.set)
        if LOCAL_DEBUG:
            logger.debug("📡🔗👋 [MQTT] aiomqtt disconnection initiated.")
