from loguru import logger

class FleetCommandQueueMixin:
    """Provides a thread-safe interface for routing commands to specific devices."""

    def enqueue_command(self, serial, command, query=False, correlation_id="N/A"):
        """
        Sends a SCPI command or query to a specific instrument by its serial number.
        """
        proxy = self.discovery_orchestrator.get_proxy_for_device(serial)
        if proxy:
            proxy.enqueue_command(command, query, correlation_id)
        else:
            self.cb_error(serial, "Device not found in fleet manager", command)
