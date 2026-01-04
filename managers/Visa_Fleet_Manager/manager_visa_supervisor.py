# managers/Visa_Fleet_Manager/manager_visa_supervisor.py
#
# Manages a fleet of VISA instruments, scanning, fingerprinting, and spawning proxies/drivers.
# Now orchestrates discovery through specialized modules: manager_visa_USB, manager_visa_IP, manager_visa_Gateway, manager_visa_Search.
#
# Author: Gemini Agent
#

import pyvisa
import time
import threading
import inspect
import re
import queue # Assuming queue is used by proxy, otherwise remove if not needed.

# Import graceful logger fallback
try:
    from workers.logger.logger import debug_logger
    from workers.logger.log_utils import _get_log_args
except ModuleNotFoundError:
    print("Warning: 'workers.logger' not found. Using dummy logger for VisaFleetSupervisor.")
    def debug_logger(message, *args, **kwargs):
        if kwargs.get('level', 'INFO') != 'DEBUG':
            print(f"[{kwargs.get('level', 'INFO')}] {message}")
    def _get_log_args(*args, **kwargs):
        return {} # Return empty dict, as logger args are not available

# Import necessary components from other modules within the fleet manager
from managers.Visa_Fleet_Manager.visa_proxy_fleet import VisaProxyFleet
from managers.Visa_Fleet_Manager.manager_visa_parse_idn import parse_idn_string # Moved to dedicated parsing module
# Import the new specialized discovery and probing modules
from managers.Visa_Fleet_Manager import manager_visa_USB
from managers.Visa_Fleet_Manager import manager_visa_IP
from managers.Visa_Fleet_Manager import manager_visa_Gateway
from managers.Visa_Fleet_Manager import manager_visa_Search


