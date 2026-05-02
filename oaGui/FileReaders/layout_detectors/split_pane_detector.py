# oaGui/FileReaders/layout_detectors/split_pane_detector.py
# Author: Anthony Peter Kuzub
# Version: 20260502.1000.1
#
# Description: Detector for split-pane GUI layouts.

import tkinter as tk
from .base_detector import BaseLayoutDetector
from oaGui.Constants.schema_defaults import DEFAULT_PANEL_PERCENTAGE

class SplitPaneDetector(BaseLayoutDetector):
    """Detects split-pane layouts (directories starting with 'left_', 'right_', etc.)."""

    def detect(self, path, sub_dirs, gui_files):
        layout_dirs = [d for d in sub_dirs if d.name.split("_")[0] in ["left", "right", "top", "bottom"]]
        if not layout_dirs: return None
        
        is_h = any(d.name.startswith(("left_", "right_")) for d in layout_dirs)
        is_v = any(d.name.startswith(("top_", "bottom_")) for d in layout_dirs)
        if is_h and is_v: return {"type": "error", "data": {"error_message": "Mixed orientation split."}}

        sort_order = ["left", "right"] if is_h else ["top", "bottom"]
        sorted_dirs = sorted(layout_dirs, key=lambda d: sort_order.index(d.name.split("_")[0]))
        
        panels = []
        for d in sorted_dirs:
            try: weight = int(d.name.split("_")[1])
            except (IndexError, ValueError): weight = DEFAULT_PANEL_PERCENTAGE
            panels.append({"path": d, "weight": weight})
        
        return {
            "type": "horizontal_split" if is_h else "vertical_split",
            "data": {
                "panels": panels, 
                "panel_percentages": [p["weight"] for p in panels], 
                "orientation": tk.HORIZONTAL if is_h else tk.VERTICAL
            }
        }
