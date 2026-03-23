# Core/ptp_meter_panel.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import tkinter as tk
import datetime
from loguru import logger

class PTPMeterPanel:
    """Manages the cluster of 6 analog-style time analysis meters."""

    def __init__(self, parent, builder):
        self.parent, self.builder = parent, builder
        self.meters = {}
        self._setup()

    def _setup(self):
        configs = [("Month", 1, 12, "MONTH"), ("Day", 1, 31, "DAY"), ("Hour", 1, 24, "HOUR"),
                   ("Minute", 0, 59, "MIN"), ("Second", 0, 59, "SEC"), ("Millisecond", 0, 999, "MS")]
        self.stack = tk.Frame(self.parent, bg=self.parent.cget("bg")); self.stack.pack(expand=True)
        for label, v_min, v_max, short in configs:
            cfg = {
                "type": "_NeedleVUMeter", "label": label, "geometry": {"width": 140, "height": 140},
                "domain": {"primary": {"min": float(v_min), "max": float(v_max), "value_default": float(v_min)}},
                "cosmetics": {"colors": {"foreground": "#000000", "bezel": "#000000", "scale_label": "#000000"},
                              "style_overrides": {"bezel_shape": "squircle", "bezel_width": 4, "overlay_style": "aperture_mask", "Pointer_Style": "knife-edge", "sub_ticks": 2 if v_max < 100 else 4, "tick_length": 5, "label_radius_offset": 5},
                              "labels": [{"text": short, "x": 0, "y": -55, "size": 9, "font": "Arial", "weight": "bold"}, {"value_overlay": True, "x": 0, "y": -40, "size": 9, "weight": "bold", "color": "#000000", "sig_fig": 0}]}
            }
            mf = self.builder.make_meter_needle(self.stack, cfg)
            if mf: mf.pack(side=tk.LEFT, padx=2); self.meters[label] = mf

    def update(self, ts):
        if not self.meters: return
        dt = datetime.datetime.fromtimestamp(ts)
        ms = int(dt.microsecond / 1000)
        try:
            for k, v in [("Month", dt.month), ("Day", dt.day), ("Hour", dt.hour), ("Minute", dt.minute), ("Second", dt.second), ("Millisecond", ms)]:
                if k in self.meters: self.meters[k].vu_value_var.set(v)
        except Exception as e: logger.error(f"⚠️ PTP Meter Update Error: {e}")
