import inspect

# Core/visa_fleet.py
# Author: Anthony Peter Kuzub
# Version: 2.0.0
#
# Description: Refactored VISA Fleet Manager (Composition over Inheritance).
from oaConfigurationManager.FileReaders.config_reader import Config

# --- Standard Debug Logging Setup ---
from oaLogging.Methods.matrix_gate import matrix_log

app_constants = Config.get_instance()

# Note: DiscoveryOrchestrator is imported from discovery_agents
from ..FileWriters.visa_csv import VisaCsvBuilder
from ..FileWriters.visa_json import VisaJsonBuilder
from ..Managers.discovery_orchestrator import DiscoveryOrchestrator
from ..Managers.fleet_mqtt_bridge import MqttFleetBridge

# --- Refactored Core Managers ---
from .fleet_command_manager import CommandQueueManager
from .fleet_inventory_manager import InventoryManager
from .fleet_scan_manager import ScanManager


class FleetOrchestrator:
    """Commander for the VISA instrument fleet, managing discovery and communication."""

    def __init__(self, mqtt_connection_manager=None, subscriber_router=None, aes70_manager=None):
        matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "💳🚢🔍 [VISA] Initializing FleetOrchestrator.", "DEBUG")

        self.json_builder = VisaJsonBuilder()
        self.csv_builder = VisaCsvBuilder()
        self.mqtt_bridge = MqttFleetBridge(
            mqtt_connection_manager=mqtt_connection_manager,
            subscriber_router=subscriber_router,
            topic_prefix=app_constants.get_mqtt_base_topic(),
        )
        self.mqtt_bridge.on_scan_trigger = self.trigger_scan

        self.cb_inventory = lambda x: None
        self.cb_response = lambda s, r, c, i: None
        self.cb_error = lambda s, m, c: None
        self.cb_status = lambda s, st: None

        self._current_inventory = self.json_builder.load_inventory_from_json()
        self.discovery_orchestrator = DiscoveryOrchestrator(manager_ref=self, aes70_manager=aes70_manager)

        # Initialize Composed Managers
        self._command_manager = CommandQueueManager(self)
        self._inventory_manager = InventoryManager(self)
        self._scan_manager = ScanManager(self)

        self._running = False

        matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "✅ [SUCCESS] FleetOrchestrator initialized.", "SUCCESS")

    # --- Delegated Properties and Methods (Public API Compatibility) ---

    @property
    def current_inventory(self):
        return self._inventory_manager.current_inventory

    @property
    def initial_scan_complete_event(self):
        return self._scan_manager.initial_scan_complete_event

    def enqueue_command(self, *args, **kwargs):
        return self._command_manager.enqueue_command(*args, **kwargs)

    def trigger_scan(self):
        return self._scan_manager.trigger_scan()

    def wait_for_initial_scan(self, *args, **kwargs):
        return self._scan_manager.wait_for_initial_scan(*args, **kwargs)

    # Internal notification methods for discovery_orchestrator
    def _notify_inventory(self, data): self._inventory_manager.notify_inventory(data)
    def _notify_response(self, *args): self._inventory_manager.notify_response(*args)
    def _notify_error(self, *args): self._inventory_manager.notify_error(*args)
    def _notify_status(self, *args): self._inventory_manager.notify_status(*args)

    # --- Lifecycle Methods ---

    def set_callbacks(self, on_inventory_update, on_device_response, on_device_error, on_proxy_status):
        self.cb_inventory = on_inventory_update
        self.cb_response = on_device_response
        self.cb_error = on_device_error
        self.cb_status = on_proxy_status

    def start(self):
        self._running = True
        matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "💳🚢🔍 [VISA] FleetOrchestrator Started.", "DEBUG")

    def stop(self):
        self._running = False
        if self.discovery_orchestrator: self.discovery_orchestrator.shutdown()
        if self.mqtt_bridge: self.mqtt_bridge.disconnect()
        matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "💳🚢🔍 [VISA] FleetOrchestrator Stopped.", "DEBUG")
