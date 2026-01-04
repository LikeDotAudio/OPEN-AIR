# managers/Visa_Fleet_Manager/manager_visa_json_builder.py
#
# Manages the construction and augmentation of JSON data for VISA devices.
#
# Author: Gemini Agent

import json
import os
import datetime
import inspect
import tempfile

try:
    from workers.logger.logger import debug_logger
    from workers.logger.log_utils import _get_log_args
except ModuleNotFoundError:
    print("Warning: 'workers.logger' not found. Using dummy logger for VisaJsonBuilder.")
    def debug_logger(message, *args, **kwargs):
        if kwargs.get('level', 'INFO') != 'DEBUG':
            print(f"[{kwargs.get('level', 'INFO')}] {message}")
    def _get_log_args(*args, **kwargs):
        return {} # Return empty dict, as logger args are not available

# --- Constants ---
# The project root is assumed to be two levels up from this script (OPEN-AIR/managers/Visa_Fleet_Manager)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
VISA_FLEET_JSON_PATH = os.path.join(PROJECT_ROOT, "DATA", "VISA_FLEET.json")
QUERY_DATA_DIR = os.path.join(PROJECT_ROOT, "DATA")

# Import the centralized knowledge base for known device types
from managers.Visa_Fleet_Manager.manager_visa_known_types import KNOWN_DEVICES

