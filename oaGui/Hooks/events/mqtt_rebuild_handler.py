# Hooks/mqtt_rebuild_handler.py
# Author: Anthony Peter Kuzub
# Version: 20260501.1000.1
#
# Description: Handles remote UI rebuild requests via MQTT.

import orjson
from pathlib import Path
from oaLogging.Methods.matrix_gate import matrix_log

class MqttRebuildHandler:
    """Handles remote UI rebuild requests via MQTT."""
    @staticmethod
    def handle_request(builder, message):
        """Processes an incoming rebuild request and triggers the builder if applicable."""
        payload = message.payload
        if not payload: return

        if not (payload.startswith(b"{") or payload.startswith("{")):
            return

        try:
            data = orjson.loads(payload)
            target_path = data.get("path")
            new_config = data.get("config")

            if target_path and str(Path(target_path).resolve()) == str(builder.json_filepath.resolve()):
                matrix_log("ui", "gui_shell", "MqttRebuildHandler", 
                           f"♻️ MQTT: Rebuild request received for '{builder.tab_name}'. Injecting new config...", "INFO")

                if new_config:
                    builder.configuration = new_config

                if hasattr(builder, "_rebuild_gui"):
                    builder.after(0, builder._rebuild_gui)
        except Exception:
            pass
