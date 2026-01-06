# workers/State_Cache/cache_traffic_controller.py
#
# Version 20251230.230300.1
#
# Author: Gemini
#
# The Gatekeeper: Middleware for the MQTT Listener.

import orjson
import inspect
from typing import Dict, Any, Tuple, Optional

from . import state_comparator
from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args

current_version = "20251230.230300.1"
current_version_hash = 20251230 * 230300 * 1


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
