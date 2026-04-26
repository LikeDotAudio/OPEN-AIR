# Managers/fleet_mqtt_bridge.py
#
# Bridges the Visa Fleet Manager's internal state and controls with MQTT.
# Translates discovery results into a hierarchical topic structure.
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
# Version 20260330.1600.1

from collections.abc import Callable

import orjson

from oaComProtocols.oaComMQTT.Core.mqtt_message import MqttMessage
from oaConfigurationManager.FileReaders.config_reader import Config
from oaLogging.Methods.matrix_gate import matrix_log

app_constants = Config.get_instance()

class MqttFleetBridge:
    """
    Handles the MQTT representation of the instrument fleet and its control hooks.
    """
    def __init__(self, mqtt_connection_manager, subscriber_router,
                 topic_prefix=None):
        self.mqtt_manager = mqtt_connection_manager
        self.subscriber_router = subscriber_router
        self.topic_prefix = topic_prefix or app_constants.get_mqtt_base_topic()

        self.on_scan_trigger: Callable[[], None] | None = None

        matrix_log("comms", "visa", "__init__", f"Initializing MqttFleetBridge. Prefix: {self.topic_prefix}", "DEBUG")
        self._setup_subscriptions()

    def _setup_subscriptions(self):
        if self.subscriber_router:
            scan_topic = f"{self.topic_prefix}/System/Control/Fleet/Scan"
            self.subscriber_router.subscribe_to_topic(scan_topic, self._on_scan_message)
            matrix_log("comms", "visa", "_setup_subscriptions", f"MqttFleetBridge subscribed to: {scan_topic}", "DEBUG")

    @property
    def is_connected(self) -> bool:
        return self.mqtt_manager.is_connected() if self.mqtt_manager else False

    def _on_scan_message(self, message: MqttMessage):
        payload = message.decode_payload()
        if payload == "TRIGGER":
            matrix_log("comms", "visa", "_on_scan_message", "MQTT Bridge received Scan Trigger!", "DEBUG")
            if self.on_scan_trigger:
                self.on_scan_trigger()

    def publish_inventory(self, inventory_data):
        if not self.mqtt_manager: return

        matrix_log("comms", "visa", "publish_inventory", f"Fleet Bridge: Publishing inventory. Size: {len(str(inventory_data))} chars.", "DEBUG")

        try:
            self._publish_flattened_dict(inventory_data, self.topic_prefix)
        except Exception as e:
            matrix_log("comms", "visa", "publish_inventory", f"MQTT Bridge Error publishing flattened message: {e}", "ERROR")

    def _publish_flattened_dict(self, data, base_topic):
        if not self.mqtt_manager: return

        if isinstance(data, dict):
            if ("serial_number" in data and "device_type" in data
                and "model" in data):
                try:
                    payload = orjson.dumps(data, option=orjson.OPT_INDENT_2).decode()
                    self.mqtt_manager.publish(base_topic, payload)
                except Exception as e:
                    matrix_log("comms", "visa", "_publish_flattened_dict", f"MQTT Bridge Error publishing device BLOB {base_topic}: {e}", "ERROR")
                return

            for key, value in data.items():
                sanitized_key = key.replace("/", "_")
                new_topic = f"{base_topic}/{sanitized_key}"
                self._publish_flattened_dict(value, new_topic)
        elif isinstance(data, list):
            for index, item in enumerate(data):
                new_topic = f"{base_topic}/{index}"
                self._publish_flattened_dict(item, new_topic)
        else:
            if data is None: return
            try:
                self.mqtt_manager.publish(base_topic, str(data))
            except Exception as e:
                matrix_log("comms", "visa", "_publish_flattened_dict", f"MQTT Bridge Error publishing leaf node {base_topic}: {e}", "ERROR")

    def disconnect(self):
        pass
