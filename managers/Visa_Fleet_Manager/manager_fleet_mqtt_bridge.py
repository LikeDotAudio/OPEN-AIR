import paho.mqtt.client as mqtt
import json
import os
import time

try:
    from workers.logger.logger import debug_logger
    from workers.logger.log_utils import _get_log_args
except ModuleNotFoundError:
    print(
        "Warning: 'workers.logger' not found. Using dummy logger for MqttFleetBridge."
    )

    def debug_logger(message, *args, **kwargs):
        if kwargs.get("level", "INFO") != "DEBUG":
            print(f"[{kwargs.get('level', 'INFO')}] {message}")

    def _get_log_args(*args, **kwargs):
        return {}  # Return empty dict, as logger args are not available


class MqttFleetBridge:
    def __init__(self, broker="localhost", port=1883, MQTT_TOPIC="OPEN-AIR"):
        self.broker = broker
        self.port = port
        self.topic = MQTT_TOPIC
        self.client = mqtt.Client()
        self.client.on_connect = self._on_connect
        self.client.on_publish = self._on_publish
        self.is_connected = False
        debug_logger(
            message=f"Initializing MqttFleetBridge. Broker: {self.broker}:{self.port}, Base Topic: {self.topic}",
            **_get_log_args(),
        )
        self._connect_mqtt()

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            debug_logger(
                message=f"MQTT Bridge Connected to Broker: {self.broker}",
                **_get_log_args(),
            )
            self.is_connected = True
        else:
            debug_logger(
                message=f"MQTT Bridge Failed to connect, return code {rc}",
                level="ERROR",
                **_get_log_args(),
            )
            self.is_connected = False

    def _on_publish(self, client, userdata, mid):
        # This callback is less useful for individual flattened messages, as mid is for the specific publish call.
        # debug_logger(message=f"MQTT Bridge Message Published (MID: {mid})", level="DEBUG", **_get_log_args())
        pass  # Keep this minimal to avoid log spam for every single published parameter

    def _connect_mqtt(self):
        try:
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_start()
            debug_logger(
                message=f"Attempting connection to MQTT Broker: {self.broker}:{self.port}",
                level="DEBUG",
                **_get_log_args(),
            )
        except Exception as e:
            debug_logger(
                message=f"MQTT Bridge Error connecting to broker: {e}",
                level="ERROR",
                **_get_log_args(),
            )
            self.is_connected = False

    def publish_inventory(self, inventory_data):
        debug_logger(
            message=f"Received inventory data for publishing. Size: {len(str(inventory_data))} chars.",
            level="DEBUG",
            **_get_log_args(),
        )
        if not self.is_connected:
            debug_logger(
                message="MQTT Bridge Not connected to broker, attempting to re-connect...",
                level="WARNING",
                **_get_log_args(),
            )
            self._connect_mqtt()

        if self.is_connected:
            try:
                self._publish_flattened_dict(inventory_data, self.topic)
                debug_logger(
                    message="Inventory publishing process initiated.",
                    level="DEBUG",
                    **_get_log_args(),
                )
            except Exception as e:
                debug_logger(
                    message=f"MQTT Bridge Error publishing flattened message: {e}",
                    level="ERROR",
                    **_get_log_args(),
                )
        else:
            debug_logger(
                message="MQTT Bridge Failed to publish: Not connected to broker.",
                level="ERROR",
                **_get_log_args(),
            )

    def _publish_flattened_dict(self, data, base_topic):
        """
        Recursively publishes key-value pairs from a dictionary
        to MQTT topics derived from the dictionary structure.
        Device dictionaries at the innermost level are published as single JSON blobs.
        """
        if isinstance(data, dict):
            # Heuristic to identify if 'data' is a device BLOB (innermost dictionary)
            # If it contains typical device attributes like serial_number, it's likely
            # a device BLOB that needs to be published as a whole.
            if "serial_number" in data and "device_type" in data and "model" in data:
                try:
                    payload = json.dumps(data, indent=2)
                    self.client.publish(base_topic, payload)
                    debug_logger(
                        message=f"Published Device BLOB. Topic: '{base_topic}', Payload length: {len(payload)}",
                        level="INFO",
                        **_get_log_args(),
                    )
                except Exception as e:
                    debug_logger(
                        message=f"MQTT Bridge Error publishing device BLOB {base_topic}: {e}",
                        level="ERROR",
                        **_get_log_args(),
                    )
                return  # Stop further flattening, as we published the whole BLOB

            for key, value in data.items():
                # Removing space sanitization as per user's explicit request for "Spectrum Analyzer" in topic
                # Keeping forward slash sanitization as / is a topic level separator
                sanitized_key = key.replace("/", "_")
                new_topic = f"{base_topic}/{sanitized_key}"
                debug_logger(
                    message=f"Traversing to topic: '{new_topic}'",
                    level="DEBUG",
                    **_get_log_args(),
                )
                self._publish_flattened_dict(value, new_topic)
        elif isinstance(data, list):
            # If a list is encountered, flatten its elements by index
            # This is primarily for lists of simple values, not device BLOBs anymore.
            for index, item in enumerate(data):
                new_topic = f"{base_topic}/{index}"
                debug_logger(
                    message=f"Traversing list index: '{new_topic}'",
                    level="DEBUG",
                    **_get_log_args(),
                )
                self._publish_flattened_dict(item, new_topic)
        else:
            # This is a leaf node (not a dict or list), publish its value
            try:
                # Convert non-string values to string for MQTT payload
                payload = str(data)
                self.client.publish(base_topic, payload)
                debug_logger(
                    message=f"Published Leaf Node. Topic: '{base_topic}', Payload: '{payload}'",
                    level="INFO",
                    **_get_log_args(),
                )
            except Exception as e:
                debug_logger(
                    message=f"MQTT Bridge Error publishing leaf node {base_topic}: {e}",
                    level="ERROR",
                    **_get_log_args(),
                )

    def disconnect(self):
        if self.is_connected:
            self.client.loop_stop()
            self.client.disconnect()
            debug_logger(message="MQTT Bridge Disconnected.", **_get_log_args())
            self.is_connected = False
