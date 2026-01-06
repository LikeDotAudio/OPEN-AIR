import time
import orjson
from workers.mqtt.mqtt_topic_utils import get_topic
from workers.mqtt.mqtt_publisher_service import is_connected


class HiddenVisibilityManagerMixin:
    """
    The 'Snitch'. Reports to MQTT when this GUI is visible or hidden.
    """

    def _setup_visibility_snitch(self):
        """Called during __init__ to bind events."""
        if not self.state_mirror_engine:
            return

        # Create a specific topic: .../TabName/_META/visible
        self.visibility_topic = get_topic(
            self.state_mirror_engine.base_topic,
            self.base_mqtt_topic_from_path,
            "visibility/visible",
        )

        # Bind to Tkinter Map (Show) and Unmap (Hide) events
        self.bind("<Map>", self._on_gui_visible)
        self.bind("<Unmap>", self._on_gui_hidden)
        self.bind("<Destroy>", self._on_gui_destroy)

    def _on_gui_visible(self, event):
        """User can see this tab."""
        self._publish_visibility(True)
        if hasattr(self, "_on_geometry_change"):
            self._on_geometry_change(event)

    def _on_gui_hidden(self, event):
        """User switched tabs or minimized."""
        self._publish_visibility(False)

    def _on_gui_destroy(self, event):
        """Widget is being destroyed."""
        # Ensure the event is for this widget specifically
        if event.widget == self:
            self._publish_visibility(False)

    def _publish_visibility(self, is_visible: bool):
        if not is_connected():
            return

        payload = {
            "visible": is_visible,
            "ts": time.time(),
            "tab_name": getattr(self, "tab_name", "Unknown"),
        }
        # Use the engine from the main class
        self.state_mirror_engine.publish_command(
            self.visibility_topic, orjson.dumps(payload)
        )
