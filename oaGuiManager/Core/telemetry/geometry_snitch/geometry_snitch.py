# geometry_snitch/geometry_snitch.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import time
from oaLogging.Methods.matrix_gate import matrix_log
import inspect
import orjson
from oaComProtocols.oaComMQTT.Methods.mqtt_topic_utils import get_topic
from oaComProtocols.oaComMQTT.Core.mqtt_publisher_service import is_connected
from loguru import logger


class HiddenGeometryManagerMixin:
    """
    The 'Geometry Snitch'. Reports the size and position of the widget's toplevel window.
    """

    def _setup_geometry_snitch(self):
        """Called during __init__ to bind events."""
        if not self.state_mirror_engine:
            return

        if getattr(self, "tab_name", "") == "InteractivePreview":
            return

        self.geometry_topic = get_topic(
            self.state_mirror_engine.base_topic,
            self.base_mqtt_topic_from_path,
            "visibility/geometry",
        )

        matrix_log("UI", "GUI_MANAGER", inspect.currentframe().f_code.co_name, f"📏 GeometrySnitch: Monitoring toplevel for {self.tab_name}", level="TRACE")
        self.bind("<Configure>", self._on_geometry_change)

    def _on_geometry_change(self, event):
        """Handles the <Configure> event to report geometry."""
        if not hasattr(self, "_geometry_timer"):
            self._geometry_timer = None
            
        if self._geometry_timer:
            self.after_cancel(self._geometry_timer)
            
        toplevel = self.winfo_toplevel()
        if toplevel:
            w, h, x, y = toplevel.winfo_width(), toplevel.winfo_height(), toplevel.winfo_x(), toplevel.winfo_y()
            matrix_log("UI", "GUI_MANAGER", inspect.currentframe().f_code.co_name, f"📏 GeometrySnitch: GALLOP detected for {self.tab_name} ({w}x{h} @ {x},{y}). Debouncing...", level="TRACE")
            self._geometry_timer = self.after(500, lambda: self._perform_geometry_publish(w, h, x, y))

    def _perform_geometry_publish(self, w, h, x, y):
        self._geometry_timer = None
        matrix_log("UI", "GUI_MANAGER", inspect.currentframe().f_code.co_name, f"📏 GeometrySnitch: SETTLED. Publishing for {self.tab_name} ({w}x{h})", level="DEBUG")
        self._publish_geometry(w, h, x, y)

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
            self.geometry_topic, orjson.dumps(payload).decode()
        )
