import inspect
from oaLogging.Methods.matrix_gate import matrix_log
# Workers/mqtt_async_worker.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Background worker for handling asynchronous aiomqtt operations.

import asyncio
import aiomqtt
import queue

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = False
from oaLogging.Core.logger import MQTT_LOGGER
from loguru import logger
from ..Core.mqtt_message import MqttMessage
from ..Constants.mqtt_config import TOPIC_STATUS, PAYLOAD_OFFLINE, WORKER_KICK_TIMEOUT

class MqttAsyncWorker:
    """Handles the async MQTT loop and traffic management."""

    def __init__(self, manager, queue_manager):
        """
        Initializes the async worker.
        
        Args:
            manager: The MqttConnectionManager instance (facade).
            queue_manager: The MqttQueueManager instance for inbound/outbound traffic.
        """
        self.manager = manager
        self.queue_manager = queue_manager
        self.loop = None
        self.stop_event = None
        self.kick_event = None
        self.client = None

    async def run(self):
        """Main entry point for the async loop."""
        self.loop = asyncio.get_running_loop()
        self.stop_event = asyncio.Event()
        self.kick_event = asyncio.Event()
        
        # Configure client
        kwargs = {
            "hostname": self.manager.broker_address,
            "port": self.manager.broker_port,
            "timeout": 10,
            "will": aiomqtt.Will(TOPIC_STATUS, payload=PAYLOAD_OFFLINE, qos=1, retain=True)
        }
        
        if self.manager.username and self.manager.password:
            kwargs["username"] = self.manager.username
            kwargs["password"] = self.manager.password

        try:
            async with aiomqtt.Client(**kwargs) as client:
                self.client = client
                self.manager.client = client
                self.manager._connected = True
                if LOCAL_DEBUG:
                    matrix_log("comms", "mqtt", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "aiomqtt: Connected to broker.", "SUCCESS")
                
                if self.manager.subscriber_router:
                    await self.manager.subscriber_router.resubscribe_all_topics(client)

                # Tasks
                receiver = asyncio.create_task(self._receiver_task(client))
                worker = asyncio.create_task(self._queue_task(client))
                stop = asyncio.create_task(self.stop_event.wait())

                done, pending = await asyncio.wait(
                    [receiver, worker, stop],
                    return_when=asyncio.FIRST_COMPLETED
                )

                for t in pending: t.cancel()
                await asyncio.gather(*pending, return_exceptions=True)
                
        except Exception as e:
            MQTT_LOGGER.error(f"Worker failure: {e}")
        finally:
            self.manager._connected = False
            self.manager.client = None

    async def _receiver_task(self, client):
        """Ingests messages from the broker."""
        try:
            async for message in client.messages:
                if self.manager.on_message_callback:
                    message = MqttMessage(
                        topic=str(message.topic),
                        payload=message.payload,
                        qos=message.qos,
                        retain=message.retain
                    )
                    self.manager.on_message_callback(client, None, message)
        except asyncio.CancelledError: pass

    async def _queue_task(self, client):
        """Processes outbound publish and subscribe queues."""
        try:
            while not self.stop_event.is_set():
                try:
                    await asyncio.wait_for(self.kick_event.wait(), timeout=WORKER_KICK_TIMEOUT)
                except asyncio.TimeoutError: pass
                
                self.kick_event.clear()
                if self.stop_event.is_set(): break

                # 1. Subscriptions
                while True:
                    job = self.queue_manager.get_subscribe_request()
                    if job is None: break
                    
                    try:
                        await client.subscribe(job["topic"], qos=job["qos"])
                    except Exception as e:
                        MQTT_LOGGER.error(f"aiomqtt: Subscribe Error: {e}")
                    finally:
                        self.queue_manager.task_done("subscribe")
                        self.queue_manager.remove_pending_subscription(job["topic"])
                
                # 2. Publications
                while True:
                    item = self.queue_manager.get_publish_message()
                    if item is None: break
                    
                    topic, payload, qos, retain = self._parse_publish_item(item)
                    try:
                        await client.publish(topic, payload=payload, qos=qos, retain=retain)
                    except Exception as e:
                        MQTT_LOGGER.error(f"aiomqtt: Publish Error: {e}")
                    finally:
                        self.queue_manager.task_done("publish")

        except asyncio.CancelledError: pass

    def _parse_publish_item(self, item):
        """Standardizes publish items and encodes payloads for aiomqtt."""
        if isinstance(item, tuple):
            topic, payload, qos, retain = item
        elif isinstance(item, MqttMessage):
            topic, payload, qos, retain = item.topic, item.payload, item.qos, item.retain
        else:
            topic = item.get("topic")
            payload = item.get("payload")
            qos = item.get("qos", 0)
            retain = item.get("retain", False)
            
        # ⚡ PROTOCOL ALIGNMENT: aiomqtt expects str, bytes, or None
        if isinstance(payload, (dict, list)):
            import orjson
            # 🛡️ ROBUSTNESS: Use default=str to handle pathlib.Path and other non-JSON types
            payload = orjson.dumps(payload, default=str)
        elif isinstance(payload, bytes):
            pass
        elif payload is not None and not isinstance(payload, str):
            payload = str(payload)
            
        return topic, payload, qos, retain
