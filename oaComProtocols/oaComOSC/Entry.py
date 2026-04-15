# oaComProtocols.oaComOSC/Entry.py
#
# The sole orchestrator and public gatekeeper for the OSC Communication Module.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Version 20260329.1105.1
#
# Description:
# This file serves as the gatekeeper and primary interface for all OSC-related
# operations. It manages the singleton OSCManager and exposes high-level 
# methods for control and interaction.
# Refactored for centralized management by ComProtocolManager, with self-contained MQTT if needed.

import sys
import os
import pathlib
import argparse
from pathlib import Path
import threading # For potential internal thread management if needed

# Ensure root directory is in the search path
current_dir = pathlib.Path(__file__).resolve().parent
project_root = current_dir.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from oaLogging.Methods.matrix_gate import matrix_log

# --- Core Components ---
# These managers will be instantiated and managed by the ComProtocolManager
# OSCManager, OscRxServer, OscTxClient

_instance = None

# Mock dependencies if not provided by the manager
class MockContext: pass
class MockStateCache: 
    def handle_external_update(self, *args, **kwargs): pass
    def shutdown(self): pass

class MockMqttConnectionManager: 
    def connect_to_broker(self, *args, **kwargs): pass
    def disconnect(self): pass
    def subscribe(self, *args, **kwargs): pass
    def publish(self, *args, **kwargs): pass

class MockSubscriberRouter:
    def add_handler(self, *args, **kwargs): pass

def get_manager(context=None, state_cache_manager=None, mqtt_connection_manager=None, subscriber_router=None, run_bridge=True):
    """
    Returns the singleton OSCManager instance.
    If not already initialized, it creates it with the provided managers.
    Dependencies should be passed externally. If MQTT connection is not provided,
    OSCManager will manage its own internal connection.
    """
    global _instance
    
    # ⚡ ROBUST SINGLETON: Check if the manager is already initialized in another 
    # copy of this module (happens when run as __main__ and imported as a package)
    if _instance is None:
        try:
            # Attempt to import from a potentially different instance if available
            import oaComProtocols.oaComOSC.Entry as osc_entry
            if osc_entry is not sys.modules[__name__] and osc_entry._instance:
                _instance = osc_entry._instance
        except (ImportError, AttributeError):
            pass # Continue with fresh initialization

    if _instance is None:
        from oaComProtocols.oaComOSC.Managers.osc_manager import OSCManager
        
        # Provide mocks if not supplied by the orchestrator
        context = context if context else MockContext()
        state_cache = state_cache_manager if state_cache_manager else MockStateCache()
        # MQTT connection manager will be created internally if not provided
        mqtt_conn = mqtt_connection_manager if mqtt_connection_manager else None 
        # subscriber_router is not directly used by OSCManager's init in this snippet
            
        _instance = OSCManager(
            context=context,
            state_cache_manager=state_cache, 
            mqtt_connection_manager=mqtt_conn, # Will be None if not provided externally
            run_bridge=run_bridge
        )
        matrix_log("comms", "osc", "get_manager", "OSCManager initialized.", "DEBUG")
    else:
        # Update existing instance if new dependencies are provided
        if context: _instance.context = context
        if state_cache_manager: _instance.state_cache_manager = state_cache_manager
        if mqtt_connection_manager: _instance.mqtt_connection_manager = mqtt_connection_manager
            
    return _instance

def start(context=None, state_cache_manager=None, mqtt_connection_manager=None, subscriber_router=None, run_bridge=True):
    """
    Starts the OSC bridge services, accepting external dependencies.
    If mqtt_connection_manager is not provided, OSCManager will initialize its own.
    """
    matrix_log("comms", "osc", "start", "🚀 [OSC] Starting OSC bridge services...", "INFO")
    manager = get_manager(
        context=context,
        state_cache_manager=state_cache_manager,
        mqtt_connection_manager=mqtt_connection_manager,
        subscriber_router=subscriber_router,
        run_bridge=run_bridge
    )
    manager.start()
    matrix_log("comms", "osc", "start", "OSC Bridge services started.", "INFO")

def stop():
    """Stops the OSC bridge services."""
    global _instance
    if _instance:
        _instance.stop()
        _instance = None
        matrix_log("comms", "osc", "stop", "OSC Bridge services stopped.", "INFO")

def status():
    """Returns the current status of the OSC bridge."""
    manager = get_manager()
    if manager:
        return manager.get_status()
    return {"running": False, "error": "OSC manager not initialized"}

def send(address, value, meta=None):
    """
    High-level method to send an OSC message.
    Can be called directly from the UI or other modules.
    """
    manager = get_manager()
    manager.send(address, value, meta)

def add_monitor_callback(callback):
    """Registers a callback for OSC activity monitoring."""
    manager = get_manager()
    manager.add_monitor_callback(callback)

def remove_monitor_callback(callback):
    """Unregisters a monitoring callback."""
    manager = get_manager()
    manager.remove_monitor_callback(callback)

def set_bridge_mode(enabled):
    """Toggles bridge mode on the singleton instance."""
    manager = get_manager()
    manager.set_bridge_mode(enabled)

# Standalone main() function is removed.
# def run_tests(): ...
# if __name__ == "__main__": ...

__all__ = [
    "OSCManager",
    "OscRxServer",
    "OscTxClient",
    "get_manager",
    "start",
    "stop",
    "status",
    "send",
    "add_monitor_callback",
    "remove_monitor_callback",
    "set_bridge_mode"
]
