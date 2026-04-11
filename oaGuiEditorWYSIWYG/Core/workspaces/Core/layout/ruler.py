# Core/layout/ruler.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Horizontal and Vertical rulers for the WYSIWYG editor.

import tkinter as tk

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

    def set_center(self, val):
        """Sets the center point value to mark on the ruler."""
        self.center_val = val
        self.redraw()
        
    def redraw(self):
        """Redraws the ruler markings."""
        try:
            self.delete("all")
            w = int(self.winfo_width())
            h = int(self.winfo_height())
            
            if self.orient == "horizontal":
                self.create_line(0, h-1, w, h-1, fill="#555555")
                start = int(-(self.offset % self.grid_size))
                step = int(self.grid_size // 10)
                if step < 1: step = 1
                
                for x in range(start, w, step):
                    val = int(x + self.offset)
                    if val % self.grid_size == 0:
                        self.create_line(x, h-10, x, h, fill="#888888")
                        self.create_text(x + 2, 2, text=str(val), anchor="nw", fill="#888888", font=("Arial", 6))
                    elif val % (self.grid_size // 2) == 0:
                        self.create_line(x, h-6, x, h, fill="#555555")
                    else:
                        self.create_line(x, h-3, x, h, fill="#333333")
                
                # Center Marker
                if self.center_val is not None:
                    cx = int(self.center_val - self.offset)
                    if 0 <= cx <= w:
                        self.create_polygon(cx-5, 0, cx+5, 0, cx, 8, fill="#FF00FF", tags="center_marker")
                        self.create_line(cx, 8, cx, h, fill="#FF00FF", width=1, dash=(2, 2))
            else:
                self.create_line(w-1, 0, w-1, h, fill="#555555")
                start = int(-(self.offset % self.grid_size))
                step = int(self.grid_size // 10)
                if step < 1: step = 1
                
                for y in range(start, h, step):
                    val = int(y + self.offset)
                    if val % self.grid_size == 0:
                        self.create_line(w-10, y, w, y, fill="#888888")
                        self.create_text(2, y + 2, text=str(val), anchor="nw", fill="#888888", font=("Arial", 6))
                    elif val % (self.grid_size // 2) == 0:
                        self.create_line(w-6, y, w, y, fill="#555555")
                    else:
                        self.create_line(w-3, y, w, y, fill="#333333")

                # Center Marker
                if self.center_val is not None:
                    cy = int(self.center_val - self.offset)
                    if 0 <= cy <= h:
                        self.create_polygon(0, cy-5, 0, cy+5, 8, cy, fill="#FF00FF", tags="center_marker")
                        self.create_line(8, cy, w, cy, fill="#FF00FF", width=1, dash=(2, 2))
        except Exception as e:
            from oaLogging.Methods.matrix_gate import matrix_log
            matrix_log("ui", "wysiwyg", "redraw", f"Ruler redraw failed: {e}", "ERROR")
