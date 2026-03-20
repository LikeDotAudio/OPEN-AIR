# oaComMQTT/Workers/mqtt_async_worker.py
# Background worker for handling asynchronous aiomqtt operations.

import asyncio
import aiomqtt
import queue
from loguru import logger
from ..Core.mqtt_message import MqttMessage
from ..Constants.mqtt_config import TOPIC_STATUS, PAYLOAD_OFFLINE, WORKER_KICK_TIMEOUT

class MqttAsyncWorker:
    """Handles the async MQTT loop and traffic management."""

    def __init__(self, manager):
        self.manager = manager
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
                logger.success("🚀🆗✅ [SUCCESS] aiomqtt: Connected to broker.")
                
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
            logger.error(f"🚀🚫🛑 [MQTT] Worker failure: {e}")
        finally:
            self.manager._connected = False
            self.manager.client = None

    async def _receiver_task(self, client):
        """Ingests messages from the broker."""
        try:
            async for message in client.messages:
                if self.manager.on_message_callback:
                    msg = MqttMessage(
                        topic=str(message.topic),
                        payload=message.payload,
                        qos=message.qos,
                        retain=message.retain
                    )
                    self.manager.on_message_callback(client, None, msg)
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
                while not self.manager._subscribe_queue.empty():
                    job = self.manager._subscribe_queue.get_nowait()
                    try:
                        await client.subscribe(job["topic"], qos=job["qos"])
                    except Exception as e:
                        logger.error(f"🚀🚫🛑 [MQTT] Subscribe Error: {e}")
                    finally:
                        with self.manager._pending_lock:
                            self.manager._pending_subscriptions.discard(job["topic"])
                
                # 2. Publications
                while not self.manager._publish_queue.empty():
                    item = self.manager._publish_queue.get_nowait()
                    topic, payload, qos, retain = self._parse_publish_item(item)
                    try:
                        await client.publish(topic, payload=payload, qos=qos, retain=retain)
                    except Exception as e:
                        logger.error(f"🚀🚫🛑 [MQTT] Publish Error: {e}")
        except asyncio.CancelledError: pass

    def _parse_publish_item(self, item):
        if isinstance(item, tuple): return item
        if isinstance(item, MqttMessage): return item.topic, item.payload, item.qos, item.retain
        return item.get("topic"), item.get("payload"), item.get("qos", 0), item.get("retain", False)
