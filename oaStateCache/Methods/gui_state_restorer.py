# Methods/gui_state_restorer.py
# Author: Anthony Peter Kuzub
# Version: 20250821.200641.1
#
# Description: State_Cache/gui_state_restorer.py
from typing import Any

from oaComProtocols.oaComMQTT.Core.mqtt_message import MqttMessage
from oaConfigurationManager.FileReaders.config_reader import Config

# --- Standard Debug Logging Setup ---
from oaLogging.Methods.matrix_gate import matrix_log

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
def restore_timeline(cache_data: dict[str, Any], state_mirror_engine: Any) -> None:
    """
    Iterate through the cache_data in batches using the GUI event loop.
    This prevents the main thread from locking up and allows the UI to remain responsive.
    """
    if not state_mirror_engine:
        matrix_log("core", "system", "restore_timeline", "⏪ℹ️ State Mirror Engine not available for restoration.", "DEBUG")
        return

    matrix_log("core", "system", "restore_timeline", f"⏪ Starting state restoration ({len(cache_data)} topics).", "INFO")

    items = list(cache_data.items())
    batch_size = 50

    def process_batch(start_idx):
        end_idx = min(start_idx + batch_size, len(items))
        batch = items[start_idx:end_idx]

        for topic, payload in batch:
            # ⚡ V3.1.22 RECURSION GUARD:
            if any(x + "/" + x + "/" in str(topic) for x in ["OSC", "MIDI", "GUI", "oaGui", "MQTT"]):
                continue

            volatile = any(x in str(topic) for x in ["/System/", "/Monitor/", "/Heartbeat/"])
            if topic.startswith("OpenAir/") and not volatile:
                message = MqttMessage(topic=topic, payload=payload)
                state_mirror_engine.sync_incoming_mqtt_to_gui(message)

        if end_idx < len(items):
            # Schedule next batch
            if hasattr(state_mirror_engine, "root") and state_mirror_engine.root:
                state_mirror_engine.root.after(1, lambda: process_batch(end_idx))
            else:
                # Headless/fallback: sync process with tiny sleep
                import time
                time.sleep(0.01)
                process_batch(end_idx)
        else:
            matrix_log("core", "system", "restore_timeline", "⏪✅ Timeline restoration complete.", "SUCCESS")

    # Launch initial batch
    process_batch(0)
