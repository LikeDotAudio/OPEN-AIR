# mqtt/mqtt_subscriber_router.py
#
# Manages MQTT subscriptions and dispatches incoming messages to registered callbacks.
# Optimized for high-throughput with wildcard-based routing and hash-map dispatch.
# Updated for aiomqtt (asyncio) compatibility.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
# Version 20260218.AioMqtt.1

import paho.mqtt.client as mqtt # Still needed for topic_matches_sub logic
import threading
from typing import Any, Callable, Dict, List, Set, Union

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True
from workers.logger.logger import initialize_logging, set_log_directory
from loguru import logger

from managers.configini.config_reader import Config
from workers.Command_Router.mqtt.mqtt_message import MqttMessage

app_constants = Config.get_instance()

class ThreadSafeMatchCache:
    """Encapsulates a thread-safe cache for MQTT wildcard matches."""
    def __init__(self, limit=1000):
        self._cache: Dict[str, List[Callable[[MqttMessage], None]]] = {}
        self._lock = threading.Lock()
        self._limit = limit

    def get_cached_callbacks(self, topic: str):
        with self._lock:
            return self._cache.get(topic)

    def cache_callbacks(self, topic: str, callbacks: List[Callable[[MqttMessage], None]]):
        with self._lock:
            if len(self._cache) < self._limit:
                self._cache[topic] = callbacks

    def clear(self):
        with self._lock:
            self._cache.clear()

    def __len__(self):
        with self._lock:
            return len(self._cache)

