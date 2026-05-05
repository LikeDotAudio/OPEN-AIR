# oaGui/Core/telemetry/interaction_telemetry_service.py
# Author: Anthony Peter Kuzub
# Version: 20260222.Telemetry.1
#
# Description: Centralized Telemetry Service for UI Visibility and Geometry.

import inspect
from oaComProtocols.oaComMQTT.Methods.mqtt_topic_utils import get_topic
from oaLogging.Methods.matrix_gate import matrix_log
from oaGui.Methods.instrumentation.telemetry_publisher import TelemetryPublisher
from oaGui.Hooks.events.telemetry_hooks import TelemetryHooks

class InteractionTelemetryService:
    """
    Centralized service to track widget visibility and geometry.
    Handles debouncing and MQTT publishing.
    """

    def __init__(self):
        self._tracked_widgets = {} # widget -> metadata

    def track_interaction(self, widget, tab_name, state_mirror_engine, base_mqtt_topic_from_path):
        """
        Starts tracking a widget (usually a root frame/builder).
        """
        if not state_mirror_engine or tab_name == "InteractivePreview":
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

        TelemetryHooks.bind_tracking_events(
            widget,
            on_visible=lambda e: self._on_visible(widget, e),
            on_hidden=lambda e: self._on_hidden(widget, e),
            on_destroy=lambda e: self._on_destroy(widget, e),
            on_configure=lambda e: self._on_geometry_change(widget, e)
        )

        matrix_log("UI", "GUI_MANAGER", inspect.currentframe().f_code.co_name, f"📡 InteractionTelemetryService: Tracking '{tab_name}'", level="TRACE")

    # Legacy Alias
    def track(self, *args, **kwargs): return self.track_interaction(*args, **kwargs)

    def _on_visible(self, widget, event):
        meta = self._tracked_widgets.get(widget)
        if not meta: return

        widget.is_visible = True
        matrix_log("UI", "GUI_MANAGER", inspect.currentframe().f_code.co_name, f"👁️ InteractionTelemetryService: VISIBLE for {meta['tab_name']}", level="DEBUG")
        TelemetryPublisher.publish_visibility(meta["engine"], meta["vis_topic"], meta["tab_name"], True)
        self._on_geometry_change(widget, event)

    def _on_hidden(self, widget, event):
        meta = self._tracked_widgets.get(widget)
        if not meta: return

        widget.is_visible = False
        matrix_log("UI", "GUI_MANAGER", inspect.currentframe().f_code.co_name, f"👁️ InteractionTelemetryService: HIDDEN for {meta['tab_name']}", level="DEBUG")
        TelemetryPublisher.publish_visibility(meta["engine"], meta["vis_topic"], meta["tab_name"], False)

    def _on_destroy(self, widget, event):
        if event.widget == widget:
            meta = self._tracked_widgets.pop(widget, None)
            if meta:
                matrix_log("UI", "GUI_MANAGER", inspect.currentframe().f_code.co_name, f"👁️ InteractionTelemetryService: DESTROYED {meta['tab_name']}", level="DEBUG")
                TelemetryPublisher.publish_visibility(meta["engine"], meta["vis_topic"], meta["tab_name"], False)

    def _on_geometry_change(self, widget, event):
        if event.widget != widget: return

        meta = self._tracked_widgets.get(widget)
        if not meta: return

        if meta["geo_timer"]:
            widget.after_cancel(meta["geo_timer"])

        meta["geo_timer"] = widget.after(500, lambda: self._perform_geometry_publish(widget))

    def _perform_geometry_publish(self, widget):
        meta = self._tracked_widgets.get(widget)
        if not meta: return
        meta["geo_timer"] = None

        try:
            width, height, pos_x, pos_y = widget.winfo_width(), widget.winfo_height(), widget.winfo_x(), widget.winfo_y()
            TelemetryPublisher.publish_geometry(meta["engine"], meta["geo_topic"], meta["tab_name"], (width, height, pos_x, pos_y))
            
            if hasattr(widget, '_log_telemetry_tx'):
                widget._log_telemetry_tx(f"GEO: {width}x{height}")

            matrix_log("ui", "gui_telemetry", "_perform_geometry_publish",
                       f"📡📏 [TELEMETRY] Transmitting {meta['tab_name']} geometry: {width}x{height} at {pos_x},{pos_y}", "TRACE")
        except Exception:
            pass
