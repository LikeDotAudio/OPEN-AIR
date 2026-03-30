# Managers/fleet_mqtt_bridge.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Bridges the Visa Fleet Manager's internal state and controls with MQTT.

import orjson
import os
import time
from typing import Optional, Callable

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True    # Set to False in production, True for dev on this file
from oaLogging.Core.logger import initialize_logging, set_log_directory
from loguru import logger

from oaConfiguration.FileReaders.config_reader import Config
from oaComMQTT.Core.mqtt_message import MqttMessage

app_constants = Config.get_instance()

class MqttFleetBridge:
    """
    Handles the MQTT representation of the instrument fleet and its control hooks.
    """
    def __init__(self, mqtt_connection_manager, subscriber_router, 
                 topic_prefix=None):
        """
        Initializes the MQTT bridge for the visa fleet.

        Parameters:
        - mqtt_connection_manager: The shared instance for publishing messages.
        - subscriber_router: The instance for subscribing to control topics.
        - topic_prefix: Root topic for all fleet messages (defaults to base topic).

        Returns:
        - A new MqttFleetBridge instance.

        Side Effects & Thread-Safety:
        - Registers MQTT subscriptions via the subscriber_router.
        """
        self.mqtt_manager = mqtt_connection_manager
        self.subscriber_router = subscriber_router
        self.topic_prefix = topic_prefix or app_constants.get_mqtt_base_topic()
        
        self.on_scan_trigger: Optional[Callable[[], None]] = None
        
        if LOCAL_DEBUG:
            logger.debug(f"Initializing MqttFleetBridge. Prefix: {self.topic_prefix}")
        
        self._setup_subscriptions()

    def _setup_subscriptions(self):
        """
        Configures internal MQTT listeners for fleet control.

        Returns:
        - None.
        """
        if self.subscriber_router:
            scan_topic = f"{self.topic_prefix}/System/Control/Fleet/Scan"
            self.subscriber_router.subscribe_to_topic(
                scan_topic, 
                self._on_scan_message
            )
            if LOCAL_DEBUG:
                logger.debug(f"MqttFleetBridge subscribed to: {scan_topic}")

    @property
    def is_connected(self) -> bool:
        """
        Checks if the underlying MQTT manager is currently connected.

        Returns:
        - True if connected, False otherwise.
        """
        return self.mqtt_manager.is_connected() if self.mqtt_manager else False

    def _on_scan_message(self, msg: MqttMessage):
        """
        Handles incoming scan trigger messages from MQTT.

        Parameters:
        - msg: The MqttMessage containing the "TRIGGER" payload.

        Returns:
        - None.
        """
        payload = msg.decode_payload()
        if payload == "TRIGGER":
            if LOCAL_DEBUG:
                logger.debug("MQTT Bridge received Scan Trigger!")
            if self.on_scan_trigger:
                self.on_scan_trigger()

    def publish_inventory(self, inventory_data):
        """
        Publishes the entire fleet inventory to MQTT.

        Parameters:
        - inventory_data: A dictionary representing the grouped fleet inventory.

        Returns:
        - None.

        Side Effects & Thread-Safety:
        - Performs multiple MQTT publish operations.
        """
        if not self.mqtt_manager:
            return
        
        if LOCAL_DEBUG:
            logger.debug(f"Fleet Bridge: Publishing inventory. "
                         f"Size: {len(str(inventory_data))} chars.")

        try:
            self._publish_flattened_dict(inventory_data, self.topic_prefix)
        except Exception as e:
            if LOCAL_DEBUG:
                logger.exception("MQTT Bridge Error publishing flattened message")

    def _publish_flattened_dict(self, data, base_topic):
        """
        Recursively maps a nested data structure to a hierarchy of MQTT topics.

        Parameters:
        - data: The dictionary, list, or leaf value to publish.
        - base_topic: The MQTT topic path corresponding to this node.

        Returns:
        - None.

        Side Effects & Thread-Safety:
        - Recursively invokes itself and performs MQTT I/O.
        """
        if not self.mqtt_manager:
            return

        if isinstance(data, dict):
            # If the dictionary looks like a complete device record, 
            # publish it as a single JSON blob for convenience.
            if ("serial_number" in data and "device_type" in data 
                and "model" in data):
                try:
                    payload = orjson.dumps(
                        data, 
                        option=orjson.OPT_INDENT_2
                    ).decode()
                    self.mqtt_manager.publish(base_topic, payload)
                except Exception as e:
                    if LOCAL_DEBUG:
                        logger.exception(f"MQTT Bridge Error publishing "
                                         f"device BLOB {base_topic}")
                return

            # Otherwise, continue flattening the dictionary into sub-topics.
            for key, value in data.items():
                sanitized_key = key.replace("/", "_")
                new_topic = f"{base_topic}/{sanitized_key}"
                self._publish_flattened_dict(value, new_topic)
        elif isinstance(data, list):
            # Map list indices to numeric sub-topics.
            for index, item in enumerate(data):
                new_topic = f"{base_topic}/{index}"
                self._publish_flattened_dict(item, new_topic)
        else:
            # Leaf node: publish the literal value (skip if None).
            if data is None:
                return
                
            try:
                self.mqtt_manager.publish(base_topic, str(data))
            except Exception as e:
                if LOCAL_DEBUG:
                    logger.exception(f"MQTT Bridge Error publishing "
                                     f"leaf node {base_topic}")

    def disconnect(self):
        """
        Cleans up the bridge. Note: Does not disconnect the shared MQTT manager.

        Returns:
        - None.
        """
        pass
