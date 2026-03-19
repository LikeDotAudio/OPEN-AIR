import tkinter as tk
import math
from oaGuiElements.Core.metering.meter_needle.constants import (
    NUMBER_FONT_FAMILY, NUMBER_FONT_SIZE
)

class NumberDrawer:
    @staticmethod
    def draw_labels(canvas, center_x, center_y, tick_values,
                    min_val, max_val, start_angle_deg, end_angle_deg, extent_deg,
                    main_arc_radius, text_offset_from_arc,
                    fg_color, scale_numbers, label_overrides, counter_clockwise, label_radius=None):
        
        if not scale_numbers:
            return

        for i, tick_val in enumerate(tick_values):
            range_val = max_val - min_val
            percentage = (tick_val - min_val) / range_val if range_val != 0 else 0
            
            if counter_clockwise:
                current_angle_deg = end_angle_deg + (percentage * extent_deg)
            else:
                current_angle_deg = start_angle_deg - (percentage * extent_deg)
                
            current_angle_rad = math.radians(current_angle_deg)
            
            if label_radius is not None:
                text_radius_pos = label_radius
            else:
                text_radius_pos = main_arc_radius + text_offset_from_arc
            
            tx = center_x + text_radius_pos * math.cos(current_angle_rad)
            ty = center_y - text_radius_pos * math.sin(current_angle_rad)
            
            # Check for label overrides
            label_text = str(int(tick_val))
            if label_overrides:
                if str(tick_val) in label_overrides:
                    label_text = label_overrides[str(tick_val)]
                elif str(int(tick_val)) in label_overrides:
                    label_text = label_overrides[str(int(tick_val))]
            
            canvas.create_text(
                tx, ty, text=label_text, fill=fg_color, font=(NUMBER_FONT_FAMILY, NUMBER_FONT_SIZE), tags="vu_element"
            )
