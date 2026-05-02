# oaGui/Interface/Canvas_Viewport_Manager.py
# Author: Anthony Peter Kuzub
# Version: 20260502.1000.1
#
# Description: Manages the physical viewport of the Tkinter Canvas.
# Handles scaling, scroll region synchronization, and filling the canvas with the inner build frame.

import tkinter as tk
from oaLogging.Methods.matrix_gate import matrix_log

class CanvasViewportManager:
    """
    Orchestrates the sizing and filling behavior of the GUI's primary Canvas.
    """

    def __init__(self, parent: tk.Widget, bg: str, allow_horizontal_scroll: bool = True):
        """
        Initializes the canvas and inner scroll frame.
        """
        self.allow_horizontal_scroll = allow_horizontal_scroll
        
        # 1. Primary Drawing Surface
        self.canvas = tk.Canvas(parent, background=bg, bd=0, highlightthickness=0)
        
        # 2. Inner Content Container
        self.scroll_frame = tk.Frame(self.canvas, bd=0, highlightthickness=0, bg=bg)
        
        # 3. Viewport Window Item
        self.window_id = self.canvas.create_window(
            (0, 0), window=self.scroll_frame, anchor="nw"
        )

        # 4. Bindings
        self.scroll_frame.bind("<Configure>", self._on_content_configure, add="+")

    def _on_content_configure(self, event=None):
        """Updates the scroll region whenever the content size changes."""
        try:
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        except tk.TclError:
            pass

    def synchronize_to_viewport(self, viewport_w: int, viewport_h: int):
        """
        Calculates and applies the target dimensions for the content frame to ensure it fills
        the viewport or scrolls correctly.
        """
        if not self.canvas.winfo_exists():
            return None

        # Determine requested content size
        req_w = self.scroll_frame.winfo_reqwidth()
        req_h = self.scroll_frame.winfo_reqheight()

        # logic: fill viewport width if not scrolling horizontally, else max(viewport, content)
        new_w = viewport_w if not self.allow_horizontal_scroll else max(viewport_w, req_w)
        new_h = max(viewport_h, req_h)

        matrix_log("gui", "gui_render", "synchronize_to_viewport", 
                   f"📏 [VIEWPORT] Sync -> View: {viewport_w}x{viewport_h} | "
                   f"Content Req: {req_w}x{req_h} | Target: {new_w}x{new_h}", "TRACE")

        try:
            self.canvas.itemconfig(self.window_id, width=int(new_w), height=int(new_h))
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            return {
                "viewport": (viewport_w, viewport_h),
                "content": (req_w, req_h),
                "target": (new_w, new_h)
            }
        except tk.TclError:
            return None

    def pack(self, **kwargs):
        """Packs the managed canvas."""
        self.canvas.pack(**kwargs)

    def grid(self, **kwargs):
        """Grids the managed canvas."""
        self.canvas.grid(**kwargs)

    def reset_view(self):
        """Snaps the viewport back to (0,0)."""
        self.canvas.xview_moveto(0)
        self.canvas.yview_moveto(0)

    def destroy(self):
        """Cleans up widgets."""
        if self.canvas.winfo_exists():
            self.canvas.destroy()