class VisaJsonBuilder:
    def __init__(self):
        current_function_name = inspect.currentframe().f_code.co_name
        debug_logger(message=f"🛠️ VisaJsonBuilder initialized with {len(KNOWN_DEVICES)} known devices.", **_get_log_args())
        self.known_devices = KNOWN_DEVICES

    def augment_device_details(self, device_entry):
        """
        Looks up the Model Number in KNOWN_DEVICES and adds Type/Notes to the entry.
        """
        model = device_entry.get("model", "Unknown")
        
        # Default values
        device_entry["device_type"] = "Unknown Instrument"
        device_entry["notes"] = "Not in Knowledge Base"
        device_entry["allocated"] = False # New parameter, defaulted to False
        device_entry["connection_timestamp"] = datetime.datetime.now().isoformat() # Add connection timestamp
        
        if model in self.known_devices:
            info = self.known_devices[model]
            device_entry["device_type"] = info["type"]
            device_entry["notes"] = info["notes"]
            
        return device_entry

    def save_inventory_to_json(self, inventory_data):
        """
        Saves the current fleet inventory to a JSON file in an atomic way to prevent corruption.
        It writes to a temporary file first and then renames it.
        """
        filepath = VISA_FLEET_JSON_PATH
        temp_path = None
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # Group the inventory data before saving
            grouped_data = self._group_devices_by_type_and_model(inventory_data)

            # Write to a temporary file in the same directory
            with tempfile.NamedTemporaryFile(mode='w', delete=False, dir=os.path.dirname(filepath), suffix='.tmp') as tmp_f:
                temp_path = tmp_f.name
                json.dump(grouped_data, tmp_f, indent=4)
            
            # Atomically rename the temp file to the final destination
            os.rename(temp_path, filepath)
            
            debug_logger(f"✅ Atomically saved fleet inventory to {filepath}", **_get_log_args())
        except Exception as e:
            debug_logger(f"❌ Error saving inventory to JSON: {e}", **_get_log_args(), level="ERROR")
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path) # Clean up temp file on error

    def load_inventory_from_json(self):
        """Loads fleet inventory from a JSON file if it exists, is not empty, and flattens it."""
        filepath = VISA_FLEET_JSON_PATH
        if os.path.exists(filepath):
            if os.path.getsize(filepath) == 0: # Check if file is empty
                debug_logger(f"ℹ️ Inventory file {filepath} is empty. Initializing empty inventory.", **_get_log_args())
                return [] # Treat empty file as empty inventory
            try:
                with open(filepath, 'r') as f:
                    grouped_inventory = json.load(f)
                flat_inventory = self._flatten_grouped_inventory(grouped_inventory)
                debug_logger(f"✅ Loaded and flattened fleet inventory from {filepath} with {len(flat_inventory)} devices.", **_get_log_args())
                return flat_inventory
            except json.JSONDecodeError as e:
                debug_logger(f"❌ Error decoding inventory JSON from {filepath}: {e}. Initializing empty inventory.", **_get_log_args(), level="ERROR")
                return [] # Return empty list, as it's flattened
            except Exception as e:
                debug_logger(f"❌ Error loading inventory from JSON: {e}. Initializing empty inventory.", **_get_log_args(), level="ERROR")
                return [] # Return empty list
        else:
            debug_logger(f"ℹ️ No existing inventory file found at {filepath}. Initializing empty inventory and creating file.", **_get_log_args())
            self.save_inventory_to_json([]) # Create the file with an empty inventory
            return [] # Return empty list

    def load_grouped_inventory_from_json(self):
        """
        Loads fleet inventory from a JSON file if it exists and returns the raw,
        hierarchical (grouped) dictionary without flattening.
        """
        filepath = VISA_FLEET_JSON_PATH
        if os.path.exists(filepath):
            if os.path.getsize(filepath) == 0:  # Check if file is empty
                debug_logger(f"ℹ️ Grouped inventory file {filepath} is empty. Returning empty dictionary.", **_get_log_args())
                return {}
            try:
                with open(filepath, 'r') as f:
                    grouped_inventory = json.load(f)
                debug_logger(f"✅ Loaded raw grouped fleet inventory from {filepath}.", **_get_log_args())
                return grouped_inventory
            except json.JSONDecodeError as e:
                debug_logger(f"❌ Error decoding grouped inventory JSON from {filepath}: {e}", **_get_log_args(), level="ERROR")
                return {} # Return empty dict, as it's grouped
            except Exception as e:
                debug_logger(f"❌ Error loading grouped inventory from JSON: {e}", **_get_log_args(), level="ERROR")
                return {} # Return empty dict
        else:
            debug_logger(f"ℹ️ No existing grouped inventory file found at {filepath}. Initializing empty grouped inventory and creating file.", **_get_log_args())
            self.save_inventory_to_json([]) # Create the file with an empty inventory
            return {} # Return empty dict

    def save_query_response_to_json(self, serial, response, command, corr_id):
        """
        Saves a query response to a JSON file in the DATA directory.
        Filename format: DATA/{serial}_query_{timestamp}.json
        """
        os.makedirs(QUERY_DATA_DIR, exist_ok=True)

        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"{serial}_query_{timestamp}.json"
        filepath = os.path.join(QUERY_DATA_DIR, filename)

        query_data = {
            "serial_number": serial,
            "command": command,
            "response": response,
            "correlation_id": corr_id,
            "timestamp": datetime.datetime.now().isoformat()
        }

        try:
            with open(filepath, 'w') as f:
                json.dump(query_data, f, indent=4)
            debug_logger(f"✅ Saved query response for {serial} to {filepath}", **_get_log_args())
        except Exception as e:
            debug_logger(f"❌ Error saving query response to JSON: {e}", **_get_log_args(), level="ERROR")

    def _group_devices_by_type_and_model(self, inventory_data):
        """
        Groups a flat list of device dictionaries first by 'device_type',
        then a constant 'YAK' topic, then 'model' (forced uppercase), then a constant 'Connection' topic,
        and finally by 'gpib_address'.
        The innermost level will contain the device's full details.
        """
        grouped_data = {}
        
        # Ensure inventory_data is actually a list for consistent processing
        if not isinstance(inventory_data, list):
            # If it's a dict, try to flatten it (e.g., from old grouped structure)
            if isinstance(inventory_data, dict):
                flat_devices = []
                for type_group in inventory_data.values():
                    if isinstance(type_group, dict):
                        for model_group in type_group.values():
                            if isinstance(model_group, list): # Old list structure
                                flat_devices.extend(model_group)
                            elif isinstance(model_group, dict): # New dict structure, need to extract devices
                                for port_group in model_group.values():
                                    if isinstance(port_group, dict):
                                        for device_blob in port_group.values():
                                            if isinstance(device_blob, dict):
                                                flat_devices.append(device_blob)
                inventory_data = flat_devices
            else:
                inventory_data = [] # Fallback to empty list
        
        for device in inventory_data:
            device_type = device.get("device_type", "Unknown Type")
            model = device.get("model", "Unknown Model") # Model casing is determined by source
            interface_port = device.get("interface_port", "Unknown Port")
            gpib_address = device.get("gpib_address", "Unknown GPIB")

            if device_type not in grouped_data:
                grouped_data[device_type] = {}
            # Insert the constant "YAK" topic here
            if "YAK" not in grouped_data[device_type]:
                grouped_data[device_type]["YAK"] = {}
            if model not in grouped_data[device_type]["YAK"]:
                grouped_data[device_type]["YAK"][model] = {}
            # Insert the constant "Connection" topic here
            if "Connection" not in grouped_data[device_type]["YAK"][model]:
                grouped_data[device_type]["YAK"][model]["Connection"] = {}
            if "Table" not in grouped_data[device_type]["YAK"][model]["Connection"]:
                grouped_data[device_type]["YAK"][model]["Connection"]["Table"] = {
                    "type": "OcaTable",
                    "description": "Discovered Devices",
                    "headers": ["type", "resource_string", "ip_address", "interface_port", "gpib_address", "status", "manufacturer", "model", "serial_number", "firmware", "idn_string", "device_type", "notes", "allocated", "connection_timestamp"],
                    "data": {}
                }
            
            # The innermost level now directly contains the device details (BLOB)
            # We use gpib_address as the final key to avoid lists.
            # Assuming gpib_address is unique within an interface_port for a given model/type.
            grouped_data[device_type]["YAK"][model]["Connection"]["Table"]["data"][gpib_address] = device
        return grouped_data

    def _flatten_grouped_inventory(self, grouped_data):
        """
        Flattens the hierarchical grouped inventory data back into a list of individual device dictionaries.
        Expected structure: device_type -> "YAK" -> model -> "Connection" -> "Table" -> gpib_address -> device_dict
        """
        flat_devices = []
        for device_type_group in grouped_data.values():
            if isinstance(device_type_group, dict):
                # Iterate through the "YAK" level
                if "YAK" in device_type_group and isinstance(device_type_group["YAK"], dict):
                    for model_group in device_type_group["YAK"].values():
                        if isinstance(model_group, dict):
                            # Iterate through the "Connection" level
                            if "Connection" in model_group and isinstance(model_group["Connection"], dict):
                                if "Table" in model_group["Connection"] and isinstance(model_group["Connection"]["Table"], dict):
                                    table_wrapper = model_group["Connection"]["Table"]
                                    if "data" in table_wrapper and isinstance(table_wrapper["data"], dict):
                                        for device_blob in table_wrapper["data"].values():
                                            if isinstance(device_blob, dict):
                                                flat_devices.append(device_blob)
        return flat_devices