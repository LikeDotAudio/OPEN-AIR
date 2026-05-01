# telemetry/ui_tracking_service.py
# Author: Anthony Peter Kuzub
# Version: 20260222.Telemetry.1
#
# Description: Centralized Telemetry Service for UI Visibility and Geometry.

import inspect
import time

import orjson

from oaComProtocols.oaComMQTT.Core.mqtt_publisher_service import is_connected
from oaComProtocols.oaComMQTT.Methods.mqtt_topic_utils import get_topic
from oaLogging.Methods.matrix_gate import matrix_log


class UITrackingService:
    """
    Centralized service to track widget visibility and geometry.
    Handles debouncing and MQTT publishing.
    """

    def __init__(self):
        self._tracked_widgets = {} # widget -> metadata

    def track(self, widget, tab_name, state_mirror_engine, base_mqtt_topic_from_path):
        """
        Starts tracking a widget (usually a root frame/builder).
        """
        if not state_mirror_engine:
            return

        if tab_name == "InteractivePreview":
            return

        visibility_topic = get_topic(
            state_mirror_engine.base_topic,
            base_mqtt_topic_from_path,
            "visibility/visible",
        )

        geometry_topic = get_topic(
            state_mirror_engine.base_topic,
            base_mqtt_topic_from_path,
            "visibility/geometry",
        )

        metadata = {
            "tab_name": tab_name,
            "engine": state_mirror_engine,
            "vis_topic": visibility_topic,
            "geo_topic": geometry_topic,
            "geo_timer": None
        }

        self._tracked_widgets[widget] = metadata

        widget.bind("<Map>", lambda e: self._on_visible(widget, e), add="+")
        widget.bind("<Unmap>", lambda e: self._on_hidden(widget, e), add="+")
        widget.bind("<Destroy>", lambda e: self._on_destroy(widget, e), add="+")
        widget.bind("<Configure>", lambda e: self._on_geometry_change(widget, e), add="+")

        matrix_log("UI", "GUI_MANAGER", inspect.currentframe().f_code.co_name, f"📡 UITrackingService: Tracking '{tab_name}'", level="TRACE")

    def _on_visible(self, widget, event):
        meta = self._tracked_widgets.get(widget)
        if not meta: return

        # ⚡ VISIBILITY FLAG: Set local attribute for child widgets to check
        widget.is_visible = True

        matrix_log("UI", "GUI_MANAGER", inspect.currentframe().f_code.co_name, f"👁️ UITrackingService: VISIBLE for {meta['tab_name']}", level="DEBUG")
        self._publish_visibility(meta, True)
        # Force geometry update on show
        self._on_geometry_change(widget, event)

    def _on_hidden(self, widget, event):
        meta = self._tracked_widgets.get(widget)
        if not meta: return

        # ⚡ VISIBILITY FLAG: Set local attribute for child widgets to check
        widget.is_visible = False

        matrix_log("UI", "GUI_MANAGER", inspect.currentframe().f_code.co_name, f"👁️ UITrackingService: HIDDEN for {meta['tab_name']}", level="DEBUG")
        self._publish_visibility(meta, False)

    def _on_destroy(self, widget, event):
        if event.widget == widget:
            meta = self._tracked_widgets.pop(widget, None)
            if meta:
                matrix_log("UI", "GUI_MANAGER", inspect.currentframe().f_code.co_name, f"👁️ UITrackingService: DESTROYED {meta['tab_name']}", level="DEBUG")
                self._publish_visibility(meta, False)

    def _on_geometry_change(self, widget, event):
        # ⚡ EVENT GATE: Ignore resize events from children
        if event.widget != widget: return

        meta = self._tracked_widgets.get(widget)
        if not meta: return

        if meta["geo_timer"]:
            widget.after_cancel(meta["geo_timer"])

        # Debounce
        meta["geo_timer"] = widget.after(500, lambda: self._perform_geometry_publish(widget))

    def _perform_geometry_publish(self, widget):
        meta = self._tracked_widgets.get(widget)
        if not meta: return
        meta["geo_timer"] = None

        try:
            # ⚡ TELEMETRY SYNC: Report the actual widget (viewport) dimensions, not the entire window.
            # This ensures MQTT telemetry aligns with the footer display.
            w, h, x, y = widget.winfo_width(), widget.winfo_height(), widget.winfo_x(), widget.winfo_y()

            if not is_connected(): return

            payload = {
                "width": w, "height": h, "x": x, "y": y,
                "timestamp": time.time(),
                "tab_name": meta["tab_name"],
            }
            meta["engine"].publish_command(meta["geo_topic"], orjson.dumps(payload).decode())
            
            # ⚡ LOCAL SYNC: Update the footer if the widget supports it
            if hasattr(widget, '_log_telemetry_tx'):
                widget._log_telemetry_tx(f"GEO: {w}x{h}")

            # Explicitly log to GuiRender if enabled
            matrix_log("ui", "gui_telemetry", "_perform_geometry_publish", 
                       f"📡📏 [TELEMETRY] Transmitting {meta['tab_name']} geometry: {w}x{h} at {x},{y}", "DEBUG")
        except Exception:
            pass

    def _publish_visibility(self, meta, is_visible):
        if not is_connected(): return
        payload = {
            "visible": is_visible,
            "timestamp": time.time(),
            "tab_name": meta["tab_name"],
        }
        meta["engine"].publish_command(meta["vis_topic"], orjson.dumps(payload).decode())
