# managers/STATE_VISA_FLEET_Manager/manager_visa_json_builder.py
#
# Manages the construction and augmentation of JSON data for VISA devices.
#
# Author: Gemini Agent

import orjson
import os
import datetime
import inspect
import tempfile

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True    # Set to False in production, True for dev on this file
from workers.logger.logger import initialize_logging, set_log_directory
from loguru import logger

from managers.configini.config_reader import Config

app_constants = Config.get_instance()


import workers.initialization.project_paths as app_paths

# --- Constants ---
STATE_VISA_FLEET_JSON_PATH = str(app_paths.STATE_VISA_FLEET_JSON_PATH)
QUERY_DATA_DIR = str(app_paths.QUERY_DATA_DIR)

# Import the centralized knowledge base for known device types
from managers.Visa_Fleet.visa_known_types import KNOWN_DEVICES


class VisaJsonBuilder:
    def __init__(self):
        if LOCAL_DEBUG: logger.debug(f"🛠️ VisaJsonBuilder initialized with {len(KNOWN_DEVICES)} known devices.")
        self.known_devices = KNOWN_DEVICES

    def augment_device_details(self, device_entry):
        """
        Looks up the Model Number in KNOWN_DEVICES and adds Type/Notes to the entry.
        """
        model = device_entry.get("model", "Unknown")

        # Default values
        device_entry["device_type"] = "Unknown Instrument"
        device_entry["notes"] = "Not in Knowledge Base"
        device_entry["allocated"] = False  # New parameter, defaulted to False
        device_entry["connection_timestamp"] = (
            datetime.datetime.now().isoformat()
        )  # Add connection timestamp

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
        filepath = STATE_VISA_FLEET_JSON_PATH
        temp_path = None
        
        # Ensure directory exists (exist_ok=True prevents exception)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        # Group the inventory data before saving
        grouped_data = self._group_devices_by_type_and_model(inventory_data)

        # Write to a temporary file in the same directory
        with tempfile.NamedTemporaryFile(
            mode="wb", delete=False, dir=os.path.dirname(filepath), suffix=".tmp"
        ) as tmp_f:
            temp_path = tmp_f.name
            tmp_f.write(orjson.dumps(grouped_data, option=orjson.OPT_INDENT_2))

        # ⚡ VALIDATION: Ensure temp file was actually created and has content
        if temp_path and os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
            # Atomically rename the temp file to the final destination
            os.rename(temp_path, filepath)
            if LOCAL_DEBUG: logger.debug(f"✅ Atomically saved fleet inventory to {filepath}")
        else:
            logger.error(f"❌ Failed to save inventory: Temp file {temp_path} is invalid.")
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)

    def load_inventory_from_json(self):
        """Loads fleet inventory from a JSON file if it exists, is not empty, and flattens it."""
        filepath = STATE_VISA_FLEET_JSON_PATH
        if not os.path.exists(filepath):
            if LOCAL_DEBUG: logger.debug(f"ℹ️ No existing inventory file found at {filepath}. Initializing empty inventory and creating file.")
            self.save_inventory_to_json([])  # Create the file with an empty inventory
            return []

        if os.path.getsize(filepath) == 0:  # Check if file is empty
            if LOCAL_DEBUG: logger.debug(f"ℹ️ Inventory file {filepath} is empty. Initializing empty inventory.")
            return []  # Treat empty file as empty inventory

        with open(filepath, "rb") as f:
            raw_data = f.read()

        # ⚡ PRE-VALIDATION: Structural integrity check
        stripped_data = raw_data.strip()
        if not stripped_data.startswith((b"{", b"[")) or not stripped_data.endswith((b"}", b"]")):
            logger.error(f"❌ Error: JSON structural validation failed for {filepath}. Corrupted file?")
            return []

        grouped_inventory = orjson.loads(raw_data)
        flat_inventory = self._flatten_grouped_inventory(grouped_inventory)
        if LOCAL_DEBUG: logger.debug(f"✅ Loaded and flattened fleet inventory from {filepath} with {len(flat_inventory)} devices.")
        return flat_inventory

    def load_grouped_inventory_from_json(self):
        """
        Loads fleet inventory from a JSON file if it exists and returns the raw,
        hierarchical (grouped) dictionary without flattening.
        """
        filepath = STATE_VISA_FLEET_JSON_PATH
        if not os.path.exists(filepath):
            if LOCAL_DEBUG: logger.debug(f"ℹ️ No existing grouped inventory file found at {filepath}. Initializing empty grouped inventory and creating file.")
            self.save_inventory_to_json([])  # Create the file with an empty inventory
            return {}

        if os.path.getsize(filepath) == 0:  # Check if file is empty
            if LOCAL_DEBUG: logger.debug(f"ℹ️ Grouped inventory file {filepath} is empty. Returning empty dictionary.")
            return {}

        with open(filepath, "rb") as f:
            raw_data = f.read()

        # ⚡ PRE-VALIDATION: Structural integrity check
        stripped_data = raw_data.strip()
        if not stripped_data.startswith(b"{") or not stripped_data.endswith(b"}"):
            logger.error(f"❌ Error: JSON structural validation failed for {filepath}. Corrupted grouped file?")
            return {}

        grouped_inventory = orjson.loads(raw_data)
        if LOCAL_DEBUG: logger.debug(f"✅ Loaded raw grouped fleet inventory from {filepath}.")
        return grouped_inventory

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
            "timestamp": datetime.datetime.now().isoformat(),
        }

        with open(filepath, "wb") as f:
            f.write(orjson.dumps(query_data, option=orjson.OPT_INDENT_2))
        
        if LOCAL_DEBUG: 
            # Final validation: check if file was written
            if os.path.exists(filepath):
                logger.debug(f"✅ Saved query response for {serial} to {filepath}")
            else:
                logger.error(f"❌ Failed to save query response for {serial} to {filepath}")


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
                            if isinstance(model_group, list):  # Old list structure
                                flat_devices.extend(model_group)
                            elif isinstance(
                                model_group, dict
                            ):  # New dict structure, need to extract devices
                                for port_group in model_group.values():
                                    if isinstance(port_group, dict):
                                        for device_blob in port_group.values():
                                            if isinstance(device_blob, dict):
                                                flat_devices.append(device_blob)
                inventory_data = flat_devices
            else:
                inventory_data = []  # Fallback to empty list

        for device in inventory_data:
            device_type = device.get("device_type", "Unknown Type")
            model = device.get(
                "model", "Unknown Model"
            )  # Model casing is determined by source
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
                    "data": {},
                }

            # The innermost level now directly contains the device details (BLOB)
            # We use gpib_address as the final key to avoid lists.
            # Assuming gpib_address is unique within an interface_port for a given model/type.
            grouped_data[device_type]["YAK"][model]["Connection"]["Table"]["data"][
                gpib_address
            ] = device
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
                if "YAK" in device_type_group and isinstance(
                    device_type_group["YAK"], dict
                ):
                    for model_group in device_type_group["YAK"].values():
                        if isinstance(model_group, dict):
                            # Iterate through the "Connection" level
                            if "Connection" in model_group and isinstance(
                                model_group["Connection"], dict
                            ):
                                if "Table" in model_group["Connection"] and isinstance(
                                    model_group["Connection"]["Table"], dict
                                ):
                                    table_wrapper = model_group["Connection"]["Table"]
                                    if "data" in table_wrapper and isinstance(
                                        table_wrapper["data"], dict
                                    ):
                                        for device_blob in table_wrapper[
                                            "data"
                                        ].values():
                                            if isinstance(device_blob, dict):
                                                flat_devices.append(device_blob)
        return flat_devices