class VisaFleetSupervisor:
    """
    Supervises a fleet of VISA instruments. Handles discovery, fingerprinting,
    proxy instantiation, and inventory management.
    """
    def __init__(self, manager_ref):
        self.manager = manager_ref
        
        self.device_proxies = {}
        # self.device_drivers = {} # Commented out as per user request (no drivers)
        self.instrument_inventory = {}
        
      #  self.driver_factory = InstrumentDriverFactory() # Commented out as per user request (no drivers)
        self.resource_manager = pyvisa.ResourceManager('@py')

        self.scan_lock = threading.Lock()

    def scan_and_manage_fleet(self):
        """
        Performs a full scan of VISA resources, fingerprints them, and manages proxies.
        This scan is now controlled by settings in config.ini.
        """
        if not self.scan_lock.acquire(blocking=False):
            debug_logger("💳 ℹ️ FleetSupervisor: Scan already in progress. Skipping new scan.", **_get_log_args())
            return
        
        try:
            from workers.setup.config_reader import Config
            app_constants = Config.get_instance()

            debug_logger("💳 🔍 FleetSupervisor: Starting comprehensive fleet scan...", **_get_log_args())
            
            potential_targets = []
            
            # 1. Discover USB/Local devices (conditional)
            if app_constants.SCAN_USB:
                debug_logger("💳 🔍 Discovering USB/Local devices...", **_get_log_args())
                usb_resources = manager_visa_USB.discover_usb_devices(self.resource_manager)
                debug_logger(f"💳 🔍 USB/Local resources found: {usb_resources}", **_get_log_args())
                for res_str in usb_resources:
                    potential_targets.append({"Type": "LOCAL", "Resource": res_str})
            else:
                debug_logger("💳 ⏩ Skipping USB device scan as per config.", **_get_log_args())
            
            # 2. Discover IP devices (Dedicated and Gateways)
            # We discover both, then conditionally add them to the target list.
            debug_logger("💳 🔍 Discovering potential IP devices...", **_get_log_args())
            dedicated_ips, gateway_ips = manager_visa_IP.discover_ip_devices()

            # Conditionally add DEDICATED (Direct IP) devices
            if app_constants.SCAN_IP_DIRECT:
                debug_logger(f"💳 🔍 Processing {len(dedicated_ips)} potential Dedicated IPs...", **_get_log_args())
                for ip in dedicated_ips:
                    potential_targets.append({"Type": "DEDICATED", "Resource": f"TCPIP::{ip}::INSTR"})
            else:
                debug_logger("💳 ⏩ Skipping Direct IP device scan as per config.", **_get_log_args())

            # 3. Discover Gateway devices (conditional)
            if app_constants.SCAN_GATEWAYS:
                debug_logger(f"💳 🔍 Processing {len(gateway_ips)} potential Gateway IPs...", **_get_log_args())
                gateway_resources = manager_visa_Gateway.discover_gateway_devices(gateway_ips)
                debug_logger(f"💳 🔍 Gateway resources found: {gateway_resources}", **_get_log_args())
                for res_str in gateway_resources:
                    potential_targets.append({"Type": "GATEWAY", "Resource": res_str})
            else:
                debug_logger("💳 ⏩ Skipping Gateway device scan as per config.", **_get_log_args())


            debug_logger(f"💳 🔍 Final list of potential targets ({len(potential_targets)}): {potential_targets}", **_get_log_args())
            debug_logger(f"   ⏳ Pausing 2s for settling after discovery phases...", **_get_log_args())
            time.sleep(2.0)

            # 4. PROBE INSTRUMENTS
            debug_logger("💳 🔍 Probing instruments...", **_get_log_args())
            
            # Use the manager_visa_Search module to probe all potential targets
            probed_devices_collection = manager_visa_Search.probe_devices(self.resource_manager, potential_targets)
            debug_logger(f"💳 🔍 Probed devices collection: {probed_devices_collection}", **_get_log_args())
            
            current_scanned_serials = set(probed_devices_collection.keys()) # All successfully probed devices

            # Update self.instrument_inventory with probed details and manage proxies
            self.instrument_inventory.clear()
            for device_identifier, device_entry in probed_devices_collection.items():
                self.instrument_inventory[device_identifier] = device_entry

                # If the device is active, ensure a proxy is running
                if device_entry.get("status") == "Active":
                    if device_identifier not in self.device_proxies:
                        debug_logger(f"💳 ✨ FleetSupervisor: New active device detected: {device_identifier}", **_get_log_args())
                        
                        # Extract details for proxy creation
                        resource_name = device_entry.get("resource_string", "N/A")
                        model = device_entry.get("model", "Unknown Model")
                        manufacturer = device_entry.get("manufacturer", "Unknown Manufacturer")
                        idn_string = device_entry.get("idn_string", "")
                        # Use the robust parse_idn_string to get full idn_details from the idn_string
                        idn_details = parse_idn_string(idn_string) # Re-enabled parsing from dedicated module 

                        proxy = VisaProxyFleet(
                            manager_ref=self.manager,
                            device_serial=device_identifier,
                            resource_name=resource_name,
                            instrument_model=model,
                            manufacturer=manufacturer,
                        )
                        self.device_proxies[device_identifier] = proxy
                        
                        connection_thread = threading.Thread(
                            target=self._connect_and_setup_device, 
                            args=(proxy, resource_name, idn_details, idn_string),
                            daemon=True
                        )
                        connection_thread.start()
                    else:
                        # Device already known and active, just ensure its resource string is up-to-date in proxy
                        existing_proxy = self.device_proxies[device_identifier]
                        if existing_proxy.resource_name != device_entry.get("resource_string"):
                            debug_logger(f"💳 🔄 FleetSupervisor: Resource string updated for {device_identifier}. Old: {existing_proxy.resource_name}, New: {device_entry.get('resource_string')}. Updating proxy.", **_get_log_args())
                            existing_proxy.resource_name = device_entry.get("resource_string") # Update resource name in proxy
                else: # Device is unresponsive or not active
                    if device_identifier in self.device_proxies:
                        debug_logger(f"💳 ℹ️ FleetSupervisor: Active device {device_identifier} is now unresponsive. Shutting down its proxy.", **_get_log_args())
                        proxy_to_remove = self.device_proxies.pop(device_identifier)
                        if device_identifier in self.device_drivers:
                            del self.device_drivers[device_identifier]
                        proxy_to_remove.shutdown()
                        del proxy_to_remove

            # Clean up proxies for devices that are no longer found at all
            managed_serials = set(self.device_proxies.keys())
            removed_serials = managed_serials - current_scanned_serials
            for serial in removed_serials:
                debug_logger(f"💳 ℹ️ FleetSupervisor: Device {serial} is no longer detected. Shutting down its proxy.", **_get_log_args())
                proxy_to_remove = self.device_proxies.pop(serial)
                driver_to_remove = self.device_drivers.pop(serial, None)
                
                if driver_to_remove: 
                    del driver_to_remove
                
                proxy_to_remove.shutdown()
                del proxy_to_remove
                
                if serial in self.instrument_inventory:
                    del self.instrument_inventory[serial] # Remove from inventory if completely gone
            
            debug_logger(f"💳 ✅ FleetSupervisor: Scan and management cycle complete. {len(self.device_proxies)} proxies active.", **_get_log_args())
            self._emit_inventory_update()
            return len(probed_devices_collection) # Return the number of probed devices

        finally:
            self.scan_lock.release()

    def _connect_and_setup_device(self, proxy_instance: VisaProxyFleet, resource_name: str, idn_details: dict, idn_string: str):
        """
        Handles the connection and driver setup for a newly detected device.
        Runs in a separate thread.
        """
        device_serial = proxy_instance.device_serial
        manufacturer = idn_details.get("manufacturer")
        model = idn_details.get("model")

        debug_logger(f"💳 🔵 FleetSupervisor: Initiating connection for {device_serial} ({resource_name})", **_get_log_args())
        
        try:
            rm = pyvisa.ResourceManager('@py')
            inst = rm.open_resource(resource_name)
            inst.timeout = manager_visa_Search.VISA_TIMEOUT # Use consistent timeout from search module
            inst.read_termination = '\n'
            inst.write_termination = '\n'
            inst.query_delay = 0.1

            proxy_instance.set_instrument_instance(inst)
            
            # The instrument_inventory is already updated by scan_and_manage_fleet, 
            # so just ensure the status is correct.
            if device_serial in self.instrument_inventory:
                self.instrument_inventory[device_serial].update({
                    "status": "CONNECTED"
                })

            # # Create and assign the appropriate driver (Commented out: no drivers/command factory as per user request)
            # driver = self.driver_factory.create_driver(
            #     visa_proxy_fleet=proxy_instance,
            #     device_serial=device_serial,
            #     instrument_model=model,
            #     manufacturer=manufacturer,
            #     instrument_idn=idn_string
            # )
            # self.device_drivers[device_serial] = driver
            # if device_serial in self.instrument_inventory:
            #     self.instrument_inventory[device_serial]["driver_type"] = type(driver).__name__
            
            # debug_logger(f"💳 ✅ FleetSupervisor: Successfully connected and set up driver for {device_serial} ({model}, {manufacturer}). Driver: {type(driver).__name__}", **_get_log_args())
            
        except pyvisa.errors.VisaIOError as vioe:
            error_msg = f"VISA IO Error connecting to {device_serial} ({resource_name}): {vioe}"
            debug_logger(f"💳 ❌ FleetSupervisor: {error_msg}", **_get_log_args(), level="ERROR")
            import traceback
            debug_logger(f"Traceback: {traceback.format_exc()}", **_get_log_args(), level="ERROR")
            self.manager._notify_error(serial=device_serial, message=error_msg, command="connect")
            proxy_instance.set_instrument_instance(None)
            if device_serial in self.instrument_inventory:
                self.instrument_inventory[device_serial]["status"] = "CONNECTION_FAILED"
        except Exception as e:
            error_msg = f"Unexpected error connecting to {device_serial} ({resource_name}): {e}"
            debug_logger(f"💳 ❌ FleetSupervisor: {error_msg}", **_get_log_args(), level="ERROR")
            self.manager._notify_error(serial=device_serial, message=error_msg, command="connect")
            proxy_instance.set_instrument_instance(None)
            if device_serial in self.instrument_inventory:
                self.instrument_inventory[device_serial]["status"] = "CONNECTION_FAILED"
        finally:
            self._emit_inventory_update()

    def _emit_inventory_update(self):
        """Compiles inventory list and sends it to the Manager."""
        inventory_list = list(self.instrument_inventory.values())
        
        self.manager._notify_inventory(inventory_list)
        debug_logger(f"💳 📡⬆️ FleetSupervisor: Emitted fleet inventory ({len(inventory_list)} devices) to manager.", **_get_log_args())

    def get_driver_for_device(self, device_serial):
        """Returns the driver instance for a given device serial."""
        return self.device_drivers.get(device_serial)

    def get_proxy_for_device(self, device_serial):
        """Returns the proxy instance for a given device serial."""
        return self.device_proxies.get(device_serial)

    def shutdown(self):
        """Shuts down all managed proxies and cleans up resources."""
        debug_logger("💳 ℹ️ FleetSupervisor: Shutting down fleet supervisor.", **_get_log_args())
        for serial, proxy in list(self.device_proxies.items()):
            proxy.shutdown()
            del self.device_proxies[serial]
            # if serial in self.device_drivers: # Commented out as per user request (no drivers)
            #     del self.device_drivers[serial]
        debug_logger("💳 ℹ️ FleetSupervisor: All managed proxies shut down.", **_get_log_args())