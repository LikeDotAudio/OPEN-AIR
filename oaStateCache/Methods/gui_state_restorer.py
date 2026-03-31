from oaLogging.Methods.matrix_gate import matrix_log
# Methods/gui_state_restorer.py
# Author: Anthony Peter Kuzub
# Version: 20250821.200641.1
#
# Description: State_Cache/gui_state_restorer.py

import inspect
from typing import Dict, Any, Optional
from oaComMQTT.Core.mqtt_message import MqttMessage

# --- Standard Debug Logging Setup ---
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
    matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "⏪ Restoring State.", "INFO")
    if not state_mirror_engine:
        logger.error("⏪❌ State Mirror Engine not available for restoration!")
        return

    matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "⏪ Restoring GUI state from cache.", "INFO")
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
                matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"Cosmetic: Failed to extract 'val' for replaying log: {e}", "TRACE")

            matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"⏪🔄 Topic='{topic}'{val_str}", "TRACE")
            # ⚡ REFACTORED: Wrap in MqttMessage for Partitioned Architecture compatibility
            msg = MqttMessage(topic=topic, payload=payload)
            state_mirror_engine.sync_incoming_mqtt_to_gui(msg)
        matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "⏪✅ Timeline restored!", "SUCCESS")
    except Exception:
        logger.exception("⏪❌ Error restoring timeline")
