# oaComSMPTE2138/Entry.py
#
# Gatekeeper for the SMPTE ST 2138 (SMPTE2138) Communication Module. 
# Orchestrates translation (Bridge) and observation (Monitor) services.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Version 20260330.1600.1

from .Managers.smpte2138_bridge_manager import SMPTE2138BridgeManager
from .Managers.smpte2138_monitor_manager import SMPTE2138MonitorManager

__all__ = ["SMPTE2138BridgeManager", "SMPTE2138MonitorManager"]

def start_bridge(mqtt_connection, subscriber_router):
    """
    Initializes the SMPTE2138 Bridge Manager (Internal -> External).
    Used in the Core Partition.
    """
    return SMPTE2138BridgeManager(mqtt_connection, subscriber_router)

def start_monitor(mqtt_connection, subscriber_router):
    """
    Initializes the SMPTE2138 Monitor Manager (External -> Human Readable).
    Used in the UI Partition.
    """
    return SMPTE2138MonitorManager(mqtt_connection, subscriber_router)
