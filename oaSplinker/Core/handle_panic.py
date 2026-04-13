# Core/handle_panic.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

from ..Constants.constants import splinker_logger

def handle_panic(self, trigger_splink_id=None):
    """Emergency shutdown of all splinks."""
    self.panic_active = True
    
    message = f"🆘 SPLINKER PANIC TRIGGERED! Emergency stop active."
    if trigger_splink_id:
        message = f"🆘 SPLINKER PANIC TRIGGERED by splink [{trigger_splink_id}]! High-frequency loop detected."
    
    splinker_logger.critical(message)
    
    # Deactivate all splinks
    for s in self.splinks:
        if s.get("active"):
            s["active"] = False
            splinker_logger.warning(f"  🛑 Deactivating splink [{s['id']}] for safety.")
            # Trigger persistence
            self.save_splink(s)

    # Notify UI/MQTT
    import orjson
    panic_payload = {"value": True, "trigger_id": trigger_splink_id}
    
    self.notify_monitor("panic", panic_payload)
    if self.mqtt_manager:
        self.mqtt_manager.publish(
            "OPEN-AIR/System/Status/Splinker/Panic", 
            orjson.dumps(panic_payload).decode(), 
            retain=True
        )
    
    # Broadcast to ProtocolRouter for system-wide awareness
    if hasattr(self, 'router') and self.router:
        self.router.ingest("SPLINKER", "OPEN-AIR/System/Status/Splinker/Panic", True)

def _reset_panic(self):
    """Clear the panic state."""
    import orjson
    self.panic_active = False
    splinker_logger.info("✅ SPLINKER PANIC RESET. Ready for operation.")
    
    reset_payload = {"value": False}
    self.notify_monitor("panic", reset_payload)
    if self.mqtt_manager:
        self.mqtt_manager.publish(
            "OPEN-AIR/System/Status/Splinker/Panic", 
            orjson.dumps(reset_payload).decode(), 
            retain=True
        )
