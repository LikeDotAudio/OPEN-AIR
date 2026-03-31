# oaComBroker/Entry.py
#
# The sole orchestrator and public gatekeeper for the Communication Broker.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Professional services for customizing and tailoring this software to your specific
# application can be negotiated. There is no charge to use, modify, or fork this software.
#
# Build Log: https://like.audio/category/software/spectrum-scanner/
# Source Code: https://github.com/APKaudio/
# Feature Requests can be emailed to i @ like . audio
#
# Version 20260328.1620.1
#
# Description:
# This module acts as the Gatekeeper for the oaComBroker subsystem. It abstracts
# the complexities of the multi-protocol routing engine and provides a unified
# interface for lifecycle management. Following the Partitioned Architecture,
# this file resides in the module root as the only permitted entry point.
#
# Architectural Role:
# - Orchestrates the initialization of Core services.
# - Provides access to the Singleton ProtocolRouter.
# - Exports the FailoverManager for redundancy control.
# - Manages high-level status and lifecycle hooks.

from .Core.protocol_router.router import ProtocolRouter
from .Managers.Failover.Manager import FailoverManager
from .Core import open_air_core

def get_router_instance():
    """
    Allocates or retrieves the singleton ProtocolRouter instance.
    
    Returns:
        ProtocolRouter: The active routing engine instance.
    """
    return ProtocolRouter.get_instance()

def start_core_services():
    """
    Initializes the safety-critical core services for OPEN-AIR.
    
    This function triggers the boot sequence for hardware-facing logic 
    and protocol listeners. It should only be called once during the 
    application startup phase.
    
    Returns:
        int: Success (0) or Error Code.
    """
    return open_air_core.main()

# Standardized exports for the Gatekeeper pattern.
__all__ = [
    "ProtocolRouter", 
    "FailoverManager",
    "get_router_instance", 
    "start_core_services"
]
