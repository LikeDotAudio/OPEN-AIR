# Core/fader_bar_state_mixin.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import tkinter as tk
from oaLogging.Core.logger import builder_logger

# --- Standard Debug Logging Setup ---
BUILDER_DEBUG = True

class FaderBarStateMixin:
    """Handles multi-variable registration and MQTT synchronization for fader/meters."""

    def _register_vars(self):
        if not self.path: return
        if BUILDER_DEBUG: builder_logger.trace(f"📡 Registering multi-state for '{self.path}'")
        self._register_comp(self.fader_var, f"{self.path}/fader")
        self._register_comp(self.left_var, f"{self.path}/left_meter")
        self._register_comp(self.right_var, f"{self.path}/right_meter")

    def _register_comp(self, var, path):
        if not self.state_mirror_engine: return
        topic = self.state_mirror_engine.register_widget(path, var, self.base_mqtt_topic, self.widget_config)
        if self.subscriber_router and topic:
            self.subscriber_router.subscribe_to_topic(topic, self.state_mirror_engine.sync_incoming_mqtt_to_gui)
        self.state_mirror_engine.initialize_widget_state(path)
        var.trace_add("write", lambda *a: self.state_mirror_engine.broadcast_gui_change_to_mqtt(path))
