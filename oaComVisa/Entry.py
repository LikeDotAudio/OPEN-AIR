# oaComVisa/Entry.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

"""
oaComVisa/Entry.py - The sole orchestrator for the VISA Communication Module.
"""

from .Managers.discovery_orchestrator import DiscoveryOrchestrator
from .Managers.visa_manager import VisaManagerOrchestrator
from .Core.visa_proxy import VisaProxy
from .Core.visa_proxy_fleet import VisaProxyFleet
from .Core.visa_fleet import FleetOrchestrator

def get_discovery_orchestrator(manager_ref, aes70_manager=None):
    """Returns a new DiscoveryOrchestrator instance."""
    return DiscoveryOrchestrator(manager_ref, aes70_manager)

def get_visa_manager(mqtt_connection_manager, subscriber_router):
    """Returns a new VisaManagerOrchestrator instance."""
    return VisaManagerOrchestrator(mqtt_connection_manager, subscriber_router)

def get_fleet_orchestrator(mqtt_connection_manager=None, subscriber_router=None, aes70_manager=None):
    """Returns a new FleetOrchestrator instance."""
    return FleetOrchestrator(mqtt_connection_manager, subscriber_router, aes70_manager)

__all__ = [
    "DiscoveryOrchestrator",
    "VisaManagerOrchestrator",
    "VisaProxy",
    "VisaProxyFleet",
    "FleetOrchestrator",
    "get_discovery_orchestrator",
    "get_visa_manager",
    "get_fleet_orchestrator"
]
