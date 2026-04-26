# Core/fleet_command_manager.py
# Author: Anthony Peter Kuzub
# Version: 2.0.0
#
# Description: Refactored Command Manager (Composition over Inheritance).


class CommandQueueManager:
    """Provides a thread-safe interface for routing commands to specific devices."""

    def __init__(self, orchestrator):
        self._orchestrator = orchestrator

    def enqueue_command(self, serial, command, query=False, correlation_id="N/A"):
        """
        Sends a SCPI command or query to a specific instrument by its serial number.
        """
        proxy = self._orchestrator.discovery_orchestrator.get_proxy_for_device(serial)
        if proxy:
            proxy.enqueue_command(command, query, correlation_id)
        else:
            self._orchestrator.cb_error(serial, "Device not found in fleet manager", command)
