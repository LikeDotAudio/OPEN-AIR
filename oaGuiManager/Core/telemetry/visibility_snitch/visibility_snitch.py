# visibility_snitch/visibility_snitch.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import time
import orjson
from oaComMQTT.Methods.mqtt_topic_utils import get_topic
from oaComMQTT.Core.mqtt_publisher_service import is_connected
from loguru import logger

LOCAL_DEBUG = False    # Set to False in production, True for dev on this file

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

        if LOCAL_DEBUG: logger.trace(f"👁️ VisibilitySnitch: Monitoring visibility for {self.tab_name}")
        self.bind("<Map>", self._on_gui_visible)
        self.bind("<Unmap>", self._on_gui_hidden)
        self.bind("<Destroy>", self._on_gui_destroy)

    def _on_gui_visible(self, event):
        """User can see this tab."""
        if LOCAL_DEBUG: logger.debug(f"👁️ VisibilitySnitch: VISIBLE (Map) for {self.tab_name}")
        self._publish_visibility(True)
        if hasattr(self, "_on_geometry_change"):
            self._on_geometry_change(event)

    def _on_gui_hidden(self, event):
        """User switched tabs or minimized."""
        if LOCAL_DEBUG: logger.debug(f"👁️ VisibilitySnitch: HIDDEN (Unmap) for {self.tab_name}")
        self._publish_visibility(False)

    def _on_gui_destroy(self, event):
        """Widget is being destroyed."""
        if event.widget == self:
            if LOCAL_DEBUG: logger.debug(f"👁️ VisibilitySnitch: DESTROYED for {self.tab_name}")
            self._publish_visibility(False)

    def _publish_visibility(self, is_visible: bool):
        # 🧊 [ON ICE] Visibility telemetry is currently suspended for re-architecture.
        #     return

        # payload = {
        #     "visible": is_visible,
        #     "ts": time.time(),
        #     "tab_name": getattr(self, "tab_name", "Unknown"),
        # }
        # self.state_mirror_engine.publish_command(
        #     self.visibility_topic, orjson.dumps(payload).decode()
        # )
        pass
