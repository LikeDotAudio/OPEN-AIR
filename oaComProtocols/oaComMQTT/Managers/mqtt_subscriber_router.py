# Managers/mqtt_subscriber_router.py
# Author: Anthony Peter Kuzub
# Version: 20260331.2350.1
#
# Description: Manages MQTT subscriptions via high-performance Rust MqttRouter.

import threading
from typing import Any, Callable, Dict, List, Set, Union
from oaLogging.Core.logger import MQTT_LOGGER
from loguru import logger
import inspect
from oaLogging.Methods.matrix_gate import matrix_log

from oaConfigurationManager.FileReaders.config_reader import Config
from ..Core.mqtt_message import MqttMessage
from ..Core.mqtt_router import MqttRouter

app_constants = Config.get_instance()
LOCAL_DEBUG = False

class MqttSubscriberRouter:
    """
    Optimized MQTT routing engine using PURE RUST core.
    Bridges the async aiomqtt client with synchronous application callbacks.
    """
    def __init__(self):
        # High-performance Rust backend
        self.router = MqttRouter()
        
        self._client = None
        self._base_topic = app_constants.MQTT_BASE_TOPIC
        
        # --- Namespace Split: Default global roots ---
        self._roots = {
            "Cmd": f"{self._base_topic}/Cmd/#",
            "Tx": f"{self._base_topic}/Tx/#",
            "Assets": f"{self._base_topic}/Assets/#",
            "Spectrum": f"{self._base_topic}/Spectrum/#",
            "Status": f"{self._base_topic}/System/Status/#",
            "Monitor": f"{self._base_topic}/System/Monitor/#",
            "Control": f"{self._base_topic}/System/Control/#"
        }
        
        # Track what we've actually asked the broker for
        self._active_broker_subscriptions: Set[str] = set()
        self._lock = threading.Lock() # For broker subscription sync

    def set_client(self, client):
        self._client = client

    def subscribe_to_topic(self, topic_filter: str, callback_func: Callable[[MqttMessage], None]):
        """Registers a callback for a topic filter via Rust Router."""
        matrix_log("comms", "mqtt", "subscribe_to_topic", f"Subscribing to {topic_filter}", "DEBUG")
            
        self.router.subscribe(topic_filter, callback_func)
        
        with self._lock:
            # Determining global root logic
            if topic_filter.startswith(f"{self._base_topic}/"):
                root_to_use = None
                if "/Cmd/" in topic_filter: root_to_use = self._roots["Cmd"]
                elif "/Tx/" in topic_filter: root_to_use = self._roots["Tx"]
                elif "/Assets/" in topic_filter: root_to_use = self._roots["Assets"]
                elif "/Spectrum/" in topic_filter: root_to_use = self._roots["Spectrum"]
                elif "/Status/" in topic_filter: root_to_use = self._roots["Status"]
                elif "/Monitor/" in topic_filter: root_to_use = self._roots["Monitor"]
                elif "/Control/" in topic_filter: root_to_use = self._roots["Control"]
                
                # ⚡ OPTIMIZATION: If it matches a root, use the root. 
                # Otherwise, subscribe to the specific filter.
                sub_target = root_to_use or topic_filter
                
                if sub_target not in self._active_broker_subscriptions:
                    self._active_broker_subscriptions.add(sub_target)
                    from .mqtt_connection import MqttConnectionManager
                    MqttConnectionManager().subscribe(sub_target)
                return

            if topic_filter not in self._active_broker_subscriptions:
                self._active_broker_subscriptions.add(topic_filter)
                from .mqtt_connection import MqttConnectionManager
                MqttConnectionManager().subscribe(topic_filter)

    def unsubscribe_from_topic(self, topic_filter: str, callback_func: Callable[[MqttMessage], None]):
        """Removes a callback. Rust router currently handles per-filter unsubscription."""
        # Simple implementation for POC: remove the whole filter
        # In a refined impl, Rust would handle multiple callbacks per filter.
        self.router.unsubscribe(topic_filter)
        with self._lock:
            self._active_broker_subscriptions.discard(topic_filter)

    def _on_message(self, client, userdata, msg: MqttMessage):
        """Dispatches incoming messages using the Rust router."""
        topic = msg.topic

        # 1. SPECIAL ROUTING: Yak Monitor
        if "yak" in topic.lower():
            from oaTranslator.Managers.yak_trigger_handler import handle_yak_monitor_traffic
            handle_yak_monitor_traffic(msg)

        # 2. RUST MATCHING (O(1) exact, optimized wildcards)
        callbacks_to_invoke = self.router.match_topic(topic)

        # ⚡ THREAD SAFETY: Call callbacks outside any Python locks
        for callback_func in callbacks_to_invoke:
            try:
                callback_func(msg)
            except Exception:
                MQTT_LOGGER.exception(f"Error in MQTT callback for topic {topic}")

    def get_on_message_callback(self):
        return self._on_message

    async def resubscribe_all_topics(self, client):
        """Async resubscription for global roots and external filters."""
        with self._lock:
            # ⚡ RESILIENCE: We must re-subscribe to everything that was previously
            # active to ensure continuity across network interruptions.
            subscriptions_to_restore = list(self._active_broker_subscriptions)
            
            # Ensure the core roots are always present in the restoration list
            for root in self._roots.values():
                if root not in subscriptions_to_restore:
                    subscriptions_to_restore.append(root)
            
            self._active_broker_subscriptions.clear()
            for root in subscriptions_to_restore:
                try:
                    await client.subscribe(root)
                    self._active_broker_subscriptions.add(root)
                    matrix_log("comms", "mqtt", "resubscribe_all_topics", f"aiomqtt: Restored subscription to {root}", "DEBUG")
                except Exception as e:
                    MQTT_LOGGER.error(f"aiomqtt: Failed to restore subscription to {root}: {e}")
        
        matrix_log("comms", "mqtt", "resubscribe_all_topics", "aiomqtt: All topics resubscribed.", "DEBUG")
