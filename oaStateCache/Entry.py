# oaStateCache/Entry.py
#
# The sole orchestrator for the State Cache Module. It manages the 
# lifecycle of the StateRegistry and StateMirrorEngine.
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
# Version 20260406.2000.1

"""
oaStateCache/Entry.py - The sole orchestrator for the State Cache Module.
"""

from .Core.state_cache import StateRegistry
from .Core.state_mirror_engine import StateMirrorEngine

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
    "StateMirrorEngine",
    "get_registry",
    "start",
    "stop",
    "status"
]
