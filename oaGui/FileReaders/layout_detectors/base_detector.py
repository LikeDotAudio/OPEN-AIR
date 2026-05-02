# oaGui/FileReaders/layout_detectors/base_detector.py
# Author: Anthony Peter Kuzub
# Version: 20260502.1000.1
#
# Description: Base class for GUI layout detectors.

import pathlib

class BaseLayoutDetector:
    """Base class for specialized GUI layout detectors."""
    
    def __init__(self, interpreter):
        self.interpreter = interpreter

    def detect(self, path: pathlib.Path, sub_dirs: list, gui_files: list) -> dict:
        """Must be implemented by subclasses to detect a specific layout type."""
        raise NotImplementedError("Subclasses must implement detect()")
