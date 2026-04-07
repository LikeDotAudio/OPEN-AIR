# Core/graph_state_mixin.py
from oaGui.Methods.i18n_utils import get_text
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import tkinter as tk
from oaLogging.Methods.matrix_gate import matrix_log
import inspect
from loguru import logger
from oaLogging.Core.logger import builder_logger

# --- Standard Debug Logging Setup ---

class GraphStateMixin:
    """Handles MQTT topic registration and state synchronization for datasets, markers, and settings."""

    def _initialize_marker_mirroring(self):
        path = f"{self.widget_id}/oaDataRunningFiles/MARKERS"
        self.state_mirror_engine.register_widget(path, self.marker_var, self.base_mqtt_topic_from_path, {"type": "_GraphMarkers"})
        self.marker_var.trace_add("write", self._on_marker_var_change)
        self.marker_var.trace_add("write", lambda *a: self.state_mirror_engine.broadcast_gui_change_to_mqtt(path))
        if self.subscriber_router:
            t = self.state_mirror_engine.get_widget_topic(path)
            if t: self.subscriber_router.subscribe_to_topic(t, self.state_mirror_engine.sync_incoming_mqtt_to_gui)

    def _initialize_state_mirroring(self):
        ss = ["show_grid", "xlim", "ylim", "title", "x_label", "y_label"]
        for s in ss:
            var = tk.StringVar(); self.settings_vars[s] = var
            path = f"{self.widget_id}/settings/{s}"
            self.state_mirror_engine.register_widget(path, var, self.base_mqtt_topic_from_path, {"type": "_GraphSetting"})
            var.trace_add("write", lambda *a, name=s: self._on_setting_var_change(name))
            var.trace_add("write", lambda *a, p=path: self.state_mirror_engine.broadcast_gui_change_to_mqtt(p))
            if self.subscriber_router:
                t = self.state_mirror_engine.get_widget_topic(path)
                if t: self.subscriber_router.subscribe_to_topic(t, self.state_mirror_engine.sync_incoming_mqtt_to_gui)
            self.state_mirror_engine.initialize_widget_state(path)

    def _on_dataset_var_change(self, ds_id, *args):
        csv = self.dataset_vars[ds_id].get()
        if not csv or self._last_csv_data.get(ds_id) == csv: return
        self._last_csv_data[ds_id] = csv
        try:
            x, y = [], []
            lines = csv.strip().split("\n")
            if lines and "x" in lines[0].lower(): lines = lines[1:]
            for l in lines:
                ps = l.split(",")
                if len(ps) >= 2: x.append(float(ps[0])); y.append(float(ps[1]))
            self._pending_data[ds_id] = (x, y); self._schedule_update()
        except Exception as e:
            matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"Error parsing dataset variable change: {e}", level="TRACE")

    def _on_setting_var_change(self, s):
        v = self.settings_vars[s].get()
        if not v or self._last_settings_vals.get(s) == v: return
        self._last_settings_vals[s] = v
        try:
            if s == "xlim": self.ax.set_xlim(*map(float, v.split(",")))
            elif s == "ylim": self.ax.set_ylim(*map(float, v.split(",")))
            elif s == "show_grid": self.ax.grid(v.lower() == "true")
            elif s == "title": self.ax.set_title(v)
            elif s == "x_label": self.ax.set_xlabel(v)
            elif s == "y_label": self.ax.set_ylabel(v)
            self._force_redraw = True; self._schedule_update()
        except Exception as e:
            matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"Error applying setting change '{s}': {e}", level="TRACE")