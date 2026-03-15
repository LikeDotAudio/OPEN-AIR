import orjson
from ..manager_constants import splinker_logger

def _handle_command(self, topic, payload):
    """Unified command handler for both MQTT and internal Router events."""
    if not topic:
        splinker_logger.error("❌ Splinker: _handle_command received None as topic.")
        return

    parts = topic.split('/')
    if len(parts) < 5: return

    command = parts[-1]
    
    splinker_logger.info(f"🔗 Splinker: Command '{command}' received on topic {topic}")
    splinker_logger.debug(f"🔗 Splinker: Raw Payload type={type(payload)}, value={payload}")

    if command == "Create":
        self.create_splink()
        return
    elif command == "Panic":
        self._handle_panic()
        return
    elif command == "ResetPanic":
        self._reset_panic()
        return
    elif command == "Refresh":
        self._load_splinks()
        return
    elif command == "DirectCreate":
        try:
            # Payload might be bytes (from MQTT) or dict (from internal Router ingest)
            data = payload
            if isinstance(payload, (bytes, str)):
                data = orjson.loads(payload)
            
            # ⚡ UNWRAP: Check if it's in a standard 'val' envelope
            if isinstance(data, dict) and "val" in data:
                data = data["val"]

            if data and isinstance(data, dict):
                self.create_splink_with_params(
                    data.get("source"), 
                    data.get("dest"),
                    source_val=data.get("source_val"),
                    dest_val=data.get("dest_val")
                )
            else:
                splinker_logger.warning(f"⚠️ Splinker: DirectCreate received with invalid or empty payload: {data}")
        except Exception as e:
            splinker_logger.error(f"❌ Splinker: Failed to parse DirectCreate: {e}")
        return
        
    splink_id = parts[-2]
    if command == "Learn":
        self.set_learn_mode(splink_id)
    elif command == "Teach":
        self.set_teach_mode(splink_id)
    elif command == "Delete":
        self.delete_splink(splink_id)
    elif command == "Update":
        try:
            data = payload
            if isinstance(payload, (bytes, str)):
                data = orjson.loads(payload)
            
            # ⚡ UNWRAP
            if isinstance(data, dict) and "val" in data:
                data = data["val"]

            if data:
                self._update_splink(splink_id, data)
            else:
                splinker_logger.warning(f"⚠️ Splinker: Update command for {splink_id} received with empty/None payload. Ignoring.")
        except Exception as e:
            splinker_logger.error(f"❌ Splinker: Failed to parse Update for {splink_id}: {e}")
