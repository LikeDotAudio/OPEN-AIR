# State_Cache/cache_traffic_controller.py
#
# Acts as a middleware for incoming MQTT messages, decoding payloads and determining if cache updates are necessary.
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

import orjson
import inspect
from typing import Dict, Any, Tuple, Optional

from . import state_comparator
from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args

current_version = "20251230.230300.1"
current_version_hash = 20251230 * 230300 * 1


# Processes incoming MQTT messages, decodes their payloads, and determines if an update to the cache is required.
# This function acts as a gatekeeper, checking for redundancy by comparing the new payload
# with the current cache state. If a significant change is detected, it signals that an update is needed.
# Inputs:
#     topic (str): The MQTT topic of the incoming message.
#     payload (str): The raw payload of the message.
#     current_cache (Dict): The current state of the application cache.
# Outputs:
#     Tuple[bool, Optional[Dict]]: A tuple indicating whether an update is needed (True/False)
#                                  and the new payload (if an update is needed, None otherwise).
def process_traffic(
    topic: str, payload: str, current_cache: Dict
) -> Tuple[bool, Optional[Dict]]:
    """
    Decodes payload.
    Calls state_comparator.
    Returns (True, new_payload) if the GUI needs an update.
    Returns (False, None) if it's redundant.
    """
    debug_logger(
        message=f"tt! A new event is rippling through the timeline! Topic: {topic}",
        **_get_log_args(),
    )
    try:
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")

        new_payload = orjson.loads(payload)
        debug_logger(
            message="🧑‍⚖️ Payload decoded. Now, to the Judge!", **_get_log_args()
        )

        if state_comparator.should_update(topic, new_payload, current_cache):
            debug_logger(
                message=f"⚓ A change in the timeline! This is heavy. Topic: {topic}",
                **_get_log_args(),
            )
            return True, new_payload
        else:
            debug_logger(
                message="🧘 No change detected. The timeline is stable... for now.",
                **_get_log_args(),
            )
            return False, None
    except Exception as e:
        debug_logger(
            message=f"t! The traffic controller has short-circuited! {e}",
            **_get_log_args(),
        )
        return False, None