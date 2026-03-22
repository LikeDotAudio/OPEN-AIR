# Core/pivot.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import tkinter as tk

class PivotDrawer:
    @staticmethod
    def draw_pivot(canvas, center_x, center_y, pivot_size, pivot_colour, secondary_color, fg_color):
        pivot_radius = pivot_size / 2.0
        canvas.create_oval(
            center_x - pivot_radius,
            center_y - pivot_radius,
            center_x + pivot_radius,
            center_y + pivot_radius,
            fill=pivot_colour or fg_color,
            outline=secondary_color,
            tags="vu_element"
        )
