from oaLogging.Methods.matrix_gate import matrix_log
# Methods/gui_state_restorer.py
# Author: Anthony Peter Kuzub
# Version: 20250821.200641.1
#
# Description: State_Cache/gui_state_restorer.py

import inspect
from typing import Dict, Any, Optional
from oaComProtocols.oaComMQTT.Core.mqtt_message import MqttMessage

# --- Standard Debug Logging Setup ---
from oaLogging.Core.logger import initialize_logging, set_log_directory
from loguru import logger

from oaConfigurationManager.FileReaders.config_reader import Config

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
        # Use debug instead of error to reduce noise during early boot partitions
        logger.debug("⏪ℹ️ State Mirror Engine not available for restoration (skipping GUI replay).")
        return

    matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "⏪ Restoring GUI state from cache.", "INFO")
    try:
        import orjson
        for topic, payload in cache_data.items():
            # ⚡ OPTIMIZATION: Extract 'value' for cleaner replaying logs
            val_str = ""
            try:
                if isinstance(payload, (str, bytes)):
                    data = orjson.loads(payload)
                else:
                    data = payload # Already parsed/dict
                
                if isinstance(data, dict) and "value" in data:
                    val_str = f" Val={data['value']}"
            except Exception as e:
                # ⚡ VOCAL: Cosmetic failure (just for cleaner logging), so trace is sufficient
                matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"Cosmetic: Failed to extract 'value' for replaying log: {e}", "TRACE")

            matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"⏪🔄 Topic='{topic}'{val_str}", "TRACE")
            
            # ⚡ V3.1.22 RECURSION GUARD (RESTORE PHASE):
            # Skip topics that have recursive protocol segments (corrupted paths).
            if any(x + "/" + x + "/" in str(topic) for x in ["OSC", "MIDI", "GUI", "oaGui", "MQTT"]):
                matrix_log("core", "system", "restore_timeline", f"🛡️ [GUARD] Skipping corrupted recursive topic: {topic}", "DEBUG")
                continue

            # ⚡ REFACTORED: Wrap in MqttMessage for Partitioned Architecture compatibility
            # Only process valid functional state topics (Exclude System/Monitor/Heartbeat)
            volatile = any(x in str(topic) for x in ["/System/", "/Monitor/", "/Heartbeat/"])
            if topic.startswith("OPEN-AIR/") and not volatile:
                message = MqttMessage(topic=topic, payload=payload)
                state_mirror_engine.sync_incoming_mqtt_to_gui(message)
            else:
                # Log or handle non-functional data if necessary
                matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"Skipping non-functional topic in cache: {topic}", "DEBUG")

            # ⚡ STABILITY: Replaying state directly into the GUI is expensive (redraws, reslices).
            # Throttle to 2ms per message to prevent overwhelming the main thread.
            import time
            time.sleep(0.002)
        matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "⏪✅ Timeline restored!", "SUCCESS")
    except Exception:
        logger.exception("⏪❌ Error restoring timeline")
