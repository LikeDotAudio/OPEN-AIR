# Managers/cache_traffic_controller.py
# Author: Anthony Peter Kuzub
# Version: 20250821.200641.1
#
# Description: State_Cache/cache_traffic_controller.py

from typing import Any

from oaComProtocols.oaComMQTT.Core.mqtt_message import MqttMessage

# --- Standard Debug Logging Setup ---
from oaConfigurationManager.FileReaders.config_reader import Config

app_constants = Config.get_instance()

from ..Methods import state_comparator

current_version = "20251230.230300.1"
current_version_hash = 20251230 * 230300 * 1


# Processes incoming MQTT messages, decodes their payloads, and determines if an update to the cache is required.
# This function acts as a gatekeeper, checking for redundancy by comparing the new payload
# Inputs:
#     message (MqttMessage): The MQTT message object.
#     current_cache (Dict): The current state of the application cache.
# Outputs:
#     Tuple[bool, Optional[Dict]]: A tuple indicating whether an update is needed (True/False)
#                                  and the new payload (if an update is needed, None otherwise).
def process_traffic(
    message: MqttMessage, current_cache: Any
) -> tuple[bool, dict | None]:
    """
    Decodes payload and determines if update is needed.
    Purity check is performed on the 'value' only, but METADATA is preserved.
    """
    topic = message.topic

    # --- HEARTBEAT FILTER (V3.0.0 Refinement) ---
    # Exclude high-frequency/volatile data from the persistent state cache.
    # This prevents 'Heartbeat' or 'Status' messages from thrashing disk I/O.
    volatile_patterns = ["/Heartbeat/", "/Status/Monitor/", "/Firehose/", "/Monitor/Telemetry/"]
    if any(pattern in topic for pattern in volatile_patterns):
        return False, None

    try:
        # 1. Decode original payload
        raw_payload = message.get_json_payload()
        if not isinstance(raw_payload, dict):
            full_payload = {"value": raw_payload}
        else:
            full_payload = raw_payload

        # 2. Extraction for Comparison (Purity Check)
        if "value" in full_payload:
            compare_val = {"value": full_payload["value"]}
            # Carry timestamp if present for high-speed Rust comparison
            if "timestamp" in full_payload: compare_val["timestamp"] = full_payload["timestamp"]
        elif "pos" in full_payload:
            compare_val = {"value": full_payload["pos"]}
            if "timestamp" in full_payload: compare_val["timestamp"] = full_payload["timestamp"]
        else:
            # Complex state: strip noise for comparison only
            keys_to_exclude = {"GUID", "type", "AES70", "source", "src"} # Keep 'timestamp' for comparison
            compare_val = {k: v for k, v in full_payload.items() if k not in keys_to_exclude}

        # 3. Decision: Only update if the VALUE changed
        if state_comparator.should_update(topic, compare_val, current_cache):
            # ⚡ RETURN FULL PAYLOAD: We need GUID/TS for the Investigation Engine
            return True, full_payload

        return False, None

    except Exception:
        return False, None
