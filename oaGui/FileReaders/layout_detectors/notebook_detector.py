# oaGui/FileReaders/layout_detectors/notebook_detector.py
# Author: Anthony Peter Kuzub
# Version: 20260502.1000.1
#
# Description: Detector for tabbed notebook GUI layouts.

from .base_detector import BaseLayoutDetector


class NotebookDetector(BaseLayoutDetector):
    """Detects notebook layouts (directories starting with a digit)."""

    def detect(self, path, sub_dirs, gui_files):
        potential_tabs = [d for d in sub_dirs if d.name and d.name[0].isdigit()]
        valid_tabs = [d for d in potential_tabs if self.interpreter._scan_for_gui_files(d)]
        if not valid_tabs: return None

        sorted_tabs = sorted(valid_tabs, key=lambda d: int(d.name.split("_")[0]))
        tabs = []
        for d in sorted_tabs:
            parts = d.name.split("_")
            name = " ".join(parts[1:]).title() if len(parts) > 1 else d.name
            tabs.append({"path": d, "display_name": name})
        return {"type": "notebook", "data": {"tabs": tabs}}
