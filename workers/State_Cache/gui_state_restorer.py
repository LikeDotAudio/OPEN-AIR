# State_Cache/gui_state_restorer.py
#
# Restores GUI state from cached data by replaying historical MQTT messages through the state mirror engine.
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

from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args

current_version = "20251230.230200.1"
current_version_hash = 20251230 * 230200 * 1


# Restores the GUI state from cached data by replaying historical MQTT messages.
# This function iterates through the provided `cache_data` (which represents
# past MQTT messages) and passes each entry to the `state_mirror_engine` to
# synchronize the GUI elements to their last known states.
# Inputs:
#     cache_data (Dict[str, Any]): A dictionary containing cached MQTT topics and their payloads.
#     state_mirror_engine (Any): An instance of the state mirror engine to handle GUI updates.
# Outputs:
#     None.
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