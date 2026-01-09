# builder_hidden/hidden_breakoff_manager.py
#
# The 'Break-off Snitch'. Reports if the widget is in a separate window.
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
import tkinter as tk


class HiddenBreakoffManagerMixin:
    """
    The 'Break-off Snitch'. Reports if the widget is in a separate window.
    """

    # Initializes the "Break-off Snitch" functionality.
    # This method sets up the necessary state variables and binds events to monitor
    # whether the widget has been "broken off" (torn off) into a separate top-level window.
    # Inputs:
    #     None.
    # Outputs:
    #     None.
    def _setup_breakoff_snitch(self):
        """Called during __init__ to bind events."""
        if not self.state_mirror_engine:
            return

        self.main_root = self.state_mirror_engine.root
        self.is_broken_off = False
        self.toplevel_window = None

        self.breakoff_topic = get_topic(
            self.state_mirror_engine.base_topic,
            self.base_mqtt_topic_from_path,
            "visibility/breakoff",
        )

        # Check the state when the widget is mapped
        self.bind("<Map>", self._check_breakoff_state)

    # Checks and updates the widget's break-off state.
    # This method determines if the widget is currently residing in a separate top-level
    # window (broken off) or in its original parent. It updates the internal state
    # and publishes the change via MQTT.
    # Inputs:
    #     event: The tkinter event object (optional).
    # Outputs:
    #     None.
    def _check_breakoff_state(self, event=None):
        """Checks if the widget has been broken off into a new window."""
        if not self.winfo_exists():
            return

        current_toplevel = self.winfo_toplevel()

        # State: Broken Off
        if current_toplevel is not self.main_root:
            if not self.is_broken_off:
                self.is_broken_off = True
                self.toplevel_window = current_toplevel
                self._publish_breakoff_state()
                self.toplevel_window.bind("<Configure>", self._on_broken_off_configure)
                self.toplevel_window.bind("<Destroy>", self._on_broken_off_destroy)

        # State: Not Broken Off (or returned)
        else:
            if self.is_broken_off:
                self.is_broken_off = False
                if self.toplevel_window:
                    try:
                        self.toplevel_window.unbind("<Configure>")
                        self.toplevel_window.unbind("<Destroy>")
                    except tk.TclError:
                        pass  # Window might already be destroyed
                self.toplevel_window = None
                self._publish_breakoff_state()

    # Handles geometry changes of a broken-off window.
    # When the user resizes or moves a widget that has been broken off into its own window,
    # this method captures the new geometry and publishes the updated state via MQTT.
    # Inputs:
    #     event: The tkinter Configure event object.
    # Outputs:
    #     None.
    def _on_broken_off_configure(self, event):
        """Handles geometry changes of the broken-off window."""
        self._publish_breakoff_state()

    # Handles the destruction of a broken-off window.
    # When a broken-off window is closed, this method updates the internal state
    # to reflect that the widget is no longer broken off and publishes this change via MQTT.
    # Inputs:
    #     event: The tkinter Destroy event object.
    # Outputs:
    #     None.
    def _on_broken_off_destroy(self, event):
        """Handles the destruction of the broken-off window."""
        if self.is_broken_off:
            # Make sure the event is for the toplevel window
            if event.widget == self.toplevel_window:
                self.is_broken_off = False
                self.toplevel_window = None
                self._publish_breakoff_state()
                # Don't publish here, as the visibility snitch will handle the destroy event of the widget itself.
                # and we might not be connected to the broker anymore

    # Publishes the current break-off state of the widget via MQTT.
    # This method creates a JSON payload containing information about whether the widget
    # is broken off, its geometry (if broken off), and other metadata, then publishes it
    # to a dedicated MQTT topic.
    # Inputs:
    #     None.
    # Outputs:
    #     None.
    def _publish_breakoff_state(self):
        if not is_connected():
            return

        width = 0
        height = 0
        x = 0
        y = 0

        if self.is_broken_off and self.toplevel_window:
            try:
                self.toplevel_window.update_idletasks()  # Ensure geometry is up to date
                width = self.toplevel_window.winfo_width()
                height = self.toplevel_window.winfo_height()
                x = self.toplevel_window.winfo_x()
                y = self.toplevel_window.winfo_y()
            except tk.TclError:
                # The window might be destroyed before we can get its geometry
                self.is_broken_off = False

        payload = {
            "is_broken_off": self.is_broken_off,
            "width": width,
            "height": height,
            "x": x,
            "y": y,
            "ts": time.time(),
            "tab_name": getattr(self, "tab_name", "Unknown"),
        }

        self.state_mirror_engine.publish_command(
            self.breakoff_topic, orjson.dumps(payload)
        )