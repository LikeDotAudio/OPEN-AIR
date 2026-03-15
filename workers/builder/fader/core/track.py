# workers/builder/fader/core/track.py

import tkinter as tk

class TrackDrawer:
    @staticmethod
    def draw(canvas, frame, cx, padding, height, slot_w, hover_color=None):
        """Draws the 3D recessed track slot for the vertical fader."""
        
        base_fill = "#050505"
        fill_col = hover_color if hover_color else base_fill

        # Main slot (Deep Shadow)
        canvas.create_rectangle(cx - slot_w/2, padding - 5, cx + slot_w/2, height - padding + 5, 
                                fill=fill_col, outline="#222", width=1, tags=("static", "track_slot"))
        
        # Inner Shadow (left and top edge of slot)
        canvas.create_line(cx - slot_w/2 + 1, padding - 4, cx - slot_w/2 + 1, height - padding + 4, 
                           fill="#000", tags="static")
        canvas.create_line(cx - slot_w/2 + 1, padding - 4, cx + slot_w/2 - 1, padding - 4, 
                           fill="#000", tags="static")
        
        # Highlight (right and bottom edge of slot)
        canvas.create_line(cx + slot_w/2, padding - 5, cx + slot_w/2, height - padding + 5, 
                           fill="#333", tags="static")
        canvas.create_line(cx - slot_w/2, height - padding + 5, cx + slot_w/2, height - padding + 5, 
                           fill="#333", tags="static")
