# Core/actuator_state_mixin.py
from oaGui.Methods.i18n_utils import get_text
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import orjson
from oaLogging.Methods.matrix_gate import matrix_log
import inspect
from loguru import logger

class ActuatorStateMixin:
    """Handles remote state synchronization for the Actuator button."""

    def _on_mqtt_state_update(self, msg):
        """Syncs the button's visual state with remote MQTT triggers."""
        try:
            payload = msg.payload
            data = orjson.loads(payload) if isinstance(payload, (bytes, str)) else payload
            is_active = data.get("val")

            matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"✨🔄🎨 [SYNC] Updating actuator '{self.path}' visual state to: {is_active}", level="DEBUG")
            self.set_active(is_active)
            self.set_text(self.text_active if is_active else self.text_inactive)
        except Exception as e:
            logger.error(f"❌ Critical failure in actuator MQTT update: {e}")