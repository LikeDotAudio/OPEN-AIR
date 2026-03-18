"""
oaComBroker/Entry.py - The sole orchestrator for the Communication Broker.

Purpose:
This file is the public entry point for 'oaComBroker'. It manages 
the lifecycle of the Protocol Router and the core hardware-facing 
partition logic.
"""

from .Managers.protocol_router import ProtocolRouter
from .Core import open_air_core

def get_router_instance():
    """Returns the singleton ProtocolRouter instance."""
    return ProtocolRouter.get_instance()

def start_core_services():
    """
    Launches the safety-critical core services for OPEN-AIR.
    """
    return open_air_core.main()

# Standardized exports
__all__ = [
    "ProtocolRouter", 
    "get_router_instance", 
    "start_core_services"
]
