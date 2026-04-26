# Core/vertical_meter_renderer.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import inspect
import re
import time
import tkinter as tk
from tkinter import ttk

import orjson

from oaComProtocols.oaComMQTT.Core.mqtt_publisher_service import publish_payload
from oaComProtocols.oaComMQTT.Methods.mqtt_topic_utils import get_topic
from oaLogging.Methods.matrix_gate import matrix_log


class VerticalMeterRenderer(ttk.Frame):
    """A Tkinter widget to simulate a multi-channel vertical meter display."""

    def __init__(self, parent, config, base_mqtt_topic, widget_id, **kwargs):
        self.subscriber_router = kwargs.pop("subscriber_router", None)
        self.state_mirror_engine = kwargs.pop("state_mirror_engine", None)
        super().__init__(parent, **kwargs)

        self.widget_config, self.base_mqtt_topic, self.widget_id = config, base_mqtt_topic, widget_id
        self.GUID = self.state_mirror_engine.GUID if self.state_mirror_engine and hasattr(self.state_mirror_engine, "GUID") else "UNKNOWN_GUID"

        self.channel_labels = []
        num_channels = config.get("num_channels", 4)

        self.meter_values_var = tk.StringVar(value=orjson.dumps([config.get("value_default", 0.0)] * num_channels).decode())

        for i in range(num_channels):
            label = ttk.Label(self, text=f"Ch {i+1}: --", anchor="w")
            label.pack(side=tk.TOP, fill=tk.X, pady=1)
            self.channel_labels.append(label)

        self._bind_state()

    def _bind_state(self):
        self.meter_values_var.trace_add("write", self._on_value_change)
        self._on_value_change()
        if self.state_mirror_engine:
            self.state_mirror_engine.register_widget(self.widget_id, self.meter_values_var, self.base_mqtt_topic, self.widget_config)
            self.state_mirror_engine.initialize_widget_state(self.widget_id)

    def _on_value_change(self, *args):
        val_str = self.meter_values_var.get()
        try:
            num_strs = re.findall(r"-?\d*\.?\d+", val_str)
            vals = []
            for n in num_strs:
                try: vals.append(float(n))
                except: continue

            for i, v in enumerate(vals):
                if i < len(self.channel_labels): self.channel_labels[i].config(text=f"Ch {i+1}: {float(v):.2f}")

            if self.state_mirror_engine and not getattr(self.state_mirror_engine, '_silent_update', False):
                topic = get_topic(self.state_mirror_engine.base_topic, self.base_mqtt_topic, self.widget_id)
                payload = {"value": vals, "timestamp": time.time(), "GUID": self.GUID, "src": "VerticalMeter"}
                publish_payload(topic, orjson.dumps(payload).decode(), retain=True)
        except Exception as e: matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"❌ Error processing array: {e}", level="DEBUG")
