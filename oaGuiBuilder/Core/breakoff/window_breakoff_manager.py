# oaGuiBuilder/Core/breakoff/window_breakoff_manager.py
# Author: Anthony Peter Kuzub
# Version: 20260416.Modular.1
#
# Description: Monitors and reports if a widget has been "broken off" into a 
# separate Toplevel window. Orchestrates state synchronization via MQTT.

import time
import orjson
import tkinter as tk
from oaComProtocols.oaComMQTT.Methods.mqtt_topic_utils import get_topic
from oaComProtocols.oaComMQTT.Core.mqtt_publisher_service import is_connected

class WindowBreakoffManagerMixin:
    """
    The 'Break-off Snitch'. Detects window reparenting and publishes 
    physical window geometry to the system.
    """

    def _setup_breakoff_monitoring(self):
        """Initializes state and binds mapping events to trigger detection."""
        if not hasattr(self, "state_mirror_engine") or not self.state_mirror_engine:
            return
        if not self.state_mirror_engine.root:
            return

        # ⚡ OPTIMIZATION: Disable monitoring in interactive editor preview
        if getattr(self, "tab_name", "") == "InteractivePreview":
            return

        self.main_root = self.state_mirror_engine.root
        self.is_broken_off = False
        self.toplevel_window = None

        self.breakoff_topic = get_topic(
            self.state_mirror_engine.base_topic,
            self.base_mqtt_topic_from_path,
            "visibility/breakoff",
        )

        # Trigger check whenever the widget is mapped to the screen
        self.bind("<Map>", self._check_breakoff_state)

    def _check_breakoff_state(self, event=None):
        """Determines if the current toplevel differs from the application root."""
        if not self.winfo_exists():
            return

        if not hasattr(self, "main_root") or not self.main_root:
            return

        current_toplevel = self.winfo_toplevel()

        if current_toplevel is not self.main_root:
            self._handle_broken_off(current_toplevel)
        else:
            self._handle_docked()

    def _handle_broken_off(self, toplevel):
        """Transitions to broken-off state and binds window lifecycle events."""
        if not self.is_broken_off:
            self.is_broken_off = True
            self.toplevel_window = toplevel
            
            # Wire up geometry and destruction tracking
            self.toplevel_window.bind("<Configure>", self._on_breakoff_configure)
            self.toplevel_window.bind("<Destroy>", self._on_breakoff_destroy)
            
            self._publish_breakoff_state()

    def _handle_docked(self):
        """Transitions back to docked state and cleans up window bindings."""
        if self.is_broken_off:
            self.is_broken_off = False
            if self.toplevel_window:
                try:
                    self.toplevel_window.unbind("<Configure>")
                    self.toplevel_window.unbind("<Destroy>")
                except tk.TclError:
                    pass # Window already dead
            self.toplevel_window = None
            self._publish_breakoff_state()

    def _on_breakoff_configure(self, event):
        """Reacts to physical window movement or resizing."""
        if event.widget == self.toplevel_window:
            self._publish_breakoff_state()

    def _on_breakoff_destroy(self, event):
        """Reacts to the Toplevel window being closed."""
        if self.is_broken_off and event.widget == self.toplevel_window:
            self.is_broken_off = False
            self.toplevel_window = None
            self._publish_breakoff_state()

    def _publish_breakoff_state(self):
        """Orchestrates MQTT payload creation and command publishing."""
        if not is_connected() or not self.state_mirror_engine:
            return

        payload = self._create_breakoff_payload()
        self.state_mirror_engine.publish_command(
            self.breakoff_topic, orjson.dumps(payload).decode()
        )

    def _create_breakoff_payload(self):
        """Calculates current window geometry for the MQTT payload."""
        geom = {"w": 0, "h": 0, "x": 0, "y": 0}
        
        if self.is_broken_off and self.toplevel_window:
            try:
                geom["w"] = self.toplevel_window.winfo_width()
                geom["h"] = self.toplevel_window.winfo_height()
                geom["x"] = self.toplevel_window.winfo_x()
                geom["y"] = self.toplevel_window.winfo_y()
            except tk.TclError:
                self.is_broken_off = False # Fallback if window vanished

        return {
            "is_broken_off": self.is_broken_off,
            "width": geom["w"],
            "height": geom["h"],
            "x": geom["x"],
            "y": geom["y"],
            "timestamp": time.time(),
            "tab_name": getattr(self, "tab_name", "Unknown"),
        }
