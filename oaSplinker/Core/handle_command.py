# Core/handle_command.py
#
# Unified command handler for both MQTT and internal Router events.
# Processes Splinker-specific control messages and dispatches them 
# to the appropriate internal logic.
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
# Version 20260330.1600.1

import orjson
from ..Constants.constants import splinker_logger
from oaLogging.Methods.matrix_gate import matrix_log

def handle_command(self, topic, payload):
    """Unified command handler for both MQTT and internal Router events."""
    if not topic:
        splinker_logger.error("❌ Splinker: _handle_command received None as topic.")
        return

    parts = topic.split('/')
    if len(parts) < 5: 
        return

    command = parts[-1]
    matrix_log("core", "splinker", "handle_command", f"🔗 Splinker: Command '{command}' received on topic {topic}", "INFO")
    matrix_log("core", "splinker", "handle_command", f"🔗 Splinker: Raw Payload type={type(payload)}, value={payload}", "DEBUG")

    # 1. Global Commands (No Splink ID required)
    global_handlers = {
        "Create": self.create_splink,
        "Panic": self._handle_panic,
        "ResetPanic": self._reset_panic,
        "Refresh": self._load_splinks,
        "DirectCreate": lambda: self._process_direct_create(payload)
    }

    if command in global_handlers:
        global_handlers[command]()
        return

    # 2. Instance Commands (Splink ID required)
    splink_id = parts[-2]
    instance_handlers = {
        "Learn": lambda: self.set_learn_mode(splink_id),
        "Teach": lambda: self.set_teach_mode(splink_id),
        "Delete": lambda: self.delete_splink(splink_id),
        "Update": lambda: self._process_update_command(splink_id, payload)
    }

    if command in instance_handlers:
        instance_handlers[command]()
    else:
        matrix_log("core", "splinker", "handle_command", f"⚠️ Splinker: Unknown command '{command}' received.", "WARNING")

def _unwrap_payload(self, payload):
    """Safely extracts data from MQTT bytes/str or direct dicts."""
    try:
        data = payload
        if isinstance(payload, (bytes, str)):
            data = orjson.loads(payload)
        
        if isinstance(data, dict) and "value" in data:
            return data["value"]
        return data
    except Exception as e:
        splinker_logger.error(f"❌ Splinker: Failed to unwrap payload: {e}")
        return None

def _process_direct_create(self, payload):
    """Specific logic for DirectCreate command."""
    data = self._unwrap_payload(payload)
    if data and isinstance(data, dict):
        self.create_splink_with_params(
            data.get("source"), 
            data.get("dest"),
            source_val=data.get("source_val"),
            dest_val=data.get("dest_val")
        )
    else:
        matrix_log("core", "splinker", "_process_direct_create", f"⚠️ Splinker: DirectCreate received with invalid or empty payload: {data}", "WARNING")

def _process_update_command(self, splink_id, payload):
    """Specific logic for Update command."""
    data = self._unwrap_payload(payload)
    if data:
        self.update_splink(splink_id, data)
    else:
        matrix_log("core", "splinker", "_process_update_command", f"⚠️ Splinker: Update for {splink_id} received with empty/None payload.", "WARNING")
