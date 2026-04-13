# Core/actuator_interaction_mixin.py
from oaGui.Methods.i18n_utils import get_text
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import orjson
from oaLogging.Methods.matrix_gate import matrix_log
import inspect
import time
from loguru import logger

class ActuatorInteractionMixin:
    """Handles mouse events and network triggers for the Momentary Actuator button."""

    def _on_press(self, event):
        """Handles the button press event."""
        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🖱️👆🔘 [INPUT] Press detected on actuator '{self.label}'", level="INFO")
        
        # 1. Local Feedback
        self.set_active(True)
        self.set_text(self.text_active)
        
        # Maintenance Command Handling
        scpi_message = str(self.config_data.get("message", self.config_data.get("value", self.config_data.get("domain", {}).get("value", ""))))
        if self._handle_maintenance_command(scpi_message):
            return 
        
        # 2. Network Action
        if self.state_mirror_engine:
            topic = self.state_mirror_engine.calculate_topic(f"{self.path}/trigger", self.base_mqtt_topic)
            payload = orjson.dumps({"value": True, "timestamp": time.time()})
            self.state_mirror_engine.publish_command(topic, payload)

    def _on_release(self, event):
        """Handles the button release event."""
        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🖱️🔙🔘 [INPUT] Release detected on actuator '{self.label}'", level="INFO")
        
        # 1. Local Feedback
        self.set_active(False)
        if self.text != "PASTE copied text into terminal":
            self.set_text(self.text_inactive)

        # Maintenance check
        scpi_message = str(self.config_data.get("message", self.config_data.get("value", self.config_data.get("domain", {}).get("value", ""))))
        if self._is_maintenance(scpi_message):
            return

        # 2. Network Action
        if self.state_mirror_engine:
            topic = self.state_mirror_engine.calculate_topic(f"{self.path}/trigger", self.base_mqtt_topic)
            payload = orjson.dumps({"value": False, "timestamp": time.time()})
            self.state_mirror_engine.publish_command(topic, payload)

    def _handle_maintenance_command(self, scpi_message):
        """Checks if a command is a maintenance command and copies to clipboard if so."""
        if self._is_maintenance(scpi_message):
            matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"📋⌨️✨ [MAINT] Maintenance command detected. Copying: {scpi_message}", level="DEBUG")
            try:
                self.master.clipboard_clear()
                self.master.clipboard_append(scpi_message)
                self.set_text("PASTE copied text into terminal")
                if hasattr(self, "winfo_exists") and self.winfo_exists():
                    self.after(3000, lambda: self.set_text(self.text_inactive))
            except Exception as e:
                logger.error(f"❌ Clipboard error: {e}")
            return True
        return False

    def _is_maintenance(self, message):
        """Predicate for maintenance commands."""
        return (message.startswith("*") or "SYSTem" in message.upper() or 
                message.startswith("sudo ") or message.startswith("pkill "))