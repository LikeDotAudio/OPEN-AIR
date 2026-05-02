# Methods/ui_coordinate_utils.py
# Author: Anthony Peter Kuzub
# Version: 20260501.1000.1
#
# Description: Utility methods for calculating relative widget coordinates.

class UICoordinateUtils:
    """Utility methods for calculating relative widget coordinates."""
    @staticmethod
    def get_relative_coords(widget, ref_widget, cache=None):
        """
        Calculates coordinates of widget relative to ref_widget.
        Caches results to prevent redundant lookups if a cache dict is provided.
        """
        wid = widget._w
        if cache is not None and wid in cache:
            return cache[wid]

        relative_x, relative_y = 0, 0
        current_widget = widget
        ref_path = ref_widget._w if ref_widget else ""

        while current_widget:
            curr_path = current_widget._w
            if curr_path == ref_path:
                break
            relative_x += current_widget.winfo_x()
            relative_y += current_widget.winfo_y()

            parent_path = current_widget.winfo_parent()
            if not parent_path: break
            current_widget = current_widget.nametowidget(parent_path)

        if cache is not None and widget.winfo_ismapped():
            cache[wid] = (relative_x, relative_y)

        return relative_x, relative_y
