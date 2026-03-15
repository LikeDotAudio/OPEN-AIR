# managers/Visa_Fleet_Manager/visa_fleet_manager.py
#
# Orchestrates the discovery and management of VISA-compatible instruments.
#
# Primary Responsibilities:
# - Coordinating instrument discovery via the DiscoveryOrchestrator.
# - Managing an inventory of fleet devices in JSON and CSV formats.
# - Bridging fleet data and commands between the core logic and MQTT.
# - Providing a thread-safe interface for sending commands to specific devices.
#
# Assumptions and Constraints:
# - Assumes availability of the VisaJsonBuilder, VisaCsvBuilder, and MqttFleetBridge.
# - Depends on a DiscoveryOrchestrator to handle low-level device interactions.
# - Relies on external configuration via the Config manager.
# - Standardizes on JSON for internal state persistence.
#
# Author: Gemini Agent / Anthony Peter Kuzub

import threading
import time
import inspect
import orjson
import os
import string
import datetime

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True    # Set to False in production, True for dev on this file
from workers.logger.logger import initialize_logging, set_log_directory
from loguru import logger

from managers.configini.config_reader import Config

app_constants = Config.get_instance()

# Note: DiscoveryOrchestrator is expected to be available in the same package
from managers.Visa_Fleet_Manager import DiscoveryOrchestrator
from managers.Visa_Fleet_Manager.manager_visa_json_builder import VisaJsonBuilder
from managers.Visa_Fleet_Manager.manager_fleet_mqtt_bridge import MqttFleetBridge
from managers.Visa_Fleet_Manager.manager_visa_csv_builder import VisaCsvBuilder

