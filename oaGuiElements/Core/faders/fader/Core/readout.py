# workers/builder/fader/core/readout.py

import tkinter as tk

class ReadoutDrawer:
    @staticmethod
    def draw_floating_value(canvas, frame, cx, handle_y, value, color):
        """Draws the floating value display near the fader cap."""
        if frame.movement_value_display and frame.value_follow and frame.is_sliding:
            # Format whole numbers without decimal points
            if value == int(value):
                val_str = f"{int(value)}"
            else:
                val_str = f"{value:.1f}"
            canvas.create_text(cx, handle_y, text=val_str, fill=color, font=("Helvetica", 7, "bold"), anchor="s")

    @staticmethod
    def update_static_label(frame, value_label, value, active_color):
        """Updates the fixed value label below the fader."""
        # Format whole numbers without decimal points
        if value == int(value):
            val_text = f"{int(value)}"
        else:
            val_text = f"{value:.1f}"

        if frame.show_units and frame.unit_text:
            if frame.unit_position == "left":
                val_text = f"{frame.unit_text} {val_text}"
            else:
                val_text = f"{val_text} {frame.unit_text}"
        
        value_label.config(text=val_text, foreground=active_color)
