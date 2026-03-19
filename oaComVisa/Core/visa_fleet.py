# managers/Visa_Fleet/visa_fleet.py
# Modularized VISA Fleet Manager.
# Version 20260315.Modular.1

import threading
from loguru import logger

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True
from oaLogging.Core.logger import builder_logger
from oaConfiguration.FileReaders.config_reader import Config
app_constants = Config.get_instance()

# Note: DiscoveryOrchestrator is imported from discovery_agents
from ..Managers.discovery_orchestrator import DiscoveryOrchestrator
from ..FileWriters.visa_json import VisaJsonBuilder
from ..Managers.fleet_mqtt_bridge import MqttFleetBridge
from ..FileWriters.visa_csv import VisaCsvBuilder

# --- EXTRACTED CORE MODULES ---
from .fleet_command_queue_mixin import FleetCommandQueueMixin
from .fleet_inventory_mixin import FleetInventoryMixin
from .fleet_scan_mixin import FleetScanMixin

class FleetOrchestrator(FleetCommandQueueMixin, FleetInventoryMixin, FleetScanMixin):
    """Commander for the VISA instrument fleet, managing discovery and communication."""
    
    def __init__(self, mqtt_connection_manager=None, subscriber_router=None, aes70_manager=None):
        if LOCAL_DEBUG: logger.debug("💳🚢🔍 [VISA] Initializing FleetOrchestrator.")

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
        
        self._running = False
        self.initial_scan_complete_event = threading.Event()

        if LOCAL_DEBUG: logger.success("✅ [SUCCESS] FleetOrchestrator initialized.")

    def set_callbacks(self, on_inventory_update, on_device_response, on_device_error, on_proxy_status):
        self.cb_inventory = on_inventory_update
        self.cb_response = on_device_response
        self.cb_error = on_device_error
        self.cb_status = on_proxy_status

    def start(self):
        self._running = True
        if LOCAL_DEBUG: logger.debug("💳🚢🔍 [VISA] FleetOrchestrator Started.")

    def stop(self):
        self._running = False
        if self.discovery_orchestrator: self.discovery_orchestrator.shutdown()
        if self.mqtt_bridge: self.mqtt_bridge.disconnect()
        if LOCAL_DEBUG: logger.debug("💳🚢🔍 [VISA] FleetOrchestrator Stopped.")
