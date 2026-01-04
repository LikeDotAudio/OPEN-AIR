# managers/Visa_Fleet_Manager/visa_fleet_manager.py
#
# The STANDALONE orchestrator. No MQTT dependencies.
#
# Author: Gemini Agent
#

import threading
import time
import inspect
import json
import os
import string
import datetime # For timestamp in query filename

try:
    from workers.logger.logger import debug_logger
    from workers.logger.log_utils import _get_log_args
except ModuleNotFoundError:
    print("Warning: 'workers.logger' not found. Using dummy logger for VisaFleetManager.")
    def debug_logger(message, *args, **kwargs):
        if kwargs.get('level', 'INFO') != 'DEBUG':
            print(f"[{kwargs.get('level', 'INFO')}] {message}")
    def _get_log_args(*args, **kwargs):
        return {} # Return empty dict, as logger args are not available
from managers.Visa_Fleet_Manager.manager_visa_supervisor import VisaFleetSupervisor
from managers.Visa_Fleet_Manager.manager_visa_json_builder import VisaJsonBuilder # Import new builder
from managers.Visa_Fleet_Manager.manager_fleet_mqtt_bridge import MqttFleetBridge # Import MQTT bridge

class VisaFleetManager:
    def __init__(self):
        current_function_name = inspect.currentframe().f_code.co_name
        debug_logger(
            message=f"💳 🟢️️️🟢 Initializing VisaFleetManager. The commander of the fleet is online!",
            **_get_log_args()
        )
        
        # Initialize the JSON builder
        self.json_builder = VisaJsonBuilder()
        # Initialize the MQTT bridge
        self.mqtt_bridge = None
        self.mqtt_bridge = MqttFleetBridge()

        # Callbacks are initially empty (No-op)
        self.cb_inventory = lambda x: None
        self.cb_response = lambda s, r, c, i: None
        self.cb_error = lambda s, m, c: None
        self.cb_status = lambda s, st: None

        self._current_inventory = [] # Internal storage for the latest inventory
        self._current_inventory = self.json_builder.load_inventory_from_json() # Load inventory on startup

        # Initialize Supervisor (Headless)
        self.fleet_supervisor = VisaFleetSupervisor(manager_ref=self)
        self._running = False
        self.initial_scan_complete_event = threading.Event()
        
        debug_logger(message=f"💳 ✅ VisaFleetManager initialized. Supervisor ready.", **_get_log_args())

    def set_callbacks(self, on_inventory_update, on_device_response, on_device_error, on_proxy_status):
        """Link external listeners (like the MQTT Bridge or a GUI) to internal events."""
        self.cb_inventory = on_inventory_update
        self.cb_response = on_device_response
        self.cb_error = on_device_error
        self.cb_status = on_proxy_status

    def start(self):
        self._running = True
        debug_logger("💳 Core: VisaFleetManager Started (Standalone Mode).", **_get_log_args())

    def stop(self):
        self._running = False
        if self.fleet_supervisor: # Ensure supervisor exists before trying to shut it down
            self.fleet_supervisor.shutdown()
        if self.mqtt_bridge:
            self.mqtt_bridge.disconnect()
        debug_logger("💳 Core: VisaFleetManager Stopped.", **_get_log_args())


    def trigger_scan(self):
        """Public API to start a scan."""
        self.initial_scan_complete_event.clear()
        debug_logger("💳 Core: Scan Triggered via API.", **_get_log_args())
        self._publish_scan_status("Start", {"status": "scanning"})
        num_devices_found = self.fleet_supervisor.scan_and_manage_fleet()
        self._publish_scan_status("Complete", {"status": "ready", "num_devices": num_devices_found})
        self.initial_scan_complete_event.set()

    def wait_for_initial_scan(self, timeout=None):
        """
        Blocks the calling thread until the initial device scan is complete.
        Returns True if the scan completed, False if it timed out.
        """
        debug_logger("⏳ Waiting for initial VISA fleet scan to complete...", **_get_log_args())
        completed = self.initial_scan_complete_event.wait(timeout=timeout)
        if completed:
            debug_logger("✅ Initial VISA fleet scan complete.", **_get_log_args())
        else:
            debug_logger("⚠️ Timed out waiting for initial VISA fleet scan.", **_get_log_args())
        return completed

    def _publish_scan_status(self, status, payload):
        """Publishes the current scan status to MQTT."""
        if self.mqtt_bridge and self.mqtt_bridge.is_connected:
            topic = f"OPEN-AIR/System/Status/Fleet/{status}"
            self.mqtt_bridge.client.publish(topic, json.dumps(payload))
            debug_logger(message=f"Published scan status '{status}' to topic '{topic}'", **_get_log_args())


    def enqueue_command(self, serial, command, query=False, correlation_id="N/A"):
        """Public API to send a command to a specific device."""
        proxy = self.fleet_supervisor.get_proxy_for_device(serial)
        if proxy:
            proxy.enqueue_command(command, query, correlation_id)
        else:
            self.cb_error(serial, "Device not found in fleet manager", command)

    # --- Internal Event Handlers (Called by Supervisor/Proxies) ---
    
    def _notify_inventory(self, inventory_data):
        """Receives updated inventory from Supervisor, augments it, and saves it."""
        augmented_inventory = []
        for device_entry in inventory_data:
            augmented_inventory.append(self.json_builder.augment_device_details(device_entry))

        self._current_inventory = augmented_inventory
        self.json_builder.save_inventory_to_json(augmented_inventory)
        
        # Load the newly saved (and grouped) inventory to ensure MQTT reflects the file structure
        grouped_inventory = self.json_builder.load_grouped_inventory_from_json()
        
        self.cb_inventory(augmented_inventory) # Still emit the flat list for other listeners if needed
        self.mqtt_bridge.publish_inventory(grouped_inventory) # Publish the grouped data

    def _notify_response(self, serial, response, command, corr_id):
        """Receives device response and saves it to a JSON file."""
        self.json_builder.save_query_response_to_json(serial, response, command, corr_id)
        self.cb_response(serial, response, command, corr_id)

    def _notify_error(self, serial, message, command):
        self.cb_error(serial, message, command)

    def _notify_status(self, serial, status):
        self.cb_status(serial, status)

    @property
    def current_inventory(self):
        """Returns the last known inventory list."""
        return self._current_inventory