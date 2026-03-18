import tkinter as tk
from tkinter import ttk
import time
import math
import orjson
from loguru import logger
from oaComMQTT.mqtt_publisher_service import publish_payload
from oaComMQTT.mqtt_topic_utils import get_topic

class HorizontalMeterRenderer(ttk.Frame):
    """A Tkinter widget that displays a numerical value with horizontal progress bars."""

    def __init__(self, parent, config, base_mqtt_topic, widget_id, **kwargs):
        self.subscriber_router = kwargs.pop("subscriber_router", None)
        self.state_mirror_engine = kwargs.pop("state_mirror_engine", None)
        super().__init__(parent, **kwargs)
        
        self.widget_config, self.base_mqtt_topic, self.widget_id = config, base_mqtt_topic, widget_id
        self.GUID = self.state_mirror_engine.GUID if self.state_mirror_engine and hasattr(self.state_mirror_engine, "GUID") else "UNKNOWN_GUID"

        self.max_integer_value = config.get("max_integer_value", 100)
        self.meter_value_var = tk.DoubleVar(value=config.get("value_default", 0.0))

        self._build_ui(config.get("title", "Meter"))
        self._bind_state()

    def _build_ui(self, title_text):
        self.header_frame = ttk.Frame(self); self.header_frame.pack(side=tk.TOP, fill=tk.X)
        ttk.Label(self.header_frame, text=title_text, anchor="w").pack(side=tk.LEFT, padx=2)
        self.label_value = ttk.Label(self.header_frame, text="Value: --", anchor="e")
        self.label_value.pack(side=tk.RIGHT, padx=2)

        self.int_frame = ttk.Frame(self); self.int_frame.pack(side=tk.TOP, fill=tk.X, pady=(5, 0))
        self.bar_graph_value1 = ttk.Progressbar(self.int_frame, orient="horizontal", length=200, mode="determinate")
        self.bar_graph_value1.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        self.bar_graph_value1["maximum"] = self.max_integer_value
        self.label1 = ttk.Label(self.int_frame, text="Int: --", width=8, anchor="w")
        self.label1.pack(side=tk.RIGHT, padx=2)

        self.dec_frame = ttk.Frame(self); self.dec_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 5))
        self.bar_graph_value_dec = ttk.Progressbar(self.dec_frame, orient="horizontal", length=200, mode="determinate")
        self.bar_graph_value_dec.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        self.bar_graph_value_dec["maximum"] = 100
        self.label_dec = ttk.Label(self.dec_frame, text="Dec: --", width=8, anchor="w")
        self.label_dec.pack(side=tk.RIGHT, padx=2)

    def _bind_state(self):
        self.meter_value_var.trace_add("write", self._on_value_change)
        self._on_value_change()
        if self.state_mirror_engine:
            self.state_mirror_engine.register_widget(self.widget_id, self.meter_value_var, self.base_mqtt_topic, self.widget_config)
            self.state_mirror_engine.initialize_widget_state(self.widget_id)

    def _on_value_change(self, *args):
        val = self.meter_value_var.get()
        self.label_value.config(text=f"Value: {val:.3f}", foreground="red" if val < 0 else "black")
        
        trunc_val = math.trunc(val)
        dec_part = abs(val - trunc_val) * 100
        
        self.bar_graph_value1["value"] = min(abs(trunc_val), self.max_integer_value)
        self.label1.config(text=f"Int: {trunc_val}")
        
        self.bar_graph_value_dec["value"] = dec_part
        self.label_dec.config(text=f"Dec: {int(dec_part)}")

        try:
            if self.state_mirror_engine and not getattr(self.state_mirror_engine, '_silent_update', False):
                topic = get_topic(self.state_mirror_engine.base_topic, self.base_mqtt_topic, self.widget_id)
                payload = {"val": val, "ts": time.time(), "GUID": self.GUID, "src": "HorizontalMeter"}
                publish_payload(topic, orjson.dumps(payload).decode(), retain=True)
        except Exception as e: logger.debug(f"❌ Publishing error: {e}")
