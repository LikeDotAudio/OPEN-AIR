import orjson
from ..manager_constants import splinker_logger

def _handle_command(self, topic, payload):
    """Unified command handler for both MQTT and internal Router events."""
    if not topic:
        splinker_logger.error("❌ Splinker: _handle_command received None as topic.")
        return

    parts = topic.split('/')
    if len(parts) < 5: 
        return

    command = parts[-1]
    splinker_logger.info(f"🔗 Splinker: Command '{command}' received on topic {topic}")
    splinker_logger.debug(f"🔗 Splinker: Raw Payload type={type(payload)}, value={payload}")

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
        splinker_logger.warning(f"⚠️ Splinker: Unknown command '{command}' received.")

def _unwrap_payload(self, payload):
    """Safely extracts data from MQTT bytes/str or direct dicts."""
    try:
        data = payload
        if isinstance(payload, (bytes, str)):
            data = orjson.loads(payload)
        
        if isinstance(data, dict) and "val" in data:
            return data["val"]
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
        splinker_logger.warning(f"⚠️ Splinker: DirectCreate received with invalid or empty payload: {data}")

def _process_update_command(self, splink_id, payload):
    """Specific logic for Update command."""
    data = self._unwrap_payload(payload)
    if data:
        self._update_splink(splink_id, data)
    else:
        splinker_logger.warning(f"⚠️ Splinker: Update for {splink_id} received with empty/None payload.")
