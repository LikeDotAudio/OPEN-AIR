# oaPTP/Entry.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

"""
oaPTP/Entry.py - The sole orchestrator for the PTP Module.

Purpose:
This file is the public entry point for 'oaPTP'. It manages the 
lifecycle of the PTP sniffer and provides high-level 
monitoring and control interfaces.
"""

from .Core.ptp import PtpManager

_instance = None

def get_manager(mqtt_connection_manager=None, subscriber_router=None):
    """Returns the singleton PtpManager instance."""
    global _instance
    if _instance is None:
        _instance = PtpManager(mqtt_connection_manager, subscriber_router)
    return _instance

def start(mqtt_connection_manager=None, subscriber_router=None):
    """
    Initializes and starts the PTP service.
    """
    manager = get_manager(mqtt_connection_manager, subscriber_router)
    return manager.start()

def stop():
    """
    Shuts down the PTP service.
    """
    if _instance:
        _instance.stop()

def status():
    """Returns the current status of the PTP manager."""
    return "running" if _instance and _instance.sniffer_thread and _instance.sniffer_thread.is_alive() else "stopped"

# Standardized exports
__all__ = [
    "PtpManager",
    "get_manager",
    "start",
    "stop",
    "status"
]
