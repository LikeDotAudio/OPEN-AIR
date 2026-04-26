# visibility_snitch/visibility_snitch.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import inspect

from oaComProtocols.oaComMQTT.Methods.mqtt_topic_utils import get_topic
from oaLogging.Methods.matrix_gate import matrix_log


class HiddenVisibilityManagerMixin:
    """
    The 'Snitch'. Reports to MQTT when this GUI is visible or hidden.
    """

    def _setup_visibility_snitch(self):
        """Called during __init__ to bind events."""
        if not self.state_mirror_engine:
            return

        if getattr(self, "tab_name", "") == "InteractivePreview":
            return

        self.visibility_topic = get_topic(
            self.state_mirror_engine.base_topic,
            self.base_mqtt_topic_from_path,
            "visibility/visible",
        )

        matrix_log("UI", "GUI_MANAGER", inspect.currentframe().f_code.co_name, f"👁️ VisibilitySnitch: Monitoring visibility for {self.tab_name}", level="TRACE")
        self.bind("<Map>", self._on_gui_visible)
        self.bind("<Unmap>", self._on_gui_hidden)
        self.bind("<Destroy>", self._on_gui_destroy)

    def _on_gui_visible(self, event):
        """User can see this tab."""
        matrix_log("UI", "GUI_MANAGER", inspect.currentframe().f_code.co_name, f"👁️ VisibilitySnitch: VISIBLE (Map) for {self.tab_name}", level="DEBUG")
        self._publish_visibility(True)
        if hasattr(self, "_on_geometry_change"):
            self._on_geometry_change(event)

    def _on_gui_hidden(self, event):
        """User switched tabs or minimized."""
        matrix_log("UI", "GUI_MANAGER", inspect.currentframe().f_code.co_name, f"👁️ VisibilitySnitch: HIDDEN (Unmap) for {self.tab_name}", level="DEBUG")
        self._publish_visibility(False)

    def _on_gui_destroy(self, event):
        """Widget is being destroyed."""
        if event.widget == self:
            matrix_log("UI", "GUI_MANAGER", inspect.currentframe().f_code.co_name, f"👁️ VisibilitySnitch: DESTROYED for {self.tab_name}", level="DEBUG")
            self._publish_visibility(False)

    def _publish_visibility(self, is_visible: bool):
        # 🧊 [ON ICE] Visibility telemetry is currently suspended for re-architecture.
        #     return

        # payload = {
        #     "visible": is_visible,
        #     "timestamp": time.time(),
        #     "tab_name": getattr(self, "tab_name", "Unknown"),
        # }
        # self.state_mirror_engine.publish_command(
        #     self.visibility_topic, orjson.dumps(payload).decode()
        # )
        pass
