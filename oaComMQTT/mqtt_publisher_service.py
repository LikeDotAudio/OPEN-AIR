# mqtt/mqtt_publisher_service.py
#
# Provides functions for publishing messages to the MQTT broker.
# Simplified to leverage the built-in queuing in MqttConnectionManager.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
# Version 20260316.1

from .mqtt_connection import MqttConnectionManager
import orjson

from oaConfiguration.config_reader import Config
app_constants = Config.get_instance()

def start_publisher_worker():
    """No-op for backward compatibility. MqttConnectionManager handles its own worker."""
    pass

def shutdown_publisher_worker():
    """No-op for backward compatibility. MqttConnectionManager handles its own lifecycle."""
    pass

def is_connected():
    """
    Checks if the MQTT client is connected.
    """
    return MqttConnectionManager().is_connected()

def publish_payload(
    topic: str, payload: str, retain: bool = app_constants.MQTT_RETAIN_BEHAVIOR
):
    """
    Publishes a payload to a given topic via the MqttConnectionManager's internal queue.
    """
    MqttConnectionManager().publish(topic, payload, retain=retain)

def publish_json_structure(base_topic: str, json_data: dict):
    """
    Publishes the entire JSON structure to a base topic.
    """
    payload = orjson.dumps(json_data).decode()
    publish_payload(base_topic, payload)
