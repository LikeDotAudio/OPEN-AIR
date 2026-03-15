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
import queue
import threading

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True    # Set to False in production, True for dev on this file
from workers.logger.logger import initialize_logging, set_log_directory
from loguru import logger

from managers.configini.config_reader import Config

app_constants = Config.get_instance()  # Get the singleton instance

# --- ASYNCHRONOUS MQTT QUEUE ---
_publish_queue = queue.Queue()
_worker_thread = None
_worker_lock = threading.Lock()

def _publish_worker():
    """Background worker thread that consumes the publish queue."""
    connection_manager = MqttConnectionManager()
    
    while True:
        try:
            item = _publish_queue.get()
            if item is None: # Shutdown signal
                break
            
            topic, payload, retain = item
            client = connection_manager.get_client_instance()
            
            if client and client.is_connected():
                # 📡 THE COMMS FIREHOSE: Log every outgoing byte
                payload_str = payload.decode('utf-8') if isinstance(payload, (bytes, bytearray)) else str(payload)
                if LOCAL_DEBUG: logger.trace(f"🚀📤📢{topic} 📨{payload_str}")
                client.publish(topic, payload, retain=retain)
            else:
                # Optionally log or requeue? For now, just drop to avoid blocking.
                pass
                
            _publish_queue.task_done()
        except Exception:
            logger.exception("❌ Error in MQTT publisher worker")

def start_publisher_worker():
    """Starts the asynchronous publisher worker thread if not already running."""
    global _worker_thread
    with _worker_lock:
        if _worker_thread is None:
            _worker_thread = threading.Thread(target=_publish_worker, name="MqttPublisherWorker", daemon=True)
            _worker_thread.start()
            if LOCAL_DEBUG: logger.debug("🚀 MQTT Publisher Worker thread started.")

def shutdown_publisher_worker():
    """Signals the publisher worker thread to shut down gracefully."""
    global _worker_thread
    with _worker_lock:
        if _worker_thread is not None:
            if LOCAL_DEBUG: logger.debug("🔌 MQTT Publisher Service: Shutting down worker...")
            _publish_queue.put(None)
            if _worker_thread.is_alive():
                _worker_thread.join(timeout=2.0)
            _worker_thread = None
            if LOCAL_DEBUG: logger.debug("✅ MQTT Publisher Service: Worker offline.")

# Ensure the worker is started when the module is imported
start_publisher_worker()


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
    Publishes a payload to a given topic via the asynchronous queue.
    """
    _publish_queue.put((topic, payload, retain))


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
    Publishes the entire JSON structure to a base topic via the asynchronous queue.
    The "Verbatim" requirement.
    """
    payload = orjson.dumps(json_data).decode()
    publish_payload(base_topic, payload)