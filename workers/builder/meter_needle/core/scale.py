import tkinter as tk
import math
from workers.builder.meter_needle.constants import (
    SCALE_DEFAULT_STEPS, SCALE_SUB_TICK_DOT_RADIUS, 
    SCALE_SUB_TICK_WIDTH, SCALE_MAIN_TICK_WIDTH
)

class ScaleDrawer:
    @staticmethod
    def draw_ticks(canvas, center_x, center_y, min_val, max_val, 
                   start_angle_deg, end_angle_deg, extent_deg,
                   main_arc_radius, arc_thickness, tick_length, sub_tick_length,
                   fg_color, ticks_visible, custom_ticks, tick_step, anchor_point,
                   sub_ticks, sub_tick_style, counter_clockwise, tick_radius=None):
        
        if tick_radius is not None:
             tick_start_radius = tick_radius
        else:
             tick_start_radius = main_arc_radius - (arc_thickness / 2)
        
        if custom_ticks:
            tick_values = custom_ticks
        elif tick_step is not None:
            # Generate based on step and anchor
            start = anchor_point if anchor_point is not None else min_val
            generated_ticks = {start}
            
            # Go down from anchor
            curr = start - tick_step
            while curr >= min_val:
                generated_ticks.add(curr)
                curr -= tick_step
            
            # Go up from anchor
            curr = start + tick_step
            while curr <= max_val:
                generated_ticks.add(curr)
                curr += tick_step
                
            tick_values = sorted(list(generated_ticks))
        else:
            steps = SCALE_DEFAULT_STEPS
            tick_values = [min_val + (i / (steps - 1.0) * (max_val - min_val)) for i in range(steps)]

        for i, tick_val in enumerate(tick_values):
            # Calculate normalized position (0.0 to 1.0)
            range_val = max_val - min_val
            percentage = (tick_val - min_val) / range_val if range_val != 0 else 0
            
            # Map to angle
            if counter_clockwise:
                current_angle_deg = end_angle_deg + (percentage * extent_deg)
            else:
                current_angle_deg = start_angle_deg - (percentage * extent_deg)
                
            current_angle_rad = math.radians(current_angle_deg)

            # Draw Main Tick
            if ticks_visible:
                x_tick_start = center_x + tick_start_radius * math.cos(current_angle_rad)
                y_tick_start = center_y - tick_start_radius * math.sin(current_angle_rad)
                x_tick_end = center_x + (tick_start_radius - tick_length) * math.cos(current_angle_rad)
                y_tick_end = center_y - (tick_start_radius - tick_length) * math.sin(current_angle_rad)
                # ⚡ OPTIMIZATION: Use 'tick' tag for batch updates
                canvas.create_line(x_tick_start, y_tick_start, x_tick_end, y_tick_end, fill=fg_color, width=SCALE_MAIN_TICK_WIDTH, tags=("vu_element", "tick"))

            # Draw Sub-Ticks (between this tick and next)
            if sub_ticks > 0 and i < len(tick_values) - 1:
                next_val = tick_values[i+1]
                for j in range(1, sub_ticks + 1):
                    sub_val = tick_val + (j * (next_val - tick_val) / (sub_ticks + 1))
                    sub_perc = (sub_val - min_val) / range_val if range_val != 0 else 0
                    
                    if counter_clockwise:
                        sub_angle_deg = end_angle_deg + (sub_perc * extent_deg)
                    else:
                        sub_angle_deg = start_angle_deg - (sub_perc * extent_deg)
                    
                    sub_angle_rad = math.radians(sub_angle_deg)
                    
                    sx_tick_start = center_x + tick_start_radius * math.cos(sub_angle_rad)
                    sy_tick_start = center_y - tick_start_radius * math.sin(sub_angle_rad)
                    
                    if sub_tick_style == "dot":
                        # Draw a small dot at the start position
                        dot_r = SCALE_SUB_TICK_DOT_RADIUS
                        # ⚡ OPTIMIZATION: Use 'tick' tag for batch updates
                        canvas.create_oval(
                            sx_tick_start - dot_r, sy_tick_start - dot_r,
                            sx_tick_start + dot_r, sy_tick_start + dot_r,
                            fill=fg_color, outline=fg_color, tags=("vu_element", "tick")
                        )
                    else:
                        # Standard Line
                        sx_tick_end = center_x + (tick_start_radius - sub_tick_length) * math.cos(sub_angle_rad)
                        sy_tick_end = center_y - (tick_start_radius - sub_tick_length) * math.sin(sub_angle_rad)
                        # ⚡ OPTIMIZATION: Use 'tick' tag for batch updates
                        canvas.create_line(sx_tick_start, sy_tick_start, sx_tick_end, sy_tick_end, fill=fg_color, width=SCALE_SUB_TICK_WIDTH, tags=("vu_element", "tick"))
        
        return tick_values

    @staticmethod
    def draw_arcs(canvas, center_x, center_y, min_val, max_val,
                  start_angle_deg, end_angle_deg, extent_deg,
                  main_arc_radius, arc_thickness,
                  lower_colour, middle_colour, upper_colour,
                  mid_range_start, red_zone_start,
                  counter_clockwise, arc_radius=None):
        
        # Use provided arc_radius override if available
        radius_to_use = arc_radius if arc_radius is not None else main_arc_radius

        range_val = max_val - min_val
        if range_val == 0: range_val = 1.0
        
        # Normalize boundaries
        mid_start_norm = (mid_range_start - min_val) / range_val
        red_start_norm = (red_zone_start - min_val) / range_val
        
        # Clamp norms
        mid_start_norm = max(0.0, min(1.0, mid_start_norm))
        red_start_norm = max(0.0, min(1.0, red_start_norm))
        
        # Ensure mid_start <= red_start for logic simplicity
        if mid_start_norm > red_start_norm:
            mid_start_norm = red_start_norm

        transition_angle_deg = 0

        if counter_clockwise:
            a_mid = end_angle_deg + (mid_start_norm * extent_deg)
            a_red = end_angle_deg + (red_start_norm * extent_deg)
            
            # Lower Arc
            canvas.create_arc(
                center_x - radius_to_use, center_y - radius_to_use,
                center_x + radius_to_use, center_y + radius_to_use,
                start=end_angle_deg, extent=(a_mid - end_angle_deg),
                style=tk.ARC, outline=lower_colour, width=arc_thickness, tags=("vu_element", "arc")
            )
            # Middle Arc
            canvas.create_arc(
                center_x - radius_to_use, center_y - radius_to_use,
                center_x + radius_to_use, center_y + radius_to_use,
                start=a_mid, extent=(a_red - a_mid),
                style=tk.ARC, outline=middle_colour, width=arc_thickness, tags=("vu_element", "arc")
            )
            # Upper Arc
            canvas.create_arc(
                center_x - radius_to_use, center_y - radius_to_use,
                center_x + radius_to_use, center_y + radius_to_use,
                start=a_red, extent=(start_angle_deg - a_red),
                style=tk.ARC, outline=upper_colour, width=arc_thickness, tags=("vu_element", "arc")
            )
            
            transition_angle_deg = a_red
        else:
            a_mid = start_angle_deg - (mid_start_norm * extent_deg)
            a_red = start_angle_deg - (red_start_norm * extent_deg)
            
            # Lower Arc
            canvas.create_arc(
                center_x - radius_to_use, center_y - radius_to_use,
                center_x + radius_to_use, center_y + radius_to_use,
                start=a_mid, extent=(start_angle_deg - a_mid),
                style=tk.ARC, outline=lower_colour, width=arc_thickness, tags=("vu_element", "arc")
            )
            # Middle Arc
            canvas.create_arc(
                center_x - radius_to_use, center_y - radius_to_use,
                center_x + radius_to_use, center_y + radius_to_use,
                start=a_red, extent=(a_mid - a_red),
                style=tk.ARC, outline=middle_colour, width=arc_thickness, tags=("vu_element", "arc")
            )
            # Upper Arc
            canvas.create_arc(
                center_x - radius_to_use, center_y - radius_to_use,
                center_x + radius_to_use, center_y + radius_to_use,
                start=end_angle_deg, extent=(a_red - end_angle_deg),
                style=tk.ARC, outline=upper_colour, width=arc_thickness, tags=("vu_element", "arc")
            )
            
            transition_angle_deg = a_red
            
        return transition_angle_deg
