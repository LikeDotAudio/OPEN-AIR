# oaComREST/Entry.py
# Author: Anthony Peter Kuzub
# Version: 20260328.1200.1
#
# Description: Public entry point for the REST API module.

from loguru import logger
from .Managers.rest_manager import RESTManager
from .Constants.rest_constants import LOCAL_DEBUG

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
        if LOCAL_DEBUG:
            logger.debug("📡⚙️🔗 [REST] Creating singleton RESTManager instance.")
        _manager = RESTManager(state_cache_manager, protocol_router)
    return _manager

def start(state_cache_manager=None, protocol_router=None):
    """Convenience function to start the REST service."""
    if LOCAL_DEBUG:
        logger.debug("📡⚙️🚀 [REST] Manual service start initiated via Entry.")
    return get_manager(state_cache_manager, protocol_router).start()

def stop():
    """Convenience function to stop the REST service."""
    if _manager:
        if LOCAL_DEBUG:
            logger.debug("📡⚙️🛑 [REST] Manual service stop initiated via Entry.")
        _manager.stop()

def get_status():
    """Convenience function to get the current REST service status."""
    if _manager:
        return _manager.get_status()
    
    # Return a consistent minimal status object
    from .Constants.rest_constants import REST_HOST, REST_PORT
    return {
        "running": False,
        "local_host": False,
        "sibling_host": False,
        "should_run": False,
        "initialized": False,
        "host": REST_HOST,
        "port": REST_PORT,
        "url": f"http://{REST_HOST}:{REST_PORT}",
        "docs_url": f"http://{REST_HOST}:{REST_PORT}/docs",
        "routes": []
    }

def add_monitor_callback(callback):
    """Registers a callback for real-time activity monitoring."""
    if _manager:
        _manager.add_monitor_callback(callback)

def remove_monitor_callback(callback):
    """Removes a previously registered monitor callback."""
    if _manager:
        _manager.remove_monitor_callback(callback)

__all__ = ["RESTManager", "get_manager", "start", "stop", "get_status", "add_monitor_callback", "remove_monitor_callback"]
