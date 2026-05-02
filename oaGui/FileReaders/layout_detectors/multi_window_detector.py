# oaGui/FileReaders/layout_detectors/multi_window_detector.py
# Author: Anthony Peter Kuzub
# Version: 20260502.1000.1
#
# Description: Detector for multi-window GUI layouts.

import pathlib
from .base_detector import BaseLayoutDetector

class MultiWindowDetector(BaseLayoutDetector):
    """Detects multi-window layouts (directories starting with 'window_')."""

    def detect(self, path, sub_dirs, gui_files):
        window_dirs = [d for d in sub_dirs if d.name.lower().startswith("window_")]
        if window_dirs:
            return {
                "type": "multi_window", 
                "data": {
                    "windows": [{"path": d, "title": d.name.replace("_", " ")} for d in sorted(window_dirs)]
                }
            }
        return None
