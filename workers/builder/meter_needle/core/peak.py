import tkinter as tk
import math

class PeakDrawer:
    @staticmethod
    def draw_peak_dot(canvas, center_x, center_y, transition_angle_deg,
                      main_arc_radius, arc_thickness, peak_on, peak_flag, arc_radius=None):
        if peak_flag:
            radius_to_use = arc_radius if arc_radius is not None else main_arc_radius
            trad = math.radians(transition_angle_deg)
            dot_radius = radius_to_use - arc_thickness - 10
            dx = center_x + dot_radius * math.cos(trad)
            dy = center_y - dot_radius * math.sin(trad)
            dot_color = "red" if peak_on else "#444444"
            canvas.create_oval(dx-4, dy-4, dx+4, dy+4, fill=dot_color, outline="black", tags=("vu_element", "peak_dot"))
