# oaSplinker/Entry.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

"""
oaSplinker/Entry.py - The sole orchestrator for the Splinker Module.

Purpose:
This file is the public entry point for 'oaSplinker'. It manages the 
lifecycle of the ControlBroker and provides high-level 
monitoring and control interfaces for decoupled control.
"""

from .Core.splinker import ControlBroker

def get_broker(state_cache_manager=None, mqtt_manager=None):
    """Returns the singleton ControlBroker instance."""
    return ControlBroker.get_instance(state_cache_manager, mqtt_manager)

def start(state_cache_manager=None, mqtt_manager=None):
    """
    Initializes the Splinker service.
    """
    return get_broker(state_cache_manager, mqtt_manager)

def status():
    """Returns the current status of the Splinker broker."""
    broker = get_broker()
    return "running" if broker and not broker.panic_active else "panic" if broker and broker.panic_active else "stopped"

# Standardized exports
__all__ = [
    "ControlBroker",
    "get_broker",
    "start",
    "status"
]
