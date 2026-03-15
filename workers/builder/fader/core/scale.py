# workers/builder/fader/core/scale.py

import math
import tkinter as tk

class ScaleDrawer:
    @staticmethod
    def draw(canvas, frame, width, height, cx, available_height, padding, tick_length_half, slot_w, cap_width=40):
        """Draws the ticks and labels for the vertical fader."""
        tick_values = []
        if frame.custom_ticks is not None:
             tick_values = frame.custom_ticks
        else:
             value_range = frame.max_val - frame.min_val
             
             # Smart tick logic
             if hasattr(frame, "tick_interval") and frame.tick_interval is not None:
                 ti = float(frame.tick_interval)
             else:
                 target_ticks = 10
                 if value_range > 0:
                     raw_interval = value_range / target_ticks
                     exponent = math.floor(math.log10(raw_interval))
                     fraction = raw_interval / (10**exponent)
                     if fraction < 1.5: snapped = 1
                     elif fraction < 3.5: snapped = 2
                     elif fraction < 7.5: snapped = 5
                     else: snapped = 10
                     ti = snapped * (10**exponent)
                 else:
                     ti = 10

             if ti > 0:
                 curr = math.ceil(frame.min_val / ti) * ti
                 while curr <= frame.max_val:
                     tick_values.append(curr); curr += ti

        # Calculate labeling and drawing intervals
        num_ticks = len(tick_values)
        label_every = 1
        if num_ticks > 20: label_every = 2
        if num_ticks > 50: label_every = 5
        if num_ticks > 100: label_every = 10
        if num_ticks > 250: label_every = 20
        if num_ticks > 500: label_every = 50
        if num_ticks > 1000: label_every = 200
        if num_ticks > 5000: label_every = 500

        draw_every = 1
        if label_every >= 500: draw_every = 100
        elif label_every >= 200: draw_every = 50
        elif label_every >= 50: draw_every = 10
        elif label_every >= 20: draw_every = 5
        elif label_every >= 10: draw_every = 2
        elif label_every >= 5: draw_every = 1

        tick_col = getattr(frame, "tick_color", "light grey")
        sub_tick_col = getattr(frame, "sub_tick_color", tick_col)
        
        # Granular Text Colors
        tick_txt_col = getattr(frame, "tick_text_color", tick_col)
        sub_tick_txt_col = getattr(frame, "sub_tick_text_color", sub_tick_col)
        
        label_pos = getattr(frame, "tick_label_position", "right")

        # Calculate safety margin to avoid fader cap overlap
        # Labels should be at least 5px away from the cap edge OR the tick edge
        # On narrow faders, we reduce this margin.
        margin = 5
        if width < 100: margin = 2
        if width < 80: margin = 0
        
        text_offset = max(tick_length_half, (cap_width / 2)) + margin

        # If still too wide for the canvas, we allow it to overlap the cap slightly
        # because the user might have a very wide cap in a narrow fader.
        if label_pos in ["right", "both"] and (cx + text_offset > width - 10):
            # Try to fit it by reducing offset, even if it overlaps cap
            text_offset = width - cx - 15 # Give at least 15px for the number text
            # But don't go inside the track!
            text_offset = max(text_offset, slot_w/2 + 5)
        
        if label_pos in ["left", "both"] and (cx - text_offset < 10):
            text_offset = cx - 15
            text_offset = max(text_offset, slot_w/2 + 5)

        for i, tick_value in enumerate(tick_values):
            range_val = frame.max_val - frame.min_val
            linear_tick_norm = max(0.0, min(1.0, (tick_value - frame.min_val) / range_val if range_val != 0 else 0))
            
            display_tick_norm = max(0.0000001, linear_tick_norm) ** (1.0 / frame.log_exponent) if frame.log_exponent != 1.0 else linear_tick_norm
            tick_y_pos = available_height * (1 - display_tick_norm) + padding
            
            is_main_tick = (i % label_every == 0)
            current_tick_col = tick_col if is_main_tick else sub_tick_col
            current_text_col = tick_txt_col if is_main_tick else sub_tick_txt_col

            # Draw tick line (Segmented to avoid crossing the track slot)
            if i % draw_every == 0:
                gap = 2
                # Left segment
                canvas.create_line(cx - tick_length_half, tick_y_pos, cx - slot_w/2 - gap, tick_y_pos, 
                                   fill=current_tick_col, width=frame.tick_thickness, tags="static")
                # Right segment
                canvas.create_line(cx + slot_w/2 + gap, tick_y_pos, cx + tick_length_half, tick_y_pos, 
                                   fill=current_tick_col, width=frame.tick_thickness, tags="static")
            
            # Draw tick label
            if is_main_tick:
                if tick_value == int(tick_value):
                    tick_text = str(int(tick_value))
                else:
                    tick_text = f"{tick_value:.1f}"
                
                if label_pos in ["right", "both"]:
                    canvas.create_text(cx + text_offset, tick_y_pos, text=tick_text, 
                                       fill=current_text_col, font=frame.tick_font, anchor="w", tags="static")
                if label_pos in ["left", "both"]:
                    canvas.create_text(cx - text_offset, tick_y_pos, text=tick_text, 
                                       fill=current_text_col, font=frame.tick_font, anchor="e", tags="static")
