# workers/mqtt/broker_monitor.py
#
# Monitors the Mosquitto broker's $SYS topics to provide real-time statistics.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Professional services for customizing and tailoring this software to your specific
# application can be negotiated. There is no charge to use, modify, or fork this software.
#
# Build Log: https://like.audio/category/software/spectrum-scanner/
# Source Code: https://github.com/APKaudio/
# Feature Requests can be emailed to i @ like . audio
#
# Version 20260124.000000.1

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True    # Set to False in production, True for dev on this file
from workers.logger.logger import initialize_logging, set_log_directory
from loguru import logger

from managers.configini.config_reader import Config
from workers.Command_Router.mqtt.mqtt_message import MqttMessage

app_constants = Config.get_instance()

class BrokerMonitor:
    """
    Subscribes to $SYS/broker/# topics and aggregates statistics.
    Uses an observer pattern to notify the GUI of updates.
    """
    def __init__(self, subscriber_router):
        self.subscriber_router = subscriber_router
        self._stats = {}
        self._observers = []
        
        # Subscribe to key broker statistics
        # We subscribe to wildcard to catch everything useful
        self.subscriber_router.subscribe_to_topic("$SYS/broker/#", self._on_sys_message)
        
        if LOCAL_DEBUG: logger.debug("🕵️ BrokerMonitor initialized and listening to $SYS/broker/#")

    def register_observer(self, callback):
        """Register a GUI callback to receive stats updates."""
        if callback not in self._observers:
            self._observers.append(callback)

    def unregister_observer(self, callback):
        if callback in self._observers:
            self._observers.remove(callback)

    def _on_sys_message(self, msg: MqttMessage):
        """
        Callback for MQTT messages. Updates the internal stats dictionary.
        """
        topic = msg.topic
        payload = msg.decode_payload()
        
        # Clean up the topic to be a nice key (e.g. "$SYS/broker/clients/connected" -> "clients/connected")
        key = topic.replace("$SYS/broker/", "")
        self._stats[key] = payload
        
        # Notify observers
        for callback in self._observers:
            try:
                callback(self._stats)
            except Exception as e:
                if LOCAL_DEBUG:
                    logger.exception("❌ Error notifying BrokerMonitor observer")

    def get_stats(self):
        return self._stats