# oaComOSC/Entry.py
# Author: Anthony Peter Kuzub
# Version: 20260325.1200.1
#
# Description: The sole orchestrator and public API for the OSC Communication Module.

"""
oaComOSC/Entry.py - The Heart and Soul of the OSC Module.

This file serves as the gatekeeper and primary interface for all OSC-related
operations. It manages the singleton OSCManager and exposes high-level 
methods for control and interaction.
"""

from .Managers.osc_manager import OSCManager
from .Workers.osc_rx_server import OscRxServer
from .Workers.osc_tx_client import OscTxClient

_instance = None

def get_manager(state_cache_manager=None, mqtt_connection_manager=None, run_bridge=True):
    """
    Returns the singleton OSCManager instance.
    If not already initialized, it creates it with the provided managers.
    If called without managers, it relies on OSCManager's internal fallbacks.
    """
    global _instance
    if _instance is None:
        _instance = OSCManager(
            state_cache_manager=state_cache_manager, 
            mqtt_connection_manager=mqtt_connection_manager, 
            run_bridge=run_bridge
        )
    else:
        # ⚡ STANDALONE: Update existing instance if new dependencies are provided
        if state_cache_manager:
            _instance.state_cache_manager = state_cache_manager
        if mqtt_connection_manager:
            _instance.mqtt_connection_manager = mqtt_connection_manager
            
    return _instance

def start():
    """Starts the OSC bridge services."""
    manager = get_manager()
    manager.start()

def stop():
    """Stops the OSC bridge services."""
    manager = get_manager()
    manager.stop()

def status():
    """Returns the current status of the OSC bridge."""
    manager = get_manager()
    return manager.get_status()

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

# Standardized exports
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