class VisaFleetManager:
    """
    Commander for the VISA instrument fleet, managing discovery and communication.
    """
    def __init__(self, mqtt_connection_manager=None, subscriber_router=None, 
                 aes70_manager=None):
        """
        Initializes the VisaFleetManager and its constituent components.

        Parameters:
        - mqtt_connection_manager: Instance for MQTT communication.
        - subscriber_router: Instance for routing MQTT subscriptions.
        - aes70_manager: Optional manager for AES70-specific device discovery.

        Returns:
        - A new VisaFleetManager instance.

        Side Effects & Thread-Safety:
        - Loads initial inventory from local JSON storage.
        - Initializes the MQTT bridge and registers scan trigger callbacks.
        """
        if LOCAL_DEBUG:
            logger.debug("💳🚢🔍 [VISA] Initializing VisaFleetManager. "
                         "The commander of the fleet is online!")

        self.json_builder = VisaJsonBuilder()
        self.csv_builder = VisaCsvBuilder()
        self.mqtt_bridge = MqttFleetBridge(
            mqtt_connection_manager=mqtt_connection_manager,
            subscriber_router=subscriber_router,
            topic_prefix=app_constants.get_mqtt_base_topic(),
        )
        
        # Link MQTT scan requests to the internal scan logic.
        self.mqtt_bridge.on_scan_trigger = self.trigger_scan

        # Initialize callbacks with no-op functions to avoid NULL checks.
        self.cb_inventory = lambda x: None
        self.cb_response = lambda s, r, c, i: None
        self.cb_error = lambda s, m, c: None
        self.cb_status = lambda s, st: None

        # Load existing fleet state to ensure continuity across restarts.
        self._current_inventory = self.json_builder.load_inventory_from_json()

        self.discovery_orchestrator = DiscoveryOrchestrator(
            manager_ref=self, 
            aes70_manager=aes70_manager
        )
        self._running = False
        self.initial_scan_complete_event = threading.Event()

        if LOCAL_DEBUG:
            logger.success("✅✅✅ [SUCCESS] VisaFleetManager initialized. "
                           "Orchestrator ready.")

    def set_callbacks(self, on_inventory_update, on_device_response, 
                      on_device_error, on_proxy_status):
        """
        Links external listeners (GUI or higher-level logic) to fleet events.

        Parameters:
        - on_inventory_update: Callable(inventory_list).
        - on_device_response: Callable(serial, response, command, correlation_id).
        - on_device_error: Callable(serial, message, command).
        - on_proxy_status: Callable(serial, status).

        Returns:
        - None.

        Side Effects & Thread-Safety:
        - Updates internal callback references.
        """
        self.cb_inventory = on_inventory_update
        self.cb_response = on_device_response
        self.cb_error = on_device_error
        self.cb_status = on_proxy_status

    def start(self):
        """
        Activates the fleet manager.

        Returns:
        - None.
        """
        self._running = True
        if LOCAL_DEBUG:
            logger.debug("💳🚢🔍 [VISA] VisaFleetManager Started "
                         "(Standalone Mode).")

    def stop(self):
        """
        Gracefully shuts down the orchestrator and disconnects from MQTT.

        Returns:
        - None.

        Side Effects & Thread-Safety:
        - Stops the discovery orchestrator and its background threads.
        - Disconnects the MQTT bridge.
        """
        self._running = False
        if self.discovery_orchestrator:
            self.discovery_orchestrator.shutdown()
        if self.mqtt_bridge:
            self.mqtt_bridge.disconnect()
        if LOCAL_DEBUG:
            logger.debug("💳🚢🔍 [VISA] VisaFleetManager Stopped.")

    def trigger_scan(self):
        """
        Initiates a comprehensive network scan for VISA instruments.

        Returns:
        - None.

        Side Effects & Thread-Safety:
        - Clears the `initial_scan_complete_event`.
        - Publishes scan status messages to MQTT.
        - May take significant time depending on network size.
        """
        self.initial_scan_complete_event.clear()
        if LOCAL_DEBUG:
            logger.debug("💳🚢🔍 [VISA] Scan Triggered via API.")
            
        self._publish_scan_status("Start", {"status": "scanning"})
        try:
            num_devices_found = self.discovery_orchestrator.scan_and_manage_fleet()
            self._publish_scan_status(
                "Complete", 
                {"status": "ready", "num_devices": num_devices_found}
            )
        except Exception as e:
            # Gravity of Errors: Non-gated failure reporting.
            import traceback
            logger.exception(f"""💳🚢🔍 [VISA] CRITICAL: Fleet scan failed.
Forensic Report:
{traceback.format_exc()}""")
        
        self.initial_scan_complete_event.set()

    def wait_for_initial_scan(self, timeout=None):
        """
        Blocks the calling thread until the first device scan completes.

        Parameters:
        - timeout: Maximum seconds to wait. NULL or negative for infinite.

        Returns:
        - True if the scan completed, False if the timeout was reached.

        Side Effects & Thread-Safety:
        - Blocks the execution of the calling thread.
        """
        if LOCAL_DEBUG:
            logger.debug("⏳ Waiting for initial VISA fleet scan to complete...")
        completed = self.initial_scan_complete_event.wait(timeout=timeout)
        if completed:
            if LOCAL_DEBUG:
                logger.success("✅ Initial VISA fleet scan complete.")
        else:
            if LOCAL_DEBUG:
                logger.debug("⚠️ Timed out waiting for initial VISA fleet scan.")
        return completed

    def _publish_scan_status(self, status, payload):
        """
        Sends scan progress information to the MQTT status topic.

        Parameters:
        - status: String representing the phase (e.g., "Start", "Complete").
        - payload: Dictionary of data to be serialized as JSON.

        Returns:
        - None.
        """
        if self.mqtt_bridge and self.mqtt_bridge.is_connected:
            topic = f"OPEN-AIR/System/Status/Fleet/{status}"
            self.mqtt_bridge.mqtt_manager.publish(
                topic, 
                orjson.dumps(payload).decode()
            )
            if LOCAL_DEBUG:
                logger.debug(f"Published scan status '{status}' to '{topic}'")

    def enqueue_command(self, serial, command, query=False, correlation_id="N/A"):
        """
        Sends a SCPI command or query to a specific instrument by its serial number.

        Parameters:
        - serial: The unique serial number of the target device.
        - command: The SCPI string to execute.
        - query: Boolean; if True, waits for and captures the instrument response.
        - correlation_id: Tracking ID for matching responses to requests.

        Returns:
        - None.

        Side Effects & Thread-Safety:
        - Queues the command in the device's proxy worker thread.
        - Triggers an error callback if the serial number is unknown.
        """
        proxy = self.discovery_orchestrator.get_proxy_for_device(serial)
        if proxy:
            proxy.enqueue_command(command, query, correlation_id)
        else:
            self.cb_error(serial, "Device not found in fleet manager", command)

    # --- Internal Event Handlers (Called by Supervisor/Proxies) ---

    def _notify_inventory(self, inventory_data):
        """
        Updates the global inventory and persists it to disk.

        Parameters:
        - inventory_data: List of raw device dictionaries from the orchestrator.

        Returns:
        - None.

        Side Effects & Thread-Safety:
        - Saves state to JSON and CSV files.
        - Triggers MQTT publication of the updated inventory.
        """
        augmented_inventory = []
        for device_entry in inventory_data:
            # Add human-friendly details based on known device types.
            augmented_inventory.append(
                self.json_builder.augment_device_details(device_entry)
            )

        self._current_inventory = augmented_inventory
        self.json_builder.save_inventory_to_json(augmented_inventory)

        # Regenerate CSV exports for external tool compatibility.
        self.csv_builder.build_csvs_from_json()

        # Grouping by manufacturer/model provides better UI organization.
        grouped_inventory = self.json_builder.load_grouped_inventory_from_json()

        self.cb_inventory(augmented_inventory)
        self.mqtt_bridge.publish_inventory(grouped_inventory)

    def _notify_response(self, serial, response, command, corr_id):
        """
        Handles a query response from a device proxy.

        Parameters:
        - serial: Originating device serial number.
        - response: The string response from the instrument.
        - command: The original query command.
        - corr_id: The correlation ID associated with the request.

        Returns:
        - None.
        """
        self.json_builder.save_query_response_to_json(
            serial, response, command, corr_id
        )
        self.cb_response(serial, response, command, corr_id)

    def _notify_error(self, serial, message, command):
        """
        Relays an error notification from a device proxy.
        """
        self.cb_error(serial, message, command)

    def _notify_status(self, serial, status):
        """
        Relays a status change (e.g., Online, Offline) from a device proxy.
        """
        self.cb_status(serial, status)

    @property
    def current_inventory(self):
        """
        Retrieves the most recent fleet inventory list.

        Returns:
        - A list of device dictionaries.
        """
        return self._current_inventory
