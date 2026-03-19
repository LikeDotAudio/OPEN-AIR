"""
oaStateCache/Entry.py - The sole orchestrator for the State Cache Module.

Purpose:
This file is the public entry point for 'oaStateCache'. It manages the 
lifecycle of the StateRegistry and provides high-level 
monitoring and control interfaces for state persistence.
"""

from .Core.state_cache import StateRegistry

_instance = None

def get_registry(mqtt_connection_manager=None, state_mirror_engine=None):
    """Returns the singleton StateRegistry instance."""
    global _instance
    if _instance is None:
        _instance = StateRegistry(mqtt_connection_manager, state_mirror_engine)
    return _instance

def start(mqtt_connection_manager=None, state_mirror_engine=None):
    """
    Initializes and starts the State Cache service.
    """
    registry = get_registry(mqtt_connection_manager, state_mirror_engine)
    registry.initialize_state()
    return registry

def stop():
    """
    Shuts down the State Cache service.
    """
    if _instance:
        _instance.shutdown()

def status():
    """Returns the current status of the State Registry."""
    return "active" if _instance else "stopped"

# Standardized exports
__all__ = [
    "StateRegistry",
    "get_registry",
    "start",
    "stop",
    "status"
]
