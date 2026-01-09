# builder_hidden/hidden_visibility_manager.py
#
# The 'Snitch'. Reports to MQTT when this GUI is visible or hidden.
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


class HiddenVisibilityManagerMixin:
    """
    The 'Snitch'. Reports to MQTT when this GUI is visible or hidden.
    """

    # Initializes the "Visibility Snitch" functionality.
    # This method sets up the MQTT topic for publishing visibility updates and binds
    # to the Tkinter Map, Unmap, and Destroy events to monitor the widget's visibility state.
    # Inputs:
    #     None.
    # Outputs:
    #     None.
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

    # Handles the event when the GUI widget becomes visible.
    # This method is triggered when the widget is mapped (becomes visible to the user).
    # It publishes the 'visible' state via MQTT and optionally triggers a geometry update.
    # Inputs:
    #     event: The tkinter Map event object.
    # Outputs:
    #     None.
    def _on_gui_visible(self, event):
        """User can see this tab."""
        self._publish_visibility(True)
        if hasattr(self, "_on_geometry_change"):
            self._on_geometry_change(event)

    # Handles the event when the GUI widget becomes hidden.
    # This method is triggered when the widget is unmapped (hidden from the user, e.g., tab switch).
    # It publishes the 'hidden' state via MQTT.
    # Inputs:
    #     event: The tkinter Unmap event object.
    # Outputs:
    #     None.
    def _on_gui_hidden(self, event):
        """User switched tabs or minimized."""
        self._publish_visibility(False)

    # Handles the event when the GUI widget is destroyed.
    # This method is triggered when the widget is permanently removed. It publishes
    # the 'hidden' state via MQTT, ensuring the system is aware of the widget's removal.
    # Inputs:
    #     event: The tkinter Destroy event object.
    # Outputs:
    #     None.
    def _on_gui_destroy(self, event):
        """Widget is being destroyed."""
        # Ensure the event is for this widget specifically
        if event.widget == self:
            self._publish_visibility(False)

    # Publishes the current visibility state of the widget via MQTT.
    # This method creates a JSON payload indicating whether the widget is visible or hidden,
    # along with a timestamp and the tab name, and publishes it to a dedicated MQTT topic.
    # Inputs:
    #     is_visible (bool): True if the widget is visible, False otherwise.
    # Outputs:
    #     None.
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