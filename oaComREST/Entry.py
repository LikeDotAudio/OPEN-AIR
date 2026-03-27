# oaComREST/Entry.py
# Author: Anthony Peter Kuzub
# Version: 20260326.1200.1
#
# Description: Public entry point for the REST API module.

from .Managers.rest_manager import RESTManager

_manager = None

def get_manager(state_cache_manager=None, protocol_router=None):
    """
    Singleton accessor for the RESTManager.
    
    Inputs:
        state_cache_manager (StateRegistry): The system state cache.
        protocol_router (ProtocolRouter): The system command router.
        
    Outputs:
        RESTManager: The active manager instance.
    """
    global _manager
    if _manager is None:
        _manager = RESTManager(state_cache_manager, protocol_router)
    return _manager

def start(state_cache_manager=None, protocol_router=None):
    """Convenience function to start the REST service."""
    return get_manager(state_cache_manager, protocol_router).start()

def stop():
    """Convenience function to stop the REST service."""
    if _manager:
        _manager.stop()

def get_status():
    """Convenience function to get the current REST service status."""
    if _manager:
        return _manager.get_status()
    return {"running": False}

def add_monitor_callback(callback):
    """Registers a callback for real-time activity monitoring."""
    if _manager:
        _manager.add_monitor_callback(callback)

def remove_monitor_callback(callback):
    """Removes a previously registered monitor callback."""
    if _manager:
        _manager.remove_monitor_callback(callback)

__all__ = ["RESTManager", "get_manager", "start", "stop", "get_status", "add_monitor_callback", "remove_monitor_callback"]
