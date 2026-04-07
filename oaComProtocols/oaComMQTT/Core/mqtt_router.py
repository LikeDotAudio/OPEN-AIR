# oaComProtocols.oaComMQTT/Core/mqtt_router.py
# Author: Anthony Peter Kuzub
# Version: 20260331.2350.1
#
# Description: Python wrapper for the Rust MQTT Router.

LOCAL_DEBUG = False

import logging
from .oaMQTTManager_rs.compiler_hook import ensure_compiled

try:
    ensure_compiled()
    from oamqttmanager_rs import MqttRouter as RustMqttRouter
    HAS_RUST = True
except ImportError:
    logging.warning("⚠️ [MQTT] oamqttmanager_rs not found. Using fallback logic (if any).")
    HAS_RUST = False
except Exception as e:
    logging.error(f"❌ [MQTT] Failed to initialize Rust MQTT Router: {e}")
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
            logging.error("oaComProtocols.oaComMQTT: Missing mandatory Rust router.")

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
