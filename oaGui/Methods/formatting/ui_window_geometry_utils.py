# oaGui/Methods/ui_window_geometry_utils.py
# Author: Anthony Peter Kuzub
# Version: 20260501.1000.1
#
# Description: Utility methods for calculating UI widget geometry and relative positions.

import tkinter as tk

class UIWindowGeometryUtils:
    """
    Utility methods for calculating UI widget geometry and relative positions.
    """
    @staticmethod
    def get_relative_pos(widget: tk.Widget, root: tk.Widget):
        """Calculates the relative position of a widget to a root ancestor."""
        curr = widget
        rx, ry = 0, 0
        while curr and curr != root:
            rx += curr.winfo_x()
            ry += curr.winfo_y()
            parent_path = curr.winfo_parent()
            if not parent_path: break
            curr = curr.nametowidget(parent_path)
        return rx, ry
    
    @staticmethod
    def find_parent_builder(start_builder):
        """Traverses up the widget tree to find a parent LoaderOrchestrator."""
        curr = start_builder.master
        while curr:
            if hasattr(curr, 'builder_instance') and curr.builder_instance:
                return curr.builder_instance
            if hasattr(curr, 'dynamic_gui') and curr.dynamic_gui:
                return curr.dynamic_gui
            parent_path = curr.winfo_parent()
            if not parent_path: break
            curr = curr.nametowidget(parent_path)
        return None
