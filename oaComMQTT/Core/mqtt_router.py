# oaComMQTT/Core/mqtt_router.py
# Author: Anthony Peter Kuzub
# Version: 20260331.2350.1
#
# Description: Python wrapper for the Rust MQTT Router.

LOCAL_DEBUG = True

import logging
from .oaMQTTManager_rs.compiler_hook import ensure_compiled

try:
    ensure_compiled()
    from .oaMQTTManager_rs.oamqttmanager_rs import MqttRouter as RustMqttRouter
    HAS_RUST = True
except Exception as e:
    logging.error(f"oaComMQTT: Failed to load Rust MQTT Router: {e}")
    HAS_RUST = False

class MqttRouter:
    """
    High-performance MQTT topic matching engine using Rust.
    """
    def __init__(self):
        if HAS_RUST:
            if LOCAL_DEBUG:
                print("📡🛠️🔗 [MQTT] Using PURE RUST router.")
            self._router = RustMqttRouter()
        else:
            self._router = None
            logging.error("oaComMQTT: Missing mandatory Rust router.")

    def subscribe(self, filter: str, callback):
        if self._router:
            self._router.subscribe(filter, callback)

    def unsubscribe(self, filter: str):
        if self._router:
            self._router.unsubscribe(filter)

    def match_topic(self, topic: str):
        if self._router:
            return self._router.match_topic(topic)
        return []

    def clear(self):
        if self._router:
            self._router.clear()
