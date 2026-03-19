"""
oaComAES70/Entry.py - The sole orchestrator for the AES70 Communication Module.

Purpose:
This file is the public entry point for 'oaComAES70'. It manages the 
lifecycle of the AES70/OCA connection and provides high-level 
monitoring and control interfaces.
"""

from .Core.aes70 import AES70Manager

_instance = None

def get_manager(state_cache=None, run_bridge=True):
    """Returns the singleton AES70Manager instance."""
    global _instance
    if _instance is None:
        _instance = AES70Manager(state_cache, run_bridge)
    return _instance

def start(state_cache=None):
    """
    Initializes and starts the AES70 service.
    """
    manager = get_manager(state_cache)
    return manager.start()

def stop():
    """
    Shuts down the AES70 service.
    """
    if _instance:
        _instance.stop()

def status():
    """Returns the current status of the AES70 manager."""
    # Logic to derive status from manager state
    return "running" if _instance else "stopped"

# Standardized exports
__all__ = [
    "AES70Manager",
    "get_manager",
    "start",
    "stop",
    "status"
]
