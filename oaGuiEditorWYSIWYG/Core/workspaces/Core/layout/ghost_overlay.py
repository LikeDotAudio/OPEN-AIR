# Core/layout/ghost_overlay.py
# Author: Gemini (Collaborator)
# Version: 20260416.0010.1
#
# Description: High-speed transparent interaction layer for designer feedback.

import tkinter as tk
from oaLogging.Methods.matrix_gate import matrix_log

class GhostOverlay(tk.Canvas):
    """
    Transparent overlay for drawing ghosts, handles, and snapping guides.
    Decouples visual Designer feedback from live GUI component logic.
    """
    def __init__(self, parent, **kwargs):
        # ⚡ PERFORMANCE: Use borderless, highlight-free canvas
        super().__init__(parent, highlightthickness=0, bd=0, **kwargs)
        self.active_ghost = None
        self.handles = []
        self.guides = []
        
    def draw_ghost(self, x, y, width, height):
        """Draws a semi-transparent dashed outline of the target area."""
        self.delete("ghost")
        self.active_ghost = self.create_rectangle(
            x, y, x + width, y + height,
            outline="#007acc", width=2, dash=(4, 4), tags="ghost"
        )
        self.tag_raise("ghost")

    def draw_handles(self, x, y, width, height):
        """Draws 8 standard resizing handles around the ghost."""
        self.delete("handle")
        hs = 3 # Handle half-size
        coords = [
            (x, y), (x+width//2, y), (x+width, y),
            (x, y+height//2), (x+width, y+height//2),
            (x, y+height), (x+width//2, y+height), (x+width, y+height)
        ]
        for cx, cy in coords:
            self.create_rectangle(
                cx-hs, cy-hs, cx+hs, cy+hs,
                fill="white", outline="#007acc", tags="handle"
            )
        self.tag_raise("handle")

    def draw_snap_guide(self, orientation, pos, color="#ff00ff"):
        """Draws a temporary magenta alignment line (PowerPoint style)."""
        if orientation == "v":
            self.create_line(pos, 0, pos, 5000, fill=color, width=1, dash=(2, 2), tags="guide")
        else:
            self.create_line(0, pos, 5000, pos, fill=color, width=1, dash=(2, 2), tags="guide")

    def clear(self):
        """Clears all temporary design feedback elements."""
        self.delete("ghost")
        self.delete("handle")
        self.delete("guide")
        self.active_ghost = None