class MqttSubscriberRouter:
    """
    Optimized MQTT routing engine.
    Bridges the async aiomqtt client with synchronous application callbacks.
    """
    def __init__(self):
        # Hash map: topic -> list of callbacks
        self._exact_subscribers: Dict[str, List[Callable[[MqttMessage], None]]] = {}
        # Wildcard list: (filter, list of callbacks)
        self._wildcard_subscribers: List[List[Union[str, List[Callable[[MqttMessage], None]]]]] = []
        
        # ⚡ THREAD SAFETY: Protects subscriber maps during concurrent access
        self._lock = threading.RLock()

        # ⚡ OPTIMIZATION: Cache for wildcard matches to avoid redundant pattern matching
        self._match_cache = ThreadSafeMatchCache(limit=1000)
        
        self._client = None
        
        # ⚡ OPTIMIZATION: Use configured base topic
        self._base_topic = app_constants.MQTT_BASE_TOPIC
        self._root_topic = f"{self._base_topic}/#"
        
        # Track what we've actually asked the broker for to avoid spamming aiomqtt
        self._active_broker_subscriptions: Set[str] = set()

    def set_client(self, client):
        """Sets the MQTT client instance (aiomqtt Client)."""
        self._client = client

    def subscribe_to_topic(self, topic_filter: str, 
                          callback_func: Callable[[MqttMessage], None]):
        """Registers a callback for a topic filter."""
        if LOCAL_DEBUG:
            logger.debug(f"🚀📤📥 [MQTT] Subscribing to {topic_filter}")
            
        # ⚡ Invalidate cache when subscriptions change
        self._match_cache.clear()
        
        with self._lock:
            if "#" in topic_filter or "+" in topic_filter:
                found = False
                for entry in self._wildcard_subscribers:
                    f, cb_list = entry
                    if f == topic_filter:
                        if callback_func not in cb_list:
                            cb_list.append(callback_func)
                        found = True
                        break
                if not found:
                    self._wildcard_subscribers.append([topic_filter, [callback_func]])
            else:
                if topic_filter not in self._exact_subscribers:
                    self._exact_subscribers[topic_filter] = []
                if callback_func not in self._exact_subscribers[topic_filter]:
                    self._exact_subscribers[topic_filter].append(callback_func)
            
            # ⚡ aiomqtt Optimization: Avoid redundant broker subscriptions
            if topic_filter.startswith(f"{self._base_topic}/") or topic_filter == self._root_topic:
                if self._root_topic not in self._active_broker_subscriptions:
                    self._active_broker_subscriptions.add(self._root_topic)
                    from workers.Command_Router.mqtt.mqtt_connection import MqttConnectionManager
                    MqttConnectionManager().subscribe(self._root_topic)
                return

            if topic_filter in self._active_broker_subscriptions:
                return

            self._active_broker_subscriptions.add(topic_filter)
            from workers.Command_Router.mqtt.mqtt_connection import MqttConnectionManager
            MqttConnectionManager().subscribe(topic_filter)

    def unsubscribe_from_topic(self, topic_filter: str, callback_func: Callable[[MqttMessage], None]):
        """Removes a specific callback function from a topic filter."""
        # ⚡ Invalidate cache when subscriptions change
        self._match_cache.clear()
        
        with self._lock:
            if "#" in topic_filter or "+" in topic_filter:
                for i, entry in enumerate(self._wildcard_subscribers):
                    f, cb_list = entry
                    if f == topic_filter:
                        try:
                            cb_list.remove(callback_func)
                            if not cb_list: 
                                self._wildcard_subscribers.pop(i)
                                self._active_broker_subscriptions.discard(topic_filter)
                        except ValueError: pass
                        break
            else:
                if topic_filter in self._exact_subscribers:
                    try:
                        self._exact_subscribers[topic_filter].remove(callback_func)
                        if not self._exact_subscribers[topic_filter]:
                            del self._exact_subscribers[topic_filter]
                            self._active_broker_subscriptions.discard(topic_filter)
                    except ValueError: pass

    def _on_message(self, client, userdata, msg: MqttMessage):
        """
        Sync callback invoked by MqttConnectionManager's async receiver task.
        Runs in the background MQTT thread.
        """
        topic = msg.topic

        # 1. SPECIAL ROUTING: Yak Monitor
        if "yak" in topic.lower():
            from managers.yak.yak_trigger_handler import handle_yak_monitor_traffic
            handle_yak_monitor_traffic(msg)

        with self._lock:
            # 2. FAST DISPATCH: Exact Topic Match (O(1))
            if topic in self._exact_subscribers:
                for callback_func in self._exact_subscribers[topic]:
                    callback_func(msg)

            # 3. PATTERN DISPATCH: Wildcard Filters with Match Caching
            cached_callbacks = self._match_cache.get_cached_callbacks(topic)
            if cached_callbacks is not None:
                for callback_func in cached_callbacks:
                    callback_func(msg)
                return

            # Cache Miss: Resolve wildcards
            matched_callbacks = []
            for entry in self._wildcard_subscribers:
                topic_filter, callbacks = entry
                if mqtt.topic_matches_sub(topic_filter, topic):
                    for cb in callbacks:
                        matched_callbacks.append(cb)
                        cb(msg)
            
            # Store in cache
            self._match_cache.cache_callbacks(topic, matched_callbacks)

    def get_on_message_callback(self):
        return self._on_message

    async def resubscribe_all_topics(self, client):
        """
        Async resubscription. Called by MqttConnectionManager within the async context.
        """
        with self._lock:
            self._active_broker_subscriptions.clear()
            self._match_cache.clear()

            await client.subscribe(self._root_topic)
            self._active_broker_subscriptions.add(self._root_topic)
            
            for topic_filter in self._exact_subscribers:
                if not topic_filter.startswith(f"{self._base_topic}/"):
                    await client.subscribe(topic_filter)
                    self._active_broker_subscriptions.add(topic_filter)
                    
            for entry in self._wildcard_subscribers:
                topic_filter, _ = entry
                if not topic_filter.startswith(f"{self._base_topic}/"):
                    await client.subscribe(topic_filter)
                    self._active_broker_subscriptions.add(topic_filter)
        
        if LOCAL_DEBUG:
            logger.debug("🚀📤📥 [MQTT] aiomqtt: Resubscribed to root and "
                         "external filters.")
