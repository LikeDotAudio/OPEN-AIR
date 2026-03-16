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
        center_x, center_y = width / 2, height / 2
        
        # Extract config
        config = self.config
        arc_width = config["arc_width"]
        show_ticks = config["show_ticks"]
        tick_length = config["tick_length"]
        min_val, max_val = config["min"], config["max"]
        indicator_color = config["indicator_color"]
        secondary = self.state["secondary_current"]
        knob_style = config["knob_style"]
        label_text = getattr(self, 'label_text', None)
        
        # Reserve space for text
        label_padding = 12
        top_reserve = label_padding if config["text_pos"] == "top" and label_text and config["show_label"] else 0
        bottom_reserve = label_padding if (config["text_pos"] == "bottom" and label_text and config["show_label"]) or (not config["text_inside"] and not config["no_center"]) else 0
        
        padding = (arc_width / 2) + 12 # Safety margin
        if show_ticks: padding += tick_length + 4

        usable_width, usable_height = width - (padding * 2), height - top_reserve - bottom_reserve - (padding * 2)
        radius = (min(usable_width, usable_height) / 2) * 0.8
        if radius < 8: radius = 8
        
        adjusted_center_y = (top_reserve + (height - bottom_reserve)) / 2

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
        
        self._draw_track(center_x, adjusted_center_y, radius, bg_start, bg_extent, start_angle, val_extent, secondary, indicator_color, arc_width, knob_style)
        
        if show_ticks:
            self._draw_ticks(center_x, adjusted_center_y, radius, arc_width, tick_length, config["tick_style"], secondary, min_val, max_val)

        if knob_style != "dial":
            depth, side_color = 1.5, "#111111"
            self._draw_body(center_x + depth, adjusted_center_y + depth, radius, config["shape"], side_color, 0, pointer_angle_deg, 0, side_color, config["teeth"])
            cap_center_x, cap_center_y = center_x - depth, adjusted_center_y - depth
            self._draw_body(cap_center_x, cap_center_y, radius, config["shape"], config["outline_color"], config["gradient_level"], pointer_angle_deg, config["outline_thickness"], config["fill_color"], config["teeth"])
            if config["fill_color"] or config["knob_style"] == "standard":
                draw_knob_3d_effects(self, cap_center_x, cap_center_y, radius, config["shape"], config["fill_color"])
            self._draw_pointer(cap_center_x, cap_center_y, radius, arc_width, pointer_angle_deg, config["pointer_style"], indicator_color, config["pointer_length"], config["pointer_offset"], config["no_center"])
        else:
            self._draw_pointer(center_x, adjusted_center_y, radius, arc_width, pointer_angle_deg, config["pointer_style"], indicator_color, config["pointer_length"], config["pointer_offset"], config["no_center"])

        # 3. Text
        foreground_color = config["fg_color"]
        if label_text and config["show_label"]:
            text_padding = 4
            visual_radius = radius + (arc_width / 2)
            if show_ticks: visual_radius += tick_length + 2
            label_x, label_y, label_anchor = center_x, adjusted_center_y - visual_radius - text_padding, "s"
            if config["text_pos"] == "bottom": label_y, label_anchor = adjusted_center_y + visual_radius + text_padding, "n"
            elif config["text_pos"] == "left": label_x, label_y, label_anchor = center_x - visual_radius - text_padding, adjusted_center_y, "e"
            elif config["text_pos"] == "right": label_x, label_y, label_anchor = center_x + visual_radius + text_padding, adjusted_center_y, "w"
            self.create_text(label_x, label_y, text=label_text, fill=foreground_color, font=("Helvetica", 9, "bold"), anchor=label_anchor, tags=("industrial_text", "vu_static"))

        val_str = f"{int(value)}"
        if config["text_inside"]:
            self.create_text(center_x, adjusted_center_y + (10 if not config["no_center"] else 0), text=val_str, fill=indicator_color, font=("Helvetica", 8, "bold"), tags=("industrial_text", "vu_static"))
        else:
            visual_radius = radius + (arc_width / 2)
            if show_ticks: visual_radius += tick_length + 2
            value_y = adjusted_center_y + visual_radius + 4
            if config["text_pos"] == "bottom": value_y += 12 
            self.create_text(center_x, value_y, text=val_str, fill=foreground_color, font=("Helvetica", 8), anchor="n", tags=("industrial_text", "vu_static"))

    def _draw_body(self, center_x, center_y, radius, shape, color, gradient_level, rotation_angle=0, outline_thickness=0, fill_color="", teeth=8):
        steps = gradient_level + 1
        for index in range(steps):
            current_radius = radius - (index * 2)
            if current_radius <= 0: break
            current_thickness = outline_thickness if index == 0 else 1
            current_fill = fill_color if (index == 0 or steps == 1) else ""
            if shape == "circle":
                if gradient_level > 0 or (index == 0 and (current_thickness > 0 or current_fill)):
                    self.create_oval(center_x-current_radius, center_y-current_radius, center_x+current_radius, center_y+current_radius, outline=color, width=current_thickness, fill=current_fill)
            elif shape == "octagon":
                points = self._get_poly_points(center_x, center_y, current_radius, sides=8, start_angle=rotation_angle)
                self.create_polygon(points, outline=color, fill=current_fill, width=current_thickness)
            elif shape == "gear":
                points = self._get_gear_points(center_x, center_y, current_radius, teeth=teeth, notch_depth=0.15, start_angle=rotation_angle)
                self.create_polygon(points, outline=color, fill=current_fill, width=current_thickness)

    def _draw_track(self, center_x, center_y, radius, bg_start, bg_extent, start_angle, val_extent, bg_color, active_color, width, knob_style="standard"):
        self.create_arc(center_x - radius, center_y - radius, center_x + radius, center_y + radius, start=bg_start, extent=bg_extent, style=tk.ARC, outline=bg_color, width=width)
        style = tk.ARC if knob_style != "dial" else tk.PIESLICE
        final_color = "red" if (knob_style == "panner" and val_extent < 0) else active_color
        if abs(val_extent) > 0.1:
            self.create_arc(center_x - radius, center_y - radius, center_x + radius, center_y + radius, start=start_angle, extent=val_extent, style=style, outline=final_color if style==tk.ARC else "", fill=final_color if style==tk.PIESLICE else "", width=width)
        elif knob_style == "panner": 
            self.create_line(center_x, center_y - radius + 2, center_x, center_y - radius + 12, fill=bg_color, width=2)

    def _draw_ticks(self, center_x, center_y, radius, arc_width, tick_length, style, color, min_val, max_val):
        start_angle, end_angle, step = 240, 240 - 300, 30
        current_angle, value_step, current_value = start_angle, (max_val - min_val) / 10.0, min_val
        while current_angle >= end_angle - 1:
            radians = math.radians(current_angle)
            tick_start_distance, tick_end_distance = radius + (arc_width/2) + 2, radius + (arc_width/2) + 2 + tick_length
            tick_start_x, tick_start_y = center_x + tick_start_distance * math.cos(radians), center_y - tick_start_distance * math.sin(radians)
            tick_end_x, tick_end_y = center_x + tick_end_distance * math.cos(radians), center_y - tick_end_distance * math.sin(radians)
            if style == "dots": self.create_oval(tick_end_x-1, tick_end_y-1, tick_end_x+1, tick_end_y+1, fill=color, outline=color)
            elif style == "numeric": self.create_text(tick_end_x, tick_end_y, text=f"{int(current_value)}", fill=color, font=("Arial", 6))
            else: self.create_line(tick_start_x, tick_start_y, tick_end_x, tick_end_y, fill=color, width=1)
            current_angle -= step; current_value += value_step

    def _draw_pointer(self, center_x, center_y, radius, arc_width, angle_deg, style, color, length, offset, no_center):
        radians = math.radians(angle_deg)
        pointer_start, pointer_end = offset, (radius - arc_width/2) if length is None else (offset + float(length))
        if style == "triangle":
            tip_x, tip_y = center_x + pointer_end * math.cos(radians), center_y - pointer_end * math.sin(radians)
            triangle_width, base_x, base_y = 5, center_x + pointer_start * math.cos(radians), center_y - pointer_start * math.sin(radians)
            perpendicular_angle = radians + math.pi/2
            corner_1_x, corner_1_y = base_x + triangle_width * math.cos(perpendicular_angle), base_y - triangle_width * math.sin(perpendicular_angle)
            corner_2_x, corner_2_y = base_x - triangle_width * math.cos(perpendicular_angle), base_y + triangle_width * math.sin(perpendicular_angle)
            self.create_polygon(tip_x, tip_y, corner_1_x, corner_1_y, corner_2_x, corner_2_y, fill=color, outline=color)
        elif style == "notch":
            notch_length = 5
            start_x, start_y = center_x + (radius - notch_length) * math.cos(radians), center_y - (radius - notch_length) * math.sin(radians)
            end_x, end_y = center_x + radius * math.cos(radians), center_y - radius * math.sin(radians)
            self.create_line(start_x, start_y, end_x, end_y, fill=color, width=4, capstyle=tk.BUTT)
        else:
            start_x, start_y = center_x + pointer_start * math.cos(radians), center_y - pointer_start * math.sin(radians)
            end_x, end_y = center_x + pointer_end * math.cos(radians), center_y - pointer_end * math.sin(radians)
            self.create_line(start_x, start_y, end_x, end_y, fill=color, width=2, capstyle=tk.ROUND)
        if not no_center: self.create_oval(center_x - 3, center_y - 3, center_x + 3, center_y + 3, fill=color, outline=color)

    def _get_poly_points(self, center_x, center_y, radius, sides=8, start_angle=0):
        points = []
        angle_step = 360 / sides
        for index in range(sides):
            degrees = index * angle_step + start_angle
            radians = math.radians(degrees)
            points.extend([center_x + radius * math.cos(radians), center_y - radius * math.sin(radians)])
        return points

    def _get_gear_points(self, center_x, center_y, radius, teeth=8, notch_depth=0.15, start_angle=0):
        points = []
        num_segments, inner_radius = teeth * 4, radius * (1 - notch_depth)
        angle_step = 360 / num_segments
        for index in range(num_segments):
            degrees = index * angle_step + start_angle
            radians = math.radians(degrees)
            current_radius = radius if (index % 4) in [1, 2] else inner_radius
            points.extend([center_x + current_radius * math.cos(radians), center_y - current_radius * math.sin(radians)])
        return points
