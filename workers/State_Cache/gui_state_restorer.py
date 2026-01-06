# workers/State_Cache/gui_state_restorer.py
#
# Version 20251230.230200.1
#
# Author: Gemini
#
# The Time Traveler: Run ONCE at startup to blast the cached data into the GUI.

import inspect
from typing import Dict, Any, Optional

from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args

current_version = "20251230.230200.1"
current_version_hash = 20251230 * 230200 * 1


def restore_timeline(cache_data: Dict[str, Any], state_mirror_engine: Any) -> None:
    """
    Iterate through the cache_data.
    Trigger the specific GUI update methods in display (or via the state_mirror if accessible)
    to visually set the knobs/labels/graphs.
    """
    debug_logger(message="t! Engaging the Time Circuits!", **_get_log_args())
    if not state_mirror_engine:
        debug_logger(
            message="tt! State Mirror Engine not available for timeline restoration!",
            **_get_log_args(),
        )
        return

    debug_logger(
        message="t! We're going back in time! Restoring GUI state from the Almanac.",
        **_get_log_args(),
    )
    try:
        for topic, payload in cache_data.items():
            debug_logger(
                message=f"🔄 Replaying event from the past: Topic='{topic}'",
                **_get_log_args(),
            )
            state_mirror_engine.sync_incoming_mqtt_to_gui(topic, payload)
        debug_logger(
            message="tt! The timeline has been successfully restored!",
            **_get_log_args(),
        )
    except Exception as e:
        debug_logger(
            message=f"tt! A paradox has occurred! Failed to restore the timeline: {e}",
            **_get_log_args(),
        )
