# State_Cache/state_comparator.py
#
# Compares incoming MQTT payloads with cached state to determine if an update is necessary, prioritizing timestamp and falling back to value comparison.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Professional services for customizing and tailoring this software to your specific
# application can be negotiated. There is no charge to use, modify, or fork this software.
#
# Build Log: https://like.audio/category/software/spectrum-scanner/
# Source Code: https://github.com/APKaudio/
# Feature Requests can be emailed to i @ like . audio
#
# Version 20250821.200641.1

import inspect
from typing import Dict, Any, Optional

from oaLogging.Core.logger import initialize_logging, set_log_directory
from loguru import logger

LOCAL_DEBUG = True    # Set to False in production, True for dev on this file


current_version = "20251230.230100.1"
current_version_hash = 20251230 * 230100 * 1


# Compares an incoming MQTT payload with a cached state to determine if an update is needed.
# This function prioritizes comparison by timestamp (`ts`) if available, updating only
# if the incoming message is newer. If timestamps are absent, it falls back to comparing
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