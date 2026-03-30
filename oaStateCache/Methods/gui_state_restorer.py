# Methods/gui_state_restorer.py
# Author: Anthony Peter Kuzub
# Version: 20250821.200641.1
#
# Description: State_Cache/gui_state_restorer.py

import inspect
from typing import Dict, Any, Optional
from oaComMQTT.Core.mqtt_message import MqttMessage

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = False    # Set to False in production, True for dev on this file
from oaLogging.Core.logger import initialize_logging, set_log_directory
from loguru import logger

from oaConfiguration.FileReaders.config_reader import Config

app_constants = Config.get_instance()

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
    if LOCAL_DEBUG: logger.info("⏪ Restoring State.")
    if not state_mirror_engine:
        logger.error("⏪❌ State Mirror Engine not available for restoration!")
        return

    if LOCAL_DEBUG: logger.info("⏪ Restoring GUI state from cache.")
    try:
        import orjson
        for topic, payload in cache_data.items():
            # ⚡ OPTIMIZATION: Extract 'val' for cleaner replaying logs
            val_str = ""
            try:
                if isinstance(payload, (str, bytes)):
                    data = orjson.loads(payload)
                else:
                    data = payload # Already parsed/dict
                
                if isinstance(data, dict) and "val" in data:
                    val_str = f" Val={data['val']}"
            except Exception as e:
                # ⚡ VOCAL: Cosmetic failure (just for cleaner logging), so trace is sufficient
                logger.trace(f"Cosmetic: Failed to extract 'val' for replaying log: {e}")

            if LOCAL_DEBUG: logger.trace(f"⏪🔄 Topic='{topic}'{val_str}")
            # ⚡ REFACTORED: Wrap in MqttMessage for Partitioned Architecture compatibility
            msg = MqttMessage(topic=topic, payload=payload)
            state_mirror_engine.sync_incoming_mqtt_to_gui(msg)
        if LOCAL_DEBUG: logger.success("⏪✅ Timeline restored!")
    except Exception:
        logger.exception("⏪❌ Error restoring timeline")
