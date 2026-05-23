# oaGui/Workers/layout_building/base_layout_builder.py
# Author: Anthony Peter Kuzub
# Version: 20260502.1000.1
#
# Description: Base class for GUI layout builders.

import pathlib
import tkinter as tk


class BaseLayoutBuilder:
    """Base class for specialized GUI layout builders."""

    def __init__(self, scanner):
        self.scanner = scanner

    def build(self, path: pathlib.Path, parent_widget: tk.Widget, layout_data: dict, on_complete=None):
        """Must be implemented by subclasses to build a specific layout."""
        raise NotImplementedError("Subclasses must implement build()")
