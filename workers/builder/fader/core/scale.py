# workers/builder/fader/core/scale.py

import math
import tkinter as tk

class ScaleDrawer:
    @staticmethod
    def draw(canvas, frame, width, height, layout):
        """Draws the ticks and labels for the vertical fader."""
        cx = layout['cx']
        avail_h = layout['available_height']
        padding = layout['padding']
        tick_h_half = layout['tick_length_half']
        slot_w = layout['slot_w']
        cap_w = layout.get('cap_width', 40)

        tick_values = ScaleDrawer._get_tick_values(frame)
        label_every, draw_every = ScaleDrawer._calc_intervals(len(tick_values))
        
        cfg = ScaleDrawer._get_tick_config(frame)
        offset = ScaleDrawer._calc_text_offset(width, cx, tick_h_half, slot_w, cap_w, frame, cfg['label_pos'])

        for i, val in enumerate(tick_values):
            y = ScaleDrawer._calc_tick_y(val, frame, avail_h, padding)
            is_main = (i % label_every == 0)
            
            if i % draw_every == 0:
                ScaleDrawer._draw_tick_line(canvas, cx, y, tick_h_half, slot_w, is_main, frame, cfg)
            
            if is_main:
                ScaleDrawer._draw_tick_label(canvas, cx, y, val, offset, frame, cfg)

    @staticmethod
    def _get_tick_values(frame):
        """Retrieve custom ticks or generate smart ticks based on frame range."""
        if frame.custom_ticks is not None:
            return frame.custom_ticks
             
        v_range = frame.max_val - frame.min_val
        ti = ScaleDrawer._get_smart_interval(frame, v_range)
        
        ticks = []
        if ti > 0:
            curr = math.ceil(frame.min_val / ti) * ti
            while curr <= frame.max_val:
                ticks.append(curr); curr += ti
        return ticks

    @staticmethod
    def _get_smart_interval(frame, v_range):
        """Calculate a human-friendly tick interval."""
        if hasattr(frame, "tick_interval") and frame.tick_interval is not None:
            return float(frame.tick_interval)
        if v_range <= 0: return 10
        
        raw = v_range / 10.0
        exp = math.floor(math.log10(raw))
        frac = raw / (10**exp)
        
        if frac < 1.5: snap = 1
        elif frac < 3.5: snap = 2
        elif frac < 7.5: snap = 5
        else: snap = 10
        return snap * (10**exp)

    @staticmethod
    def _calc_intervals(num_ticks):
        """Determine labeling and drawing density to avoid overcrowding."""
        label_map = [(5000, 500), (1000, 200), (500, 50), (250, 20), (100, 10), (50, 5), (20, 2)]
        label_every = 1
        for threshold, interval in label_map:
            if num_ticks > threshold:
                label_every = interval
                break
        
        draw_map = [(500, 100), (200, 50), (50, 10), (20, 5), (10, 2), (5, 1)]
        draw_every = 1
        for threshold, interval in draw_map:
            if label_every >= threshold:
                draw_every = interval
                break
        return label_every, draw_every

    @staticmethod
    def _get_tick_config(frame):
        """Extract aesthetic configuration for ticks from the frame."""
        t_col = getattr(frame, "tick_color", "light grey")
        st_col = getattr(frame, "sub_tick_color", t_col)
        return {
            'tick_col': t_col,
            'sub_tick_col': st_col,
            'tick_txt_col': getattr(frame, "tick_text_color", t_col),
            'sub_tick_txt_col': getattr(frame, "sub_tick_text_color", st_col),
            'label_pos': getattr(frame, "tick_label_position", "right")
        }

    @staticmethod
    def _calc_text_offset(width, cx, tick_h_half, slot_w, cap_w, frame, label_pos):
        """Calculate safe offset for labels to avoid overlap with the fader cap."""
        margin = 5
        if width < 100: margin = 2
        if width < 80: margin = 0
        
        offset = max(tick_h_half, (cap_w / 2)) + margin
        
        # Prevent overflowing the canvas boundaries
        if label_pos in ["right", "both"] and (cx + offset > width - 10):
            offset = max(width - cx - 15, slot_w/2 + 5)
        if label_pos in ["left", "both"] and (cx - offset < 10):
            offset = max(cx - 15, slot_w/2 + 5)
        return offset

    @staticmethod
    def _calc_tick_y(val, frame, avail_h, padding):
        """Convert a value to a vertical Y coordinate on the canvas."""
        v_range = frame.max_val - frame.min_val
        lin_norm = max(0.0, min(1.0, (val - frame.min_val) / v_range if v_range != 0 else 0))
        disp_norm = max(1e-7, lin_norm) ** (1.0 / frame.log_exponent) if frame.log_exponent != 1.0 else lin_norm
        return avail_h * (1 - disp_norm) + padding

    @staticmethod
    def _draw_tick_line(canvas, cx, y, length_half, slot_w, is_main, frame, cfg):
        """Draw segmented tick lines on both sides of the track slot."""
        color = cfg['tick_col'] if is_main else cfg['sub_tick_col']
        gap = 2
        canvas.create_line(cx - length_half, y, cx - slot_w/2 - gap, y, 
                           fill=color, width=frame.tick_thickness, tags="static")
        canvas.create_line(cx + slot_w/2 + gap, y, cx + length_half, y, 
                           fill=color, width=frame.tick_thickness, tags="static")

    @staticmethod
    def _draw_tick_label(canvas, cx, y, val, offset, frame, cfg):
        """Render the numeric label at the specified offset."""
        text = str(int(val)) if val == int(val) else f"{val:.1f}"
        color = cfg['tick_txt_col'] # In this refactor we assume only main ticks call this
        pos = cfg['label_pos']
        
        if pos in ["right", "both"]:
            canvas.create_text(cx + offset, y, text=text, fill=color, font=frame.tick_font, anchor="w", tags="static")
        if pos in ["left", "both"]:
            canvas.create_text(cx - offset, y, text=text, fill=color, font=frame.tick_font, anchor="e", tags="static")
