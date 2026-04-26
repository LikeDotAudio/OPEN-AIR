import csv
import inspect

# Methods/marker_csv_to_json_mqtt.py
# Author: Anthony Peter Kuzub
# Version: 20250821.200641.1
#
# Description: importers/worker_marker_csv_to_json_mqtt.py
import os

import orjson

from oaLogging.Methods.matrix_gate import matrix_log

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = False
from loguru import logger

from oaConfigurationManager.FileReaders.config_reader import Config

app_constants = Config.get_instance()  # Get the singleton instance

from oaComProtocols.oaComMQTT.Methods.mqtt_controller_util import MqttControllerUtility
from oaOchestration.Constants.project_paths import MARKERS_CSV_PATH, MARKERS_JSON_PATH  # NEW: Import paths

# --- Global Scope Variables ---
current_version = "20251226.000000.1"
current_version_hash = (20251226 * 0 * 1)
current_file = f"{os.path.basename(__file__)}"

MQTT_BASE_TOPIC = "OPEN-AIR/repository/markers"


# Recursively publishes all key-value pairs of a nested dictionary to MQTT.
# This function traverses a dictionary structure. For each non-dictionary value,
# it constructs a full MQTT topic path by consmpte2138ting keys and publishes the value.
# Inputs:
#     mqtt_util (MqttControllerUtility): The MQTT utility for publishing messages.
#     base_topic (str): The current base topic path for the recursion.
#     data (dict or any): The data (dictionary or value) to be published.
# Outputs:
#     None.
def _publish_recursive(mqtt_util, base_topic, data):
    """
    A simple recursive function to publish all parts of a nested dictionary.
    """
    if isinstance(data, dict):
        for key, value in data.items():
            new_topic = f"{base_topic}/{key}"
            _publish_recursive(mqtt_util, new_topic, value)
    else:
        # When we hit a final value, publish it.
        mqtt_util.publish_message(topic=base_topic, subtopic="", value=str(data), retain=True)


# Reads marker data from MARKERS.csv, converts it to a device-centric JSON structure, saves it, and publishes to MQTT.
# This function performs several steps:
# 1. Reads the CSV file and calculates summary data (total devices, min/max frequency, span).
# 2. Converts each CSV row into a nested JSON structure for individual devices.
# 3. Saves the complete JSON structure to MARKERS.json.
# 4. Publishes the entire JSON structure to MQTT, after purging old data.
# Inputs:
#     mqtt_util (MqttControllerUtility): The MQTT utility for publishing messages.
# Outputs:
#     None.
def csv_to_json_and_publish(mqtt_util: MqttControllerUtility):
    """
    Reads MARKERS.csv, calculates summary data (total, min/max freq, span), converts
    to a flat device-centric JSON structure, saves it, and publishes to MQTT.

    MODIFIED: Uses the new nested structure with an 'IDENTITY' blob.
    """
    if LOCAL_DEBUG:
        matrix_log("ui", "importer", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "🟢️️️🟢 Initiating device-centric CSV to JSON conversion and MQTT publish. Applying new nested structure.", "DEBUG")

    if not MARKERS_CSV_PATH.is_file():
        logger.error(f"❌ {MARKERS_CSV_PATH} not found. Aborting operation.")
        return

    # --- Step 1: Read CSV and generate the flat JSON structure ---
    json_state = {}
    try:
        with open(MARKERS_CSV_PATH, newline='', encoding='utf-8') as csvfile:
            # Read all data into a list to process it multiple times
            reader = list(csv.DictReader(csvfile))

            total_devices = len(reader)
            min_freq = float('inf')
            max_freq = float('-inf')

            # First pass: calculate min/max frequencies
            for row in reader:
                try:
                    # --- FIX: Check for 'FREQ', 'FREQ (MHZ)', and 'FREQ_MHZ' ---
                    # Now relies on the canonical 'FREQ_MHZ' key from file_handling worker
                    freq_str = row.get("FREQ_MHZ")
                    if freq_str:
                        freq = float(freq_str)
                        if freq < min_freq:
                            min_freq = freq
                        if freq > max_freq:
                            max_freq = freq
                except (ValueError, TypeError):
                    # Ignore rows with non-numeric frequencies for min/max calculation
                    continue

            # Handle case where no valid frequencies were found
            if min_freq == float('inf'): min_freq = 0
            if max_freq == float('-inf'): max_freq = 0

            # Calculate the span
            span_mhz = max_freq - min_freq

            # Add summary data to the root of the JSON state
            json_state["total_devices"] = total_devices
            json_state["min_frequency_mhz"] = round(min_freq, 6)
            json_state["max_frequency_mhz"] = round(max_freq, 6)
            json_state["span_mhz"] = round(span_mhz, 6)

            # Second pass: build the device dictionaries
            for i, row in enumerate(reader, 1):
                device_key = f"Device-{i:03d}"

                # --- NEW STRUCTURE IMPLEMENTATION ---
                json_state[device_key] = {
                    "IDENTITY": {
                        "Name": row.get("NAME", ""),
                        "Device": row.get("DEVICE", ""),
                        "Zone": row.get("ZONE", ""),
                        "Group": row.get("GROUP", ""),
                        "FREQ_MHZ": row.get("FREQ_MHZ") or "null",
                    },
                    "Peak": row.get("PEAK", "nan"),
                    # Removing the "active" and "selected" fields as requested
                }
                # --- END NEW STRUCTURE IMPLEMENTATION ---

        matrix_log("ui", "importer", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "✅ Successfully read CSV and generated nested JSON structure with summary data.", "SUCCESS")
    except Exception:
        if LOCAL_DEBUG:
            logger.exception("❌ Error processing CSV file")
        return

    # --- Step 2: Save the generated structure to MARKERS.json ---
    try:
        # Ensure the DATA directory exists
        MARKERS_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(MARKERS_JSON_PATH, 'w') as f:
            f.write(orjson.dumps(json_state).decode())
        matrix_log("ui", "importer", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"✅ Saved generated structure to {MARKERS_JSON_PATH}.", "SUCCESS")
    except Exception:
        if LOCAL_DEBUG:
            logger.exception("❌ Error saving to {MARKERS_JSON_PATH}")
        return

    # --- Step 3: Publish the entire structure to MQTT ---
    try:
        # First, clear any old data under the base topic by publishing a null, retained message.
        # This will remove all the old topics (Device-001/Name, Device-001/active, etc.)
        mqtt_util.purge_branch(MQTT_BASE_TOPIC)
        matrix_log("ui", "importer", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"🗑️ Cleared old data under topic: {MQTT_BASE_TOPIC}/#", "DEBUG")

        # Now, publish the new, complete structure recursively.
        _publish_recursive(mqtt_util, MQTT_BASE_TOPIC, json_state)

        matrix_log("ui", "importer", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "✅ Successfully published the full marker set to MQTT.", "SUCCESS")
    except Exception:
        if LOCAL_DEBUG:
            logger.exception("❌ Error publishing to MQTT")
