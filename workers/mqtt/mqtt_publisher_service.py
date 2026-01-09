# mqtt/mqtt_publisher_service.py
#
# Provides functions for publishing messages to the MQTT broker, including raw payloads and entire JSON structures.
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
# Version 20250821.200641.1

from .mqtt_connection_manager import MqttConnectionManager
import orjson
from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args
from managers.configini.config_reader import Config

app_constants = Config.get_instance()  # Get the singleton instance


# Checks if the MQTT client is currently connected to the broker.
# Inputs:
#     None.
# Outputs:
#     bool: True if the client is connected, False otherwise.
def is_connected():
    """
    Checks if the MQTT client is connected.
    """
    connection_manager = MqttConnectionManager()
    client = connection_manager.get_client_instance()
    return client and client.is_connected()


# Publishes a raw payload string to a specified MQTT topic.
# This function checks for an active connection before attempting to publish
# and logs the publication event.
# Inputs:
#     topic (str): The MQTT topic to publish to.
#     payload (str): The string payload to send.
#     retain (bool): Whether the message should be retained by the broker.
# Outputs:
#     None.
def publish_payload(
    topic: str, payload: str, retain: bool = app_constants.MQTT_RETAIN_BEHAVIOR
):
    """
    Publishes a payload to a given topic.
    """
    if is_connected():
        connection_manager = MqttConnectionManager()
        client = connection_manager.get_client_instance()
        client.publish(topic, payload, retain=retain)
        debug_logger(message=f"📤 Published to {topic}: {payload}", **_get_log_args())
    else:
        debug_logger(
            message=f"❌ Not connected to broker. Cannot publish to {topic}.",
            **_get_log_args(),
        )


# Publishes an entire JSON structure to a base MQTT topic.
# This function serializes a dictionary into a JSON string and publishes it
# to the specified topic, ensuring the entire structure is sent as a single message.
# Inputs:
#     base_topic (str): The base MQTT topic to publish the JSON structure to.
#     json_data (dict): The dictionary representing the JSON structure to be published.
# Outputs:
#     None.
def publish_json_structure(base_topic: str, json_data: dict):
    """
    Publishes the entire JSON structure to a base topic.
    The "Verbatim" requirement.
    """
    if is_connected():
        connection_manager = MqttConnectionManager()
        client = connection_manager.get_client_instance()
        payload = orjson.dumps(json_data)
        client.publish(base_topic, payload, retain=app_constants.MQTT_RETAIN_BEHAVIOR)
        debug_logger(
            message=f"📤 Published JSON structure to {base_topic}", **_get_log_args()
        )
    else:
        debug_logger(
            message=f"❌ Not connected to broker. Cannot publish JSON structure to {base_topic}.",
            **_get_log_args(),
        )