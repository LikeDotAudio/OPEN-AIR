# oaComProtocols.oaComMQTT/Entry.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Entry point for the MQTT Communication Module.
# Manages the lifecycle of the MQTT connection and provides publisher/subscriber interfaces.
# Refactored for centralized management by ComProtocolManager, with MQTT connection being self-contained.

import sys
import os
import pathlib
import threading
import subprocess
import unittest
from pathlib import Path

# Ensure project root is in sys.path for direct execution
current_dir = pathlib.Path(__file__).resolve().parent
project_root = current_dir.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from oaLogging.Methods.matrix_gate import matrix_log
from oaConfigurationManager.FileReaders.config_reader import Config

# --- Core Components ---
from oaComProtocols.oaComMQTT.Managers.mqtt_connection import MqttConnectionManager
from oaComProtocols.oaComMQTT.Managers.mqtt_subscriber_router import MqttSubscriberRouter
from oaComProtocols.oaComMQTT.Managers.mqtt_manager import MqttManager

_connection_manager = None
_subscriber_router = None
_manager = None

def get_connection_manager(**kwargs):
    """Returns the singleton MqttConnectionManager instance. Manages its own connection."""
    global _connection_manager
    if _connection_manager is None:
        # Default parameters, will be overridden by manager if provided via kwargs
        broker_address = kwargs.get("broker_address", Config.get_instance().get("MQTT_BROKER_ADDRESS", "localhost"))
        broker_port = kwargs.get("broker_port", Config.get_instance().get("MQTT_BROKER_PORT", 1883))
        username = kwargs.get("username", Config.get_instance().get("MQTT_USERNAME", "guest"))
        password = kwargs.get("password", Config.get_instance().get("MQTT_PASSWORD", "guest"))
        client_id = kwargs.get("client_id", f"OPENAIR-MQTT-{os.getpid()}")
        
        _connection_manager = MqttConnectionManager(
            address=broker_address,
            port=broker_port,
            username=username,
            password=password,
            client_id=client_id
        )
        matrix_log("comms", "mqtt", "get_connection_manager", "MQTT Connection Manager initialized (self-contained).", "DEBUG")
    return _connection_manager

def get_subscriber_router(**kwargs):
    """Returns the singleton MqttSubscriberRouter instance."""
    global _subscriber_router
    if _subscriber_router is None:
        from oaComProtocols.oaComMQTT.Managers.mqtt_subscriber_router import MqttSubscriberRouter
        _subscriber_router = MqttSubscriberRouter()
        matrix_log("comms", "mqtt", "get_subscriber_router", "MQTT Subscriber Router initialized.", "DEBUG")
    return _subscriber_router

def get_mqtt_manager(**kwargs):
    """Returns a new MqttManager instance, using self-contained or provided dependencies."""
    global _manager
    if _manager is None:
        from oaComProtocols.oaComMQTT.Managers.mqtt_manager import MqttManager
        
        # Retrieve or create dependencies internally if not provided
        mqtt_client = kwargs.get("mqtt_client", get_connection_manager(**kwargs))
        subscriber_router = kwargs.get("subscriber_router", get_subscriber_router())
        # State cache is assumed to be handled by the orchestrator or provided
        state_cache_manager = kwargs.get("state_cache_manager", None) 
        
        _manager = MqttManager(subscriber_router, mqtt_client, state_cache_manager)
        matrix_log("comms", "mqtt", "get_mqtt_manager", "MQTT Manager initialized.", "DEBUG")
    return _manager

def start(**kwargs):
    """
    Initializes and starts the MQTT connection and publisher services internally.
    Accepts optional kwargs to override default connection parameters.
    """
    matrix_log("comms", "mqtt", "start", "🚀 [MQTT] Starting MQTT services internally...", "INFO")
    
    # Initialize connection and start publisher worker using internal managers
    conn_mgr = get_connection_manager(**kwargs)
    sub_router = get_subscriber_router(**kwargs)
    manager = get_mqtt_manager(mqtt_client=conn_mgr, subscriber_router=sub_router, **kwargs)
    
    # Initialize connection and start publisher worker
    conn_mgr.connect_to_broker(subscriber_router=sub_router)
    
    # Start background publisher worker. This might need to be managed externally if it's a long-lived process.
    from oaComProtocols.oaComMQTT.Core import mqtt_publisher_service
    if hasattr(mqtt_publisher_service, 'start_publisher_worker'):
        mqtt_publisher_service.start_publisher_worker()
    
    matrix_log("comms", "mqtt", "start", "✅ MQTT services started.", "SUCCESS")
    return conn_mgr # Return connection manager for external control if needed

def stop():
    """
    Shuts down MQTT connection and publisher services.
    """
    global _connection_manager, _subscriber_router, _manager
    
    matrix_log("comms", "mqtt", "stop", "🛑 [MQTT] Stopping MQTT services...", "INFO")
    
    # Stop publisher worker first if it was started here
    from oaComProtocols.oaComMQTT.Core import mqtt_publisher_service
    if hasattr(mqtt_publisher_service, 'shutdown_publisher_worker'):
        mqtt_publisher_service.shutdown_publisher_worker()

    # Stop and disconnect
    if _manager:
        _manager.stop() # Stop the manager itself
        _manager = None
    if _connection_manager:
        _connection_manager.disconnect()
        _connection_manager = None
    _subscriber_router = None # Clear router
    
    matrix_log("comms", "mqtt", "stop", "✅ MQTT services stopped.", "INFO")

def status():
    """
    Returns the current status of the MQTT connection.
    """
    conn_mgr = get_connection_manager() # Access singleton
    if conn_mgr:
        return {"connected": conn_mgr.is_connected(), "client_id": conn_mgr.client_id}
    return {"connected": False, "error": "Connection manager not initialized"}

# Methods from .Methods.mqtt_topic_utils can be imported directly if needed
# by the orchestrator or other modules.

# Standardized exports
__all__ = [
    "MqttConnectionManager",
    "MqttSubscriberRouter",
    "MqttManager",
    "MqttMessage",
    "mqtt_publisher_service",
    "get_connection_manager",
    "get_subscriber_router",
    "get_mqtt_manager",
    "start",
    "stop",
    "status",
    "generate_topic_path_from_filepath",
    "get_topic",
    "generate_base_topic",
    "generate_widget_topic"
]

# Standalone main() function is removed.
# def run_tests(): ...
# if __name__ == "__main__": ...
