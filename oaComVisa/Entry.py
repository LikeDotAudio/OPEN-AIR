# oaComVisa/Entry.py
# Author: Anthony Peter Kuzub
# Version: 20260330.1000.1 # Updated version for structure change
#
# Description: VISA Communication Module Entry Point.

"""
oaComVisa/Entry.py - The sole orchestrator for the VISA Communication Module.

Purpose:
This file is the public entry point for 'oaComVisa'. It manages the
lifecycle of VISA instrument connections.
"""

from .Managers.discovery_orchestrator import DiscoveryOrchestrator
from .Managers.visa_manager import VisaManagerOrchestrator
from .Core.visa_proxy import VisaProxy
from .Core.visa_proxy_fleet import VisaProxyFleet
from .Core.visa_fleet import FleetOrchestrator

class VisaComEntry:
    """Entry point for VISA communication management."""
    def __init__(self):
        print("📡📥📥 [INBOUND] Initializing VisaComEntry...")
        # Placeholder for initialization logic, e.g., setting up managers
        self.discovery_orchestrator = None
        self.visa_manager = None
        self.fleet_orchestrator = None
        pass

    def start(self):
        """Starts the VISA communication services."""
        print("🚀 [VISA] Starting VISA communication...")
        # Example: Initialize managers if they aren't already
        # if not self.discovery_orchestrator:
        #     self.discovery_orchestrator = DiscoveryOrchestrator(...)
        # if not self.visa_manager:
        #     self.visa_manager = VisaManagerOrchestrator(...)
        # if not self.fleet_orchestrator:
        #     self.fleet_orchestrator = FleetOrchestrator(...)
        # ... actual start logic ...
        pass

    def stop(self):
        """Stops the VISA communication services."""
        print("🛑 [VISA] Stopping VISA communication...")
        # Placeholder for actual stop logic
        pass

    def status(self):
        """Returns the current status of the VISA communication services."""
        print("ℹ️ [VISA] Checking VISA communication status...")
        # Placeholder for actual status check logic
        return "idle" # Example status

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
    "VisaComEntry",
    "DiscoveryOrchestrator",
    "VisaManagerOrchestrator",
    "VisaProxy",
    "VisaProxyFleet",
    "FleetOrchestrator",
    "get_discovery_orchestrator",
    "get_visa_manager",
    "get_fleet_orchestrator"
]
