# workers/discovery_agents/discovery_orchestrator.py
#
# Unified discovery orchestrator that dispatches agents and collects findings.
# Decoupled: All hardware operations now run in a dedicated background thread.
# Refactored for Modular SRP: Separates Scanning from Inventory Management.
#
# Author: Gemini Agent
#

import pyvisa
import time
import threading
import inspect
import re
import queue
import os
import orjson

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True    # Set to False in production, True for dev on this file
from oaLogging.logger import initialize_logging, set_log_directory
from loguru import logger

from oaConfiguration.config_reader import Config

app_constants = Config.get_instance()

# Import necessary components
from oaComVisa.Visa_Fleet.visa_proxy_fleet import VisaProxyFleet
from oaComVisa.Visa_Fleet.visa_parse_idn import parse_idn_string
from oaComVisa.Visa_Fleet import visa_Search as manager_visa_Search
from oaComVisa import agent_usb_enumerator, agent_mdns_zeroconf, agent_static_ip_prober

class DiscoveryOrchestrator:
    """
    Orchestrates protocol-agnostic fleet discovery.
    ⚡ THREADED: Discovery operations are isolated to prevent main thread stalls.
    """

    def __init__(self, manager_ref, aes70_manager=None):
        self.manager = manager_ref
        self.aes70_manager = aes70_manager
        self.device_proxies = {}
        self.device_drivers = {}
        self.instrument_inventory = {}
        
        # ⚡ OPTIMIZATION: Track connection failures to implement cooling-off
        self.failure_counts = {} 
        self.last_failure_time = {} 
        self.COOL_OFF_DURATION = 300 # 5 minutes

        # Discovery Worker Thread State
        self.scan_queue = queue.Queue()
        self._scan_in_progress = False
        self._last_scan_time = 0
        self._SCAN_DEBOUNCE = 10.0
        
        self.resource_manager = pyvisa.ResourceManager("@py")
        
        # Start the dedicated Discovery Worker
        self._worker_thread = threading.Thread(target=self._discovery_worker_loop, daemon=True, name="Discovery_Worker")
        self._worker_thread.start()

    def _should_skip_connection(self, serial):
        """Returns True if the device is in a cooling-off period."""
        if serial in self.last_failure_time:
            if (time.time() - self.last_failure_time[serial]) < self.COOL_OFF_DURATION:
                return True
        return False

    def scan_and_manage_fleet(self):
        """
        ⚡ NON-BLOCKING: Requests a scan and management pass. 
        Entry point for the management lifecycle.
        """
        now = time.time()
        if self._scan_in_progress or (now - self._last_scan_time) < self._SCAN_DEBOUNCE:
            return 0 # Already busy or debounced

        # Push a scan request to the worker thread
        self.scan_queue.put("SCAN_REQUEST")
        return 1

    def _discovery_worker_loop(self):
        """⚡ THE WORKHORSE: Dedicated thread for all discovery blocking calls."""
        while True:
            try:
                # Wait for a scan request
                request = self.scan_queue.get()
                if request == "SHUTDOWN": break
                
                self._scan_in_progress = True
                self._last_scan_time = time.time()
                
                # SRP REFACTOR: Step 1 - Pure I/O Scanning
                found_devices = self.scan_network()
                
                # SRP REFACTOR: Step 2 - State Management
                self.update_fleet_inventory(found_devices)
                
            except Exception as e:
                logger.exception(
                    f"💳🔍❌ [ERROR] Discovery Orchestrator: Worker Thread "
                    f"Error: {e}"
                )
            finally:
                self._scan_in_progress = False
                self.scan_queue.task_done()

    def scan_network(self):
        """
        ⚡ PURE I/O: Performs the network/USB scan protocol.
        Returns:
            dict: Collection of probed devices from all agents.
        """
        if LOCAL_DEBUG:
            logger.debug("💳🔍🧬 [DISCOVERY] Initiating network scan protocol...")

        potential_targets = []

        # 1. USB Enumeration
        if app_constants.SCAN_USB:
            usb_resources = agent_usb_enumerator.discover_usb_devices(self.resource_manager)
            for res_str in usb_resources: potential_targets.append({"Type": "LOCAL", "Resource": res_str})

        # 2. mDNS / ZeroConf Discovery (Network Scan)
        dedicated_ips, gateway_ips = agent_mdns_zeroconf.discover_ip_devices()
        
        # 2a. Integrate AES70 findings
        if self.aes70_manager and app_constants.SCAN_AES70:
            aes70_results = agent_mdns_zeroconf.discover_aes70_devices(timeout=1.5)
            for name, data in aes70_results.items():
                self.aes70_manager.register_device(name, data["ip"], data["port"], data["properties"])

        if app_constants.SCAN_IP_DIRECT:
            for ip in dedicated_ips: potential_targets.append({"Type": "DEDICATED", "Resource": f"TCPIP::{ip}::INSTR"})

        # 3. Static IP / Gateway Probing
        if app_constants.SCAN_GATEWAYS:
            gateway_resources = agent_static_ip_prober.discover_gateway_devices(gateway_ips)
            for res_str in gateway_resources: potential_targets.append({"Type": "GATEWAY", "Resource": res_str})

        # 4. PROBE (The Heavy Lifter)
        return manager_visa_Search.probe_devices(self.resource_manager, potential_targets)

    def update_fleet_inventory(self, found_devices):
        """
        ⚡ STATE MANAGEMENT: Processes discovered devices and updates system state.
        """
        if LOCAL_DEBUG:
            logger.debug(f"💳🚢🔄 [INVENTORY] Processing {len(found_devices)} discovered devices.")

        self.instrument_inventory.clear()
        current_scanned_serials = set(found_devices.keys())

        for device_identifier, device_entry in found_devices.items():
            self.instrument_inventory[device_identifier] = device_entry

            if device_entry.get("status") == "Active":
                if device_identifier not in self.device_proxies:
                    if self._should_skip_connection(device_identifier): continue
                    self._setup_new_active_device(device_identifier, device_entry)
                else:
                    # Update resource name if changed
                    existing_proxy = self.device_proxies[device_identifier]
                    if existing_proxy.resource_name != device_entry.get("resource_string"):
                        existing_proxy.resource_name = device_entry.get("resource_string")
            else:
                # Cleanup unresponsive
                if device_identifier in self.device_proxies:
                    proxy_to_remove = self.device_proxies.pop(device_identifier)
                    proxy_to_remove.shutdown()

        # Clean up removed devices
        managed_serials = set(self.device_proxies.keys())
        for serial in (managed_serials - current_scanned_serials):
            proxy_to_remove = self.device_proxies.pop(serial)
            proxy_to_remove.shutdown()
            if serial in self.instrument_inventory: del self.instrument_inventory[serial]

        # Save to fleet_inventory.json
        self._save_fleet_inventory()

        # Thread-safe callback to emit update
        if hasattr(self.manager, "after"):
            self.manager.after(0, self._emit_inventory_update)
        else:
            self._emit_inventory_update()

    def _save_fleet_inventory(self):
        """Serializes the current inventory to fleet_inventory.json."""
        try:
            from oaOchestration.project_paths import DATA_RUNNING_DIR
            inventory_path = DATA_RUNNING_DIR / "fleet_inventory.json"
            os.makedirs(os.path.dirname(inventory_path), exist_ok=True)
            with open(inventory_path, "wb") as f:
                f.write(orjson.dumps(self.instrument_inventory, option=orjson.OPT_INDENT_2))
        except Exception as e:
            logger.error(f"❌ Failed to save fleet inventory: {e}")

    def _setup_new_active_device(self, device_identifier, device_entry):
        resource_name = device_entry.get("resource_string", "N/A")
        model = device_entry.get("model", "Unknown Model")
        manufacturer = device_entry.get("manufacturer", "Unknown Manufacturer")

        proxy = VisaProxyFleet(
            manager_ref=self.manager,
            device_serial=device_identifier,
            resource_name=resource_name,
            instrument_model=model,
            manufacturer=manufacturer,
        )
        self.device_proxies[device_identifier] = proxy
        
        # Connect immediately in this background thread
        try:
            inst = self.resource_manager.open_resource(resource_name)
            inst.timeout = manager_visa_Search.VISA_TIMEOUT
            inst.read_termination = "\n"
            inst.write_termination = "\n"
            proxy.set_instrument_instance(inst)
            if device_identifier in self.instrument_inventory:
                self.instrument_inventory[device_identifier].update({"status": "CONNECTED"})
        except Exception as e:
            self.last_failure_time[device_identifier] = time.time()
            if device_identifier in self.instrument_inventory:
                self.instrument_inventory[device_identifier]["status"] = "CONNECTION_FAILED"

    def _emit_inventory_update(self):
        """Sends updates to the Manager. Called via after() from worker thread."""
        inventory_list = list(self.instrument_inventory.values())
        self.manager._notify_inventory(inventory_list)

    def get_proxy_for_device(self, serial):
        """Returns the proxy instance for a given serial, or None if not found."""
        return self.device_proxies.get(serial)

    def shutdown(self):
        """Shuts down all managed proxies and stops the worker thread."""
        self.scan_queue.put("SHUTDOWN")
        for serial, proxy in list(self.device_proxies.items()):
            proxy.shutdown()
            del self.device_proxies[serial]
