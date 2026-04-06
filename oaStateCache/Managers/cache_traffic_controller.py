# Managers/cache_traffic_controller.py
# Author: Anthony Peter Kuzub
# Version: 20250821.200641.1
#
# Description: State_Cache/cache_traffic_controller.py

import orjson
import inspect
from typing import Dict, Any, Tuple, Optional
from oaComMQTT.Core.mqtt_message import MqttMessage

# --- Standard Debug Logging Setup ---
from oaLogging.Core.logger import initialize_logging, set_log_directory
from loguru import logger

from oaConfigurationManager.FileReaders.config_reader import Config

app_constants = Config.get_instance()

from ..Methods import state_comparator

current_version = "20251230.230300.1"
current_version_hash = 20251230 * 230300 * 1


# Processes incoming MQTT messages, decodes their payloads, and determines if an update to the cache is required.
# This function acts as a gatekeeper, checking for redundancy by comparing the new payload
# Inputs:
#     msg (MqttMessage): The MQTT message object.
#     current_cache (Dict): The current state of the application cache.
# Outputs:
#     Tuple[bool, Optional[Dict]]: A tuple indicating whether an update is needed (True/False)
#                                  and the new payload (if an update is needed, None otherwise).
def process_traffic(
    msg: MqttMessage, current_cache: Any
) -> Tuple[bool, Optional[Dict]]:
    """
    Decodes payload and determines if update is needed.
    Purity check is performed on the 'value' only, but METADATA is preserved.
    """
    topic = msg.topic
    
    try:
        # 1. Decode original payload
        raw_payload = msg.get_json_payload()
        if not isinstance(raw_payload, dict):
            full_payload = {"val": raw_payload}
        else:
            full_payload = raw_payload

        # 2. Extraction for Comparison (Purity Check)
        if "val" in full_payload:
            compare_val = {"val": full_payload["val"]}
            # Carry timestamp if present for high-speed Rust comparison
            if "ts" in full_payload: compare_val["ts"] = full_payload["ts"]
        elif "pos" in full_payload:
            compare_val = {"val": full_payload["pos"]}
            if "ts" in full_payload: compare_val["ts"] = full_payload["ts"]
        else:
            # Complex state: strip noise for comparison only
            keys_to_exclude = {"GUID", "type", "AES70", "source", "src"} # Keep 'ts' for comparison
            compare_val = {k: v for k, v in full_payload.items() if k not in keys_to_exclude}

        # 3. Decision: Only update if the VALUE changed
        if state_comparator.should_update(topic, compare_val, current_cache):
            # ⚡ RETURN FULL PAYLOAD: We need GUID/TS for the Investigation Engine
            return True, full_payload
        
        return False, None

    except Exception:
        return False, None
