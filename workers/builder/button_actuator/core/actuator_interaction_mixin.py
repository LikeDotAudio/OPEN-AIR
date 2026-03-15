import orjson
import time
from loguru import logger

class ActuatorInteractionMixin:
    """Handles mouse events and network triggers for the Momentary Actuator button."""

    def _on_press(self, event):
        """Handles the button press event."""
        logger.info(f"🖱️👆🔘 [INPUT] Press detected on actuator '{self.label}'")
        
        # 1. Local Feedback
        self.set_active(True)
        self.set_text(self.text_active)
        
        # Maintenance Command Handling
        scpi_msg = str(self.config.get("message", self.config.get("value", self.config.get("domain", {}).get("value", ""))))
        if self._handle_maintenance_command(scpi_msg):
            return 
        
        # 2. Network Action
        if self.state_mirror_engine:
            topic = self.state_mirror_engine.calculate_topic(f"{self.path}/trigger", self.base_mqtt_topic)
            payload = orjson.dumps({"val": True, "ts": time.time()})
            self.state_mirror_engine.publish_command(topic, payload)

    def _on_release(self, event):
        """Handles the button release event."""
        logger.info(f"🖱️🔙🔘 [INPUT] Release detected on actuator '{self.label}'")
        
        # 1. Local Feedback
        self.set_active(False)
        if self.text != "PASTE copied text into terminal":
            self.set_text(self.text_inactive)

        # Maintenance check
        scpi_msg = str(self.config.get("message", self.config.get("value", self.config.get("domain", {}).get("value", ""))))
        if self._is_maintenance(scpi_msg):
            return

        # 2. Network Action
        if self.state_mirror_engine:
            topic = self.state_mirror_engine.calculate_topic(f"{self.path}/trigger", self.base_mqtt_topic)
            payload = orjson.dumps({"val": False, "ts": time.time()})
            self.state_mirror_engine.publish_command(topic, payload)

    def _handle_maintenance_command(self, scpi_msg):
        """Checks if a command is a maintenance command and copies to clipboard if so."""
        if self._is_maintenance(scpi_msg):
            logger.debug(f"📋⌨️✨ [MAINT] Maintenance command detected. Copying: {scpi_msg}")
            try:
                self.master.clipboard_clear()
                self.master.clipboard_append(scpi_msg)
                self.set_text("PASTE copied text into terminal")
                self.after(3000, lambda: self.set_text(self.text_inactive))
            except Exception as e:
                logger.error(f"❌ Clipboard error: {e}")
            return True
        return False

    def _is_maintenance(self, msg):
        """Predicate for maintenance commands."""
        return (msg.startswith("*") or "SYSTem" in msg.upper() or 
                msg.startswith("sudo ") or msg.startswith("pkill "))
