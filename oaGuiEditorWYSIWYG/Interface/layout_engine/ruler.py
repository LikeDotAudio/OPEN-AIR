# Core/layout/ruler.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Horizontal and Vertical rulers for the WYSIWYG editor.

import tkinter as tk

from oaLogging.Methods.matrix_gate import matrix_log


class Ruler(tk.Canvas):
    """A ruler widget that displays measurements in pixels."""
    def __init__(self, parent, orient="horizontal", **kwargs):
        self.orient = orient
        kwargs.setdefault("bg", "#1a1a1a")
        kwargs.setdefault("highlightthickness", 0)
        kwargs.setdefault("bd", 0)

        if self.orient == "horizontal":
            kwargs.setdefault("height", 20)
        else:
            kwargs.setdefault("width", 20)

        super().__init__(parent, **kwargs)
        self.offset = 0
        self.scale = 1.0
        self.grid_size = 100
        self.center_val = None
        self.bind("<Configure>", lambda e: self.redraw())

    def set_offset(self, offset):
        """Sets the scroll offset of the ruler."""
        self.offset = offset
        self.redraw()

    def set_center(self, value):
        """Sets the center point value to mark on the ruler."""
        self.center_val = value
        self.redraw()

    def redraw(self):
        """Redraws the ruler markings based on the current orientation."""
        try:
            self.delete("all")
            width, height = int(self.winfo_width()), int(self.winfo_height())

            if self.orient == "horizontal":
                self._draw_horizontal(width, height)
            else:
                self._draw_vertical(width, height)
        except Exception as e:
            matrix_log("ui", "wysiwyg", "redraw", f"Ruler redraw failed: {e}", "ERROR")

    def _draw_horizontal(self, w, h):
        """Draws the horizontal scale, markings, and center guide."""
        self.create_line(0, h-1, w, h-1, fill="#555555")
        start = int(-(self.offset % self.grid_size))
        step = max(1, int(self.grid_size // 10))

        for x in range(start, w, step):
            value = int(x + self.offset)
            self._draw_horizontal_tick(x, value, h)

        if self.center_val is not None:
            self._draw_horizontal_center(w, h)

    def _draw_horizontal_tick(self, x, value, h):
        """Draws a single horizontal tick mark and text if applicable."""
        if value % self.grid_size == 0:
            self.create_line(x, h-10, x, h, fill="#888888")
            self.create_text(x + 2, 2, text=str(value), anchor="nw", fill="#888888", font=("Arial", 6))
        elif value % (self.grid_size // 2) == 0:
            self.create_line(x, h-6, x, h, fill="#555555")
        else:
            self.create_line(x, h-3, x, h, fill="#333333")

    def _draw_horizontal_center(self, w, h):
        """Draws the magenta center marker for horizontal rulers."""
        cx = int(self.center_val - self.offset)
        if 0 <= cx <= w:
            self.create_polygon(cx-5, 0, cx+5, 0, cx, 8, fill="#FF00FF", tags="center_marker")
            self.create_line(cx, 8, cx, h, fill="#FF00FF", width=1, dash=(2, 2))

    def _draw_vertical(self, w, h):
        """Draws the vertical scale, markings, and center guide."""
        self.create_line(w-1, 0, w-1, h, fill="#555555")
        start = int(-(self.offset % self.grid_size))
        step = max(1, int(self.grid_size // 10))

        for y in range(start, h, step):
            value = int(y + self.offset)
            self._draw_vertical_tick(y, value, w)

        if self.center_val is not None:
            self._draw_vertical_center(w, h)

    def _draw_vertical_tick(self, y, value, w):
        """Draws a single vertical tick mark and text if applicable."""
        if value % self.grid_size == 0:
            self.create_line(w-10, y, w, y, fill="#888888")
            self.create_text(2, y + 2, text=str(value), anchor="nw", fill="#888888", font=("Arial", 6))
        elif value % (self.grid_size // 2) == 0:
            self.create_line(w-6, y, w, y, fill="#555555")
        else:
            self.create_line(w-3, y, w, y, fill="#333333")

    def _draw_vertical_center(self, w, h):
        """Draws the magenta center marker for vertical rulers."""
        cy = int(self.center_val - self.offset)
        if 0 <= cy <= h:
            self.create_polygon(0, cy-5, 0, cy+5, 8, cy, fill="#FF00FF", tags="center_marker")
            self.create_line(8, cy, w, cy, fill="#FF00FF", width=1, dash=(2, 2))
