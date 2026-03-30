# oaComSNMP/Entry.py
#
# The sole orchestrator and public gatekeeper for the SNMP Communication Module.
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
# Version 20260329.1045.1

"""
oaComSNMP/Entry.py - The sole orchestrator for the SNMP Communication Module.
"""

import sys
import os
import pathlib
import threading
import time

# Ensure the root directory is in the search path for local module imports.
current_dir = pathlib.Path(__file__).resolve().parent
project_root = current_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from .Managers.snmp_manager import SNMPManager
from .Workers.snmp_tester import SnmpTester
from .Methods.snmp_mib_generator import MibGenerator
from .Methods.snmp_installer_generator import InstallerGenerator

_instance = None

def get_manager(state_cache_manager=None, mqtt_connection_manager=None, subscriber_router=None, run_bridge=None):
    """
    Singleton getter for the SNMP Manager.
    If managers are not provided, it attempts to resolve them from global instances.
    """
    global _instance
    
    # ⚡ AUTONOMY: Determine run_bridge based on partition if not explicitly provided
    if run_bridge is None:
        try:
            from oaConfiguration.Core.identity import IdentityManager
            ident = IdentityManager.initialize()
            partition = ident.get("PARTITION_ID", "STANDALONE")
            # Only CORE or STANDALONE partitions run the active bridge logic
            run_bridge = (partition in ["CORE", "STANDALONE"])
        except Exception:
            run_bridge = True # Default to True for safety if identity fails

    if _instance is None:
        # ⚡ AUTONOMY: Try to resolve dependencies if not provided
        if state_cache_manager is None:
            from oaSplinker.Core.splinker import ControlBroker
            broker = ControlBroker.get_instance()
            state_cache_manager = getattr(broker, 'state_cache_manager', None)
        
        if mqtt_connection_manager is None:
            from oaComMQTT.Managers.mqtt_connection import MqttConnectionManager
            mqtt_connection_manager = MqttConnectionManager()
            
        if subscriber_router is None:
            from oaComMQTT.Managers.mqtt_subscriber_router import MqttSubscriberRouter
            # Note: We don't use a singleton for router, but we can check the MQTT manager
            subscriber_router = getattr(mqtt_connection_manager, 'subscriber_router', None)

        _instance = SNMPManager(
            state_cache_manager=state_cache_manager, 
            mqtt_connection_manager=mqtt_connection_manager, 
            subscriber_router=subscriber_router,
            run_bridge=run_bridge
        )
    return _instance

def start():
    """Starts the SNMP bridge service."""
    manager = get_manager()
    manager.start()

def stop():
    """Stops the SNMP bridge service."""
    manager = get_manager()
    manager.stop()

def status():
    """Returns the current status of the SNMP bridge."""
    manager = get_manager()
    return manager.get_status()

def main():
    """
    Main entry point for running the SNMP Bridge as a standalone module.
    Useful for debugging or isolated service deployment.
    """
    from oaLogging.Core.logger import SNMP_LOGGER
    from oaOchestration.Core.path_initializer import initialize_paths
    from oaConfiguration.FileReaders.config_reader import Config
    
    initialize_paths()
    cfg = Config.get_instance()
    
    SNMP_LOGGER.info("🚀 [SNMP] Launching Standalone SNMP Module...")
    
    # In standalone mode, we might need to initialize the MQTT connection manually
    from oaComMQTT.Managers.mqtt_connection import MqttConnectionManager
    from oaComMQTT.Managers.mqtt_subscriber_router import MqttSubscriberRouter
    from oaStateCache.Core.state_cache import StateRegistry
    
    mqtt_conn = MqttConnectionManager()
    sub_router = MqttSubscriberRouter()
    state_cache = StateRegistry(mqtt_conn)
    state_cache.subscriber_router = sub_router
    
    # Start MQTT first so SNMP can use it
    mqtt_conn.connect_to_broker(
        on_message_callback=state_cache.handle_incoming_mqtt,
        subscriber_router=sub_router
    )
    
    # Initialize the manager with our fresh services
    manager = get_manager(
        state_cache_manager=state_cache,
        mqtt_connection_manager=mqtt_conn,
        subscriber_router=sub_router,
        run_bridge=True
    )
    
    manager.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        SNMP_LOGGER.warning("👋 [SNMP] Standalone shutdown requested.")
        manager.stop()
        mqtt_conn.disconnect()

if __name__ == "__main__":
    main()

__all__ = [
    "SNMPManager",
    "SnmpTester",
    "MibGenerator",
    "InstallerGenerator",
    "get_manager",
    "start",
    "stop",
    "status",
    "main"
]
