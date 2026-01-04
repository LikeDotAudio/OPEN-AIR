# workers/mqtt/mqtt_publisher_service.py
#
# Purpose: A dedicated courier. Takes a topic and a payload, checks if connected, and sends it.
# Key Function: publish_payload(topic: str, payload: str, retain: bool)
# Key Function: publish_json_structure(base_topic: str, json_data: dict) -> The "Verbatim" requirement.

from .mqtt_connection_manager import MqttConnectionManager
import orjson
from workers.logger.logger import  debug_logger
from workers.logger.log_utils import _get_log_args
from managers.configini.config_reader import Config
app_constants = Config.get_instance() # Get the singleton instance

def is_connected():
    """
    Checks if the MQTT client is connected.
    """
    connection_manager = MqttConnectionManager()
    client = connection_manager.get_client_instance()
    return client and client.is_connected()

def publish_payload(topic: str, payload: str, retain: bool = app_constants.MQTT_RETAIN_BEHAVIOR):
    """
    Publishes a payload to a given topic.
    """
    if is_connected():
        connection_manager = MqttConnectionManager()
        client = connection_manager.get_client_instance()
        client.publish(topic, payload, retain=retain)
        debug_logger(message=f"📤 Published to {topic}: {payload}", **_get_log_args())
    else:
        debug_logger(message=f"❌ Not connected to broker. Cannot publish to {topic}.", **_get_log_args())

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
        debug_logger(message=f"📤 Published JSON structure to {base_topic}", **_get_log_args())
    else:
        debug_logger(message=f"❌ Not connected to broker. Cannot publish JSON structure to {base_topic}.", **_get_log_args())