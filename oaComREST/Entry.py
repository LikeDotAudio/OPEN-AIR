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

__all__ = ["RESTManager", "get_manager", "start", "stop"]
