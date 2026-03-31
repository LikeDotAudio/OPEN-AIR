# Methods/state_comparator.py
# Author: Anthony Peter Kuzub
# Version: 20250821.200641.1
#
# Description: State_Cache/state_comparator.py

import inspect
from typing import Dict, Any, Optional

from oaLogging.Core.logger import initialize_logging, set_log_directory
from loguru import logger



current_version = "20251230.230100.1"
current_version_hash = 20251230 * 230100 * 1


# Compares an incoming MQTT payload with a cached state to determine if an update is needed.
# This function prioritizes comparison by timestamp (`ts`) if available, updating only
# the value (`val`) of the payload.
# Inputs:
#     incoming_topic (str): The MQTT topic of the incoming message.
#     incoming_payload (Dict): The dictionary payload of the incoming message.
#     cached_state (Dict): The current cached state, a dictionary mapping topics to payloads.
# Outputs:
#     bool: True if the cache should be updated with the incoming payload, False otherwise.
def should_update(
    incoming_topic: str, incoming_payload: Any, cached_state: Dict
) -> bool:
    """
    Compare timestamps (ts). If incoming > cached, return True.
    If ts is missing (or in cache missing), compare the entire payload for parity.
    """
    # Normalize incoming_payload to a dict if it's a primitive
    if not isinstance(incoming_payload, dict):
        incoming_payload = {"val": incoming_payload}

    cached_payload = cached_state.get(incoming_topic)
    if not cached_payload:
        return True  # Not in cache, so it's new

    # Normalize cached_payload to a dict if it's a primitive
    if not isinstance(cached_payload, dict):
        cached_payload = {"val": cached_payload}

    incoming_ts = incoming_payload.get("ts")
    cached_ts = cached_payload.get("ts")

    # 1. Primary: Timestamp comparison (for historical replay safety)
    if incoming_ts and cached_ts:
        if incoming_ts > cached_ts:
            return True
        elif incoming_ts <= cached_ts:
            return False

    # 2. Fallback: Full content comparison (for trimmed value-only states)
    if incoming_payload != cached_payload:
        return True

    return False
