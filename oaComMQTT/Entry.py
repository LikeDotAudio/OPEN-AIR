"""
oaComMQTT/Entry.py - The sole orchestrator for the MQTT Communication Module.

Purpose:
This file is the public entry point for 'oaComMQTT'. It manages the 
lifecycle of the MQTT connection and provides high-level publisher/subscriber
interfaces to the rest of the project.
"""

from .Managers.mqtt_connection import MqttConnectionManager
from .Managers.mqtt_subscriber_router import MqttSubscriberRouter
from .Core.mqtt_message import MqttMessage
from .Core import mqtt_publisher_service
from .Methods.mqtt_topic_utils import (
    format_topic, 
    parse_topic, 
    validate_topic
)

def get_connection_manager():
    """Returns the singleton MqttConnectionManager instance."""
    return MqttConnectionManager()

def get_subscriber_router():
    """Returns the singleton MqttSubscriberRouter instance."""
    return MqttSubscriberRouter()

def start_mqtt_services(broker_address="localhost", broker_port=1883):
    """
    Initializes the MQTT connection and starts the publisher worker.
    """
    manager = get_connection_manager()
    router = get_subscriber_router()
    
    # Initialize connection
    manager.connect_to_broker(
        address=broker_address, 
        port=broker_port, 
        subscriber_router=router
    )
    
    # Start background publisher worker
    mqtt_publisher_service.start_publisher_worker()
    return manager

def stop_mqtt_services():
    """
    Shuts down MQTT connection and publisher services.
    """
    mqtt_publisher_service.shutdown_publisher_worker()

# Standardized exports
__all__ = [
    "MqttConnectionManager",
    "MqttSubscriberRouter",
    "MqttMessage",
    "mqtt_publisher_service",
    "get_connection_manager",
    "get_subscriber_router",
    "start_mqtt_services",
    "stop_mqtt_services",
    "format_topic",
    "parse_topic",
    "validate_topic"
]
