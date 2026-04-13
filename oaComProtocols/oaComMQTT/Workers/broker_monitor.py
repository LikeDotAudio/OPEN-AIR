import inspect
from oaLogging.Methods.matrix_gate import matrix_log
# Workers/broker_monitor.py
# Author: Anthony Peter Kuzub
# Version: 20260124.000000.1
#
# Description: Monitors the Mosquitto broker's $SYS topics to provide real-time statistics.

from oaLogging.Core.logger import MQTT_LOGGER
from loguru import logger

from oaConfigurationManager.FileReaders.config_reader import Config
from oaComProtocols.oaComMQTT.Core.mqtt_message import MqttMessage

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
        
        matrix_log("comms", "mqtt", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "BrokerMonitor initialized and listening to $SYS/broker/#", "DEBUG")

    def register_observer(self, callback):
        """Register a GUI callback to receive stats updates."""
        if callback not in self._observers:
            self._observers.append(callback)

    def unregister_observer(self, callback):
        if callback in self._observers:
            self._observers.remove(callback)

    def _on_sys_message(self, message: MqttMessage):
        """
        Callback for MQTT messages. Updates the internal stats dictionary.
        """
        topic = message.topic
        payload = message.decode_payload()
        
        # Clean up the topic to be a nice key (e.g. "$SYS/broker/clients/connected" -> "clients/connected")
        key = topic.replace("$SYS/broker/", "")
        self._stats[key] = payload
        
        # Notify observers
        for callback in self._observers:
            try:
                callback(self._stats)
            except Exception:
                MQTT_LOGGER.exception("Error notifying BrokerMonitor observer")

    def get_stats(self):
        return self._stats
