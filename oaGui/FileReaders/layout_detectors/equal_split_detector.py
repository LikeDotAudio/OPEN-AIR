# oaGui/FileReaders/layout_detectors/equal_split_detector.py
# Author: Anthony Peter Kuzub
# Version: 20260502.1000.1
#
# Description: Detector for equal-split GUI layouts.

import tkinter as tk

from .base_detector import BaseLayoutDetector


class EqualSplitDetector(BaseLayoutDetector):
    """Detects equal-split layouts (files starting with a digit)."""

    def detect(self, path, sub_dirs, gui_files):
        numerical_files = [f for f in gui_files if f.name and f.name[0].isdigit()]
        if len(numerical_files) <= 1: return None

        weight = 100 // len(numerical_files)
        panels = [{"path": f, "weight": weight} for f in numerical_files]
        return {
            "type": "vertical_split",
            "data": {
                "panels": panels,
                "panel_percentages": [weight] * len(panels),
                "orientation": tk.VERTICAL
            }
        }
