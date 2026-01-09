# builder_hidden/hidden_geometry_manager.py
#
# The 'Geometry Snitch'. Reports the size and position of the widget's toplevel window.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Professional services for customizing and tailoring this software to your specific
# application can be negotiated. There is no charge to use, modify, or fork this software.
#
# Build Log: https://like.audio/category/software/spectrum-scanner/
# Source Code: https://github.com/APKaudio/
# Feature Requests can be emailed to i @ like . audio
#
# Version 20250821.200641.1
import time
import orjson
from workers.mqtt.mqtt_topic_utils import get_topic
from workers.mqtt.mqtt_publisher_service import is_connected


class HiddenGeometryManagerMixin:
    """
    The 'Geometry Snitch'. Reports the size and position of the widget's toplevel window.
    """

    # Initializes the "Geometry Snitch" functionality.
    # This method sets up the MQTT topic for publishing geometry updates and binds
    # to the Tkinter <Configure> event to detect changes in the widget's size or position.
    # Inputs:
    #     None.
    # Outputs:
    #     None.
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

    # Handles the <Configure> event for the widget's top-level window.
    # When the widget's parent window (toplevel) is resized or moved, this method
    # captures the new geometry and publishes it via MQTT.
    # Inputs:
    #     event: The tkinter Configure event object.
    # Outputs:
    #     None.
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

    # Publishes the current geometry (width, height, x, y) of the widget's window via MQTT.
    # This method creates a JSON payload with the geometry details and other metadata,
    # then publishes it to a dedicated MQTT topic.
    # Inputs:
    #     width (int): The width of the window.
    #     height (int): The height of the window.
    #     x (int): The x-coordinate of the window's top-left corner.
    #     y (int): The y-coordinate of the window's top-left corner.
    # Outputs:
    #     None.
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