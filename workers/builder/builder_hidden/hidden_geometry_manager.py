import time
import orjson
from workers.mqtt.mqtt_topic_utils import get_topic
from workers.mqtt.mqtt_publisher_service import is_connected


class HiddenGeometryManagerMixin:
    """
    The 'Geometry Snitch'. Reports the size and position of the widget's toplevel window.
    """

    def _setup_geometry_snitch(self):
        """Called during __init__ to bind events."""
        if not self.state_mirror_engine:
            return

        self.geometry_topic = get_topic(
            self.state_mirror_engine.base_topic,
            self.base_mqtt_topic_from_path,
            "visibility/geometry",
        )

        self.bind("<Configure>", self._on_geometry_change)

    def _on_geometry_change(self, event):
        """Handles the <Configure> event to report geometry."""
        toplevel = self.winfo_toplevel()
        if toplevel:
            self._publish_geometry(
                toplevel.winfo_width(),
                toplevel.winfo_height(),
                toplevel.winfo_x(),
                toplevel.winfo_y(),
            )

    def _publish_geometry(self, width, height, x, y):
        if not is_connected():
            return

        payload = {
            "width": width,
            "height": height,
            "x": x,
            "y": y,
            "ts": time.time(),
            "tab_name": getattr(self, "tab_name", "Unknown"),
        }

        self.state_mirror_engine.publish_command(
            self.geometry_topic, orjson.dumps(payload)
        )
