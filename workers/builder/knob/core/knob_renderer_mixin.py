import tkinter as tk
import math
from ..effects.knob_3d_effects import draw_knob_3d_effects

class KnobRendererMixin:
    """Handles the modular rendering pipeline for the Rotary Knob."""

    def _draw_visuals(self):
        """Modular rendering pipeline with 3D depth. Accesses state via self."""
        if not self.winfo_exists(): return
        
        # ⚡ INDUSTRIAL TRANSPARENCY: Don't delete everything, preserve the patina slice
        for item in self.find_all():
            tags = self.gettags(item)
            if "panel_bg_slice" not in tags:
                self.delete(item)
        
        # 0. Draw Industrial Background (Fallback)
        if hasattr(self, 'panel_bg_image') and not self.find_withtag("panel_bg_slice"):
            self.create_image(0, 0, image=self.panel_bg_image, anchor="nw", tags="panel_bg_slice")
                
        width, height = self.state["dims"]["w"], self.state["dims"]["h"]
        if width <= 1: width = self.config["width"]
        if height <= 1: height = self.config["height"]
        cx, cy = width / 2, height / 2
        
        # Extract config
        cfg = self.config
        arc_width = cfg["arc_width"]
        show_ticks = cfg["show_ticks"]
        tick_length = cfg["tick_length"]
        min_val, max_val = cfg["min"], cfg["max"]
        indicator_color = cfg["indicator_color"]
        secondary = self.state["secondary_current"]
        knob_style = cfg["knob_style"]
        label_text = getattr(self, 'label_text', None)
        
        # Reserve space for text
        label_padding = 12
        top_reserve = label_padding if cfg["text_pos"] == "top" and label_text and cfg["show_label"] else 0
        bottom_reserve = label_padding if (cfg["text_pos"] == "bottom" and label_text and cfg["show_label"]) or (not cfg["text_inside"] and not cfg["no_center"]) else 0
        
        padding = (arc_width / 2) + 12 # Safety margin
        if show_ticks: padding += tick_length + 4

        usable_w, usable_h = width - (padding * 2), height - top_reserve - bottom_reserve - (padding * 2)
        radius = (min(usable_w, usable_h) / 2) * 0.8
        if radius < 8: radius = 8
        
        adj_cy = (top_reserve + (height - bottom_reserve)) / 2

        # 1. Math Prep
        value = self.variable.get()
        norm_val = (value - min_val) / (max_val - min_val) if max_val > min_val else 0

        start_angle, extent = 240, -300
        val_extent = extent * norm_val
        pointer_angle_deg = start_angle + val_extent

        if knob_style == "panner":
            mid_val = (min_val + max_val) / 2
            norm_from_center = (value - mid_val) / ((max_val - min_val) / 2)
            panner_max_arc, start_angle = 135, 90
            val_extent = -1 * norm_from_center * panner_max_arc if norm_from_center >= 0 else abs(norm_from_center) * panner_max_arc
            pointer_angle_deg = 90 + (-1 * norm_from_center * panner_max_arc)
        elif knob_style == "dial":
            start_angle, val_extent = 90, -360 * norm_val
            if abs(val_extent) >= 360: val_extent = -359.9
            pointer_angle_deg = start_angle + val_extent

        # 2. Draw Components
        bg_start = 0 if knob_style == "dial" else 240
        bg_extent = 359.9 if knob_style == "dial" else -300
        if knob_style == "panner": bg_start, bg_extent = 225, -270
        
        self._draw_track(cx, adj_cy, radius, bg_start, bg_extent, start_angle, val_extent, secondary, indicator_color, arc_width, knob_style)
        
        if show_ticks:
            self._draw_ticks(cx, adj_cy, radius, arc_width, tick_length, cfg["tick_style"], secondary, min_val, max_val)

        if knob_style != "dial":
            depth, side_color = 1.5, "#111111"
            self._draw_body(cx + depth, adj_cy + depth, radius, cfg["shape"], side_color, 0, pointer_angle_deg, 0, side_color, cfg["teeth"])
            cap_cx, cap_cy = cx - depth, adj_cy - depth
            self._draw_body(cap_cx, cap_cy, radius, cfg["shape"], cfg["outline_color"], cfg["gradient_level"], pointer_angle_deg, cfg["outline_thickness"], cfg["fill_color"], cfg["teeth"])
            if cfg["fill_color"] or cfg["knob_style"] == "standard":
                draw_knob_3d_effects(self, cap_cx, cap_cy, radius, cfg["shape"], cfg["fill_color"])
            self._draw_pointer(cap_cx, cap_cy, radius, arc_width, pointer_angle_deg, cfg["pointer_style"], indicator_color, cfg["pointer_length"], cfg["pointer_offset"], cfg["no_center"])
        else:
            self._draw_pointer(cx, adj_cy, radius, arc_width, pointer_angle_deg, cfg["pointer_style"], indicator_color, cfg["pointer_length"], cfg["pointer_offset"], cfg["no_center"])

        # 3. Text
        fg = cfg["fg_color"]
        if label_text and cfg["show_label"]:
            text_padding = 4
            visual_radius = radius + (arc_width / 2)
            if show_ticks: visual_radius += tick_length + 2
            lx, ly, l_anchor = cx, adj_cy - visual_radius - text_padding, "s"
            if cfg["text_pos"] == "bottom": ly, l_anchor = adj_cy + visual_radius + text_padding, "n"
            elif cfg["text_pos"] == "left": lx, ly, l_anchor = cx - visual_radius - text_padding, adj_cy, "e"
            elif cfg["text_pos"] == "right": lx, ly, l_anchor = cx + visual_radius + text_padding, adj_cy, "w"
            self.create_text(lx, ly, text=label_text, fill=fg, font=("Helvetica", 9, "bold"), anchor=l_anchor, tags=("industrial_text", "vu_static"))

        val_str = f"{int(value)}"
        if cfg["text_inside"]:
            self.create_text(cx, adj_cy + (10 if not cfg["no_center"] else 0), text=val_str, fill=indicator_color, font=("Helvetica", 8, "bold"), tags=("industrial_text", "vu_static"))
        else:
            visual_radius = radius + (arc_width / 2)
            if show_ticks: visual_radius += tick_length + 2
            vy = adj_cy + visual_radius + 4
            if cfg["text_pos"] == "bottom": vy += 12 
            self.create_text(cx, vy, text=val_str, fill=fg, font=("Helvetica", 8), anchor="n", tags=("industrial_text", "vu_static"))

    def _draw_body(self, cx, cy, radius, shape, color, gradient_level, rotation_angle=0, outline_thickness=0, fill_color="", teeth=8):
        steps = gradient_level + 1
        for i in range(steps):
            r = radius - (i * 2)
            if r <= 0: break
            cur_thk = outline_thickness if i == 0 else 1
            cur_fill = fill_color if (i == 0 or steps == 1) else ""
            if shape == "circle":
                if gradient_level > 0 or (i == 0 and (cur_thk > 0 or cur_fill)):
                    self.create_oval(cx-r, cy-r, cx+r, cy+r, outline=color, width=cur_thk, fill=cur_fill)
            elif shape == "octagon":
                pts = self._get_poly_points(cx, cy, r, sides=8, start_angle=rotation_angle)
                self.create_polygon(pts, outline=color, fill=cur_fill, width=cur_thk)
            elif shape == "gear":
                pts = self._get_gear_points(cx, cy, r, teeth=teeth, notch_depth=0.15, start_angle=rotation_angle)
                self.create_polygon(pts, outline=color, fill=cur_fill, width=cur_thk)

    def _draw_track(self, cx, cy, radius, bg_start, bg_extent, start_angle, val_extent, bg_color, active_color, width, knob_style="standard"):
        self.create_arc(cx - radius, cy - radius, cx + radius, cy + radius, start=bg_start, extent=bg_extent, style=tk.ARC, outline=bg_color, width=width)
        style = tk.ARC if knob_style != "dial" else tk.PIESLICE
        final_color = "red" if (knob_style == "panner" and val_extent < 0) else active_color
        if abs(val_extent) > 0.1:
            self.create_arc(cx - radius, cy - radius, cx + radius, cy + radius, start=start_angle, extent=val_extent, style=style, outline=final_color if style==tk.ARC else "", fill=final_color if style==tk.PIESLICE else "", width=width)
        elif knob_style == "panner": 
            self.create_line(cx, cy - radius + 2, cx, cy - radius + 12, fill=bg_color, width=2)

    def _draw_ticks(self, cx, cy, radius, arc_width, tick_length, style, color, min_val, max_val):
        start_angle, end_angle, step = 240, 240 - 300, 30
        curr, val_step, curr_val = start_angle, (max_val - min_val) / 10.0, min_val
        while curr >= end_angle - 1:
            rad = math.radians(curr)
            ts_dist, te_dist = radius + (arc_width/2) + 2, radius + (arc_width/2) + 2 + tick_length
            ts_x, ts_y = cx + ts_dist * math.cos(rad), cy - ts_dist * math.sin(rad)
            te_x, te_y = cx + te_dist * math.cos(rad), cy - te_dist * math.sin(rad)
            if style == "dots": self.create_oval(te_x-1, te_y-1, te_x+1, te_y+1, fill=color, outline=color)
            elif style == "numeric": self.create_text(te_x, te_y, text=f"{int(curr_val)}", fill=color, font=("Arial", 6))
            else: self.create_line(ts_x, ts_y, te_x, te_y, fill=color, width=1)
            curr -= step; curr_val += val_step

    def _draw_pointer(self, cx, cy, radius, arc_width, angle_deg, style, color, length, offset, no_center):
        rad = math.radians(angle_deg)
        p_start, p_end = offset, (radius - arc_width/2) if length is None else (offset + float(length))
        if style == "triangle":
            tip_x, tip_y = cx + p_end * math.cos(rad), cy - p_end * math.sin(rad)
            w, bx, by = 5, cx + p_start * math.cos(rad), cy - p_start * math.sin(rad)
            perp = rad + math.pi/2
            c1x, c1y = bx + w * math.cos(perp), by - w * math.sin(perp)
            c2x, c2y = bx - w * math.cos(perp), by + w * math.sin(perp)
            self.create_polygon(tip_x, tip_y, c1x, c1y, c2x, c2y, fill=color, outline=color)
        elif style == "notch":
            notch_len = 5
            sx, sy = cx + (radius - notch_len) * math.cos(rad), cy - (radius - notch_len) * math.sin(rad)
            ex, ey = cx + radius * math.cos(rad), cy - radius * math.sin(rad)
            self.create_line(sx, sy, ex, ey, fill=color, width=4, capstyle=tk.BUTT)
        else:
            sx, sy = cx + p_start * math.cos(rad), cy - p_start * math.sin(rad)
            ex, ey = cx + p_end * math.cos(rad), cy - p_end * math.sin(rad)
            self.create_line(sx, sy, ex, ey, fill=color, width=2, capstyle=tk.ROUND)
        if not no_center: self.create_oval(cx - 3, cy - 3, cx + 3, cy + 3, fill=color, outline=color)

    def _get_poly_points(self, cx, cy, radius, sides=8, start_angle=0):
        points = []
        angle_step = 360 / sides
        for i in range(sides):
            deg = i * angle_step + start_angle
            rad = math.radians(deg)
            points.extend([cx + radius * math.cos(rad), cy - radius * math.sin(rad)])
        return points

    def _get_gear_points(self, cx, cy, radius, teeth=8, notch_depth=0.15, start_angle=0):
        points = []
        num_segments, inner_radius = teeth * 4, radius * (1 - notch_depth)
        angle_step = 360 / num_segments
        for i in range(num_segments):
            deg = i * angle_step + start_angle
            rad = math.radians(deg)
            r = radius if (i % 4) in [1, 2] else inner_radius
            points.extend([cx + r * math.cos(rad), cy - r * math.sin(rad)])
        return points
