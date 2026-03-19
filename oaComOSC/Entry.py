"""
oaComOSC/Entry.py - The sole orchestrator for the OSC Communication Module.
"""

from .Managers.osc_manager import OSCManager
from .Workers.osc_rx_server import OscRxServer
from .Workers.osc_tx_client import OscTxClient

_instance = None

def get_manager(state_cache_manager=None, mqtt_connection_manager=None, run_bridge=True):
    global _instance
    if _instance is None:
        _instance = OSCManager(
            state_cache_manager=state_cache_manager, 
            mqtt_connection_manager=mqtt_connection_manager, 
            run_bridge=run_bridge
        )
    return _instance

def start():
    manager = get_manager()
    manager.start()

def stop():
    manager = get_manager()
    manager.stop()

def status():
    manager = get_manager()
    return manager.get_status()

__all__ = [
    "OSCManager",
    "OscRxServer",
    "OscTxClient",
    "get_manager",
    "start",
    "stop",
    "status"
]
