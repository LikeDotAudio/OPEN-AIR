# oaComSNMP/Entry.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

"""
oaComSNMP/Entry.py - The sole orchestrator for the SNMP Communication Module.
"""

from .Managers.snmp_manager import SNMPManager
from .Workers.snmp_tester import SnmpTester
from .Methods.snmp_mib_generator import MibGenerator
from .Methods.snmp_installer_generator import InstallerGenerator

_instance = None

def get_manager(state_cache_manager=None, mqtt_connection_manager=None, run_bridge=True):
    global _instance
    if _instance is None:
        _instance = SNMPManager(
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
    "SNMPManager",
    "SnmpTester",
    "MibGenerator",
    "InstallerGenerator",
    "get_manager",
    "start",
    "stop",
    "status"
]
