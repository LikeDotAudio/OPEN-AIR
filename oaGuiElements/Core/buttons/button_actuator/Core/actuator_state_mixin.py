# Core/actuator_state_mixin.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import inspect

import orjson
from loguru import logger

from oaLogging.Methods.matrix_gate import matrix_log


class ActuatorStateMixin:
    """Handles remote state synchronization for the Actuator button."""

    def _on_mqtt_state_update(self, message):
        """Syncs the button's visual state with remote MQTT triggers."""
        try:
            payload = message.payload
            data = orjson.loads(payload) if isinstance(payload, (bytes, str)) else payload
            is_active = data.get("value")

            matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"✨🔄🎨 [SYNC] Updating actuator '{self.path}' visual state to: {is_active}", level="DEBUG")
            self.set_active(is_active)
            self.set_text(self.text_active if is_active else self.text_inactive)
        except Exception as e:
            logger.error(f"❌ Critical failure in actuator MQTT update: {e}")
