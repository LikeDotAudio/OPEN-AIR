import tkinter as tk
import math
from dataclasses import dataclass
from typing import Optional

@dataclass
class NeedleConfig:
    val: float
    min_val: float
    max_val: float
    start_angle_deg: float
    end_angle_deg: float
    extent_deg: float
    main_arc_radius: float
    text_offset_from_arc: float
    color: str
    style: str
    thick: float
    counter_clockwise: bool
    pivot_size: float
    needle_scale: float = 1.0
    tag: str = "vu_needle"

class NeedleDrawer:
    @staticmethod
    def draw_needle(canvas, center_x, center_y, 
                    val, min_val, max_val,
                    start_angle_deg, end_angle_deg, extent_deg,
                    main_arc_radius, text_offset_from_arc,
                    color, style, thick, counter_clockwise, pivot_size,
                    needle_scale=1.0, tag="vu_needle"):
        """
        Draws or updates the needle. Legacy wrapper for draw_with_config.
        """
        config = NeedleConfig(
            val=val, min_val=min_val, max_val=max_val,
            start_angle_deg=start_angle_deg, end_angle_deg=end_angle_deg, extent_deg=extent_deg,
            main_arc_radius=main_arc_radius, text_offset_from_arc=text_offset_from_arc,
            color=color, style=style, thick=thick, counter_clockwise=counter_clockwise,
            pivot_size=pivot_size, needle_scale=needle_scale, tag=tag
        )
        return NeedleDrawer.draw_with_config(canvas, center_x, center_y, config)

    @staticmethod
    def draw_with_config(canvas, cx, cy, config: NeedleConfig):
        """Unified entry point for drawing the needle with a config object."""
        # 1. Prepare common values
        val = max(min(config.val, config.max_val), config.min_val)
        range_val = config.max_val - config.min_val
        norm_val = (val - config.min_val) / range_val if range_val != 0 else 0

        angle_deg = config.end_angle_deg + (norm_val * config.extent_deg) if config.counter_clockwise \
                    else config.start_angle_deg - (norm_val * config.extent_deg)
            
        angle_rad = math.radians(angle_deg)
        length = (config.main_arc_radius + config.text_offset_from_arc - 2) * config.needle_scale
        tip_x, tip_y = cx + length * math.cos(angle_rad), cy - length * math.sin(angle_rad)

        # 2. Try Optimization
        if NeedleDrawer._try_update_existing(canvas, cx, cy, tip_x, tip_y, angle_rad, config):
            return

        # 3. Full redraw
        existing = canvas.find_withtag(config.tag)
        if existing:
            canvas.delete(config.tag)

        # Style Dispatcher
        handlers = {
            "teardrop": NeedleDrawer._draw_teardrop,
            "spade": NeedleDrawer._draw_teardrop, # shared logic
            "knife-edge": NeedleDrawer._draw_knife_edge,
            "baton": NeedleDrawer._draw_baton,
            "hollow-diamond": NeedleDrawer._draw_hollow_diamond,
            "taper": NeedleDrawer._draw_taper,
        }
        
        handler = handlers.get(config.style, NeedleDrawer._draw_line)
        handler(canvas, cx, cy, tip_x, tip_y, angle_rad, length, config)

    @staticmethod
    def _try_update_existing(canvas, cx, cy, tip_x, tip_y, angle_rad, config):
        """Attempts to update existing needle coordinates for performance."""
        existing = canvas.find_withtag(config.tag)
        if not existing or config.style not in ["line", "baton", "taper", "knife-edge"]:
            return False
            
        if config.style == "line":
            canvas.coords(config.tag, cx, cy, tip_x, tip_y)
        elif config.style in ["taper", "knife-edge"]:
            perp_angle = angle_rad + (math.pi / 2)
            base_rad = (config.pivot_size / 2.0) if config.style == "taper" else (config.thick * 1.5)
            bx1, by1 = cx + base_rad * math.cos(perp_angle), cy - base_rad * math.sin(perp_angle)
            bx2, by2 = cx - base_rad * math.cos(perp_angle), cy + base_rad * math.sin(perp_angle)
            canvas.coords(config.tag, bx1, by1, tip_x, tip_y, bx2, by2)
        elif config.style == "baton":
            perp_angle = angle_rad + (math.pi / 2)
            off_x, off_y = (config.thick / 2.0) * math.cos(perp_angle), (config.thick / 2.0) * math.sin(perp_angle)
            canvas.coords(config.tag, cx + off_x, cy - off_y, tip_x + off_x, tip_y - off_y,
                               tip_x - off_x, tip_y + off_y, cx - off_x, cy + off_y)
        return True

    @staticmethod
    def _draw_line(canvas, cx, cy, tip_x, tip_y, angle_rad, length, config):
        canvas.create_line(cx, cy, tip_x, tip_y, width=config.thick, fill=config.color, 
                           capstyle=tk.ROUND, tags=(config.tag, "vu_element"))

    @staticmethod
    def _draw_taper(canvas, cx, cy, tip_x, tip_y, angle_rad, length, config):
        perp_angle = angle_rad + (math.pi / 2)
        base_rad = config.pivot_size / 2.0
        bx1, by1 = cx + base_rad * math.cos(perp_angle), cy - base_rad * math.sin(perp_angle)
        bx2, by2 = cx - base_rad * math.cos(perp_angle), cy + base_rad * math.sin(perp_angle)
        canvas.create_polygon([bx1, by1, tip_x, tip_y, bx2, by2], fill=config.color, outline=config.color, tags=(config.tag, "vu_element"))

    @staticmethod
    def _draw_knife_edge(canvas, cx, cy, tip_x, tip_y, angle_rad, length, config):
        perp_angle = angle_rad + (math.pi / 2)
        base_rad = config.thick * 1.5
        bx1, by1 = cx + base_rad * math.cos(perp_angle), cy - base_rad * math.sin(perp_angle)
        bx2, by2 = cx - base_rad * math.cos(perp_angle), cy + base_rad * math.sin(perp_angle)
        canvas.create_polygon([bx1, by1, tip_x, tip_y, bx2, by2], fill=config.color, outline=config.color, tags=(config.tag, "vu_element"))

    @staticmethod
    def _draw_baton(canvas, cx, cy, tip_x, tip_y, angle_rad, length, config):
        perp_angle = angle_rad + (math.pi / 2)
        off_x, off_y = (config.thick / 2.0) * math.cos(perp_angle), (config.thick / 2.0) * math.sin(perp_angle)
        canvas.create_polygon([cx + off_x, cy - off_y, tip_x + off_x, tip_y - off_y,
                               tip_x - off_x, tip_y + off_y, cx - off_x, cy + off_y], 
                               fill=config.color, outline=config.color, tags=(config.tag, "vu_element"))

    @staticmethod
    def _draw_teardrop(canvas, cx, cy, tip_x, tip_y, angle_rad, length, config):
        d1, d2 = length * 0.75, length * 0.875
        p1x, p1y = cx + d1 * math.cos(angle_rad), cy - d1 * math.sin(angle_rad)
        p2x, p2y = cx + d2 * math.cos(angle_rad), cy - d2 * math.sin(angle_rad)
        
        # Line 1
        canvas.create_line(cx, cy, p1x, p1y, width=config.thick, fill=config.color, capstyle=tk.ROUND, tags=(config.tag, "vu_element"))
        
        # Bulb
        bulb_w = config.thick * 2.5
        perp_angle = angle_rad + (math.pi / 2)
        bx, by = cx + (d1 - config.thick) * math.cos(angle_rad), cy - (d1 - config.thick) * math.sin(angle_rad)
        mid_dist = (d1 + d2) / 2
        mx, my = cx + mid_dist * math.cos(angle_rad), cy - mid_dist * math.sin(angle_rad)
        s1x, s1y = mx + bulb_w * math.cos(perp_angle), my - bulb_w * math.sin(perp_angle)
        s2x, s2y = mx - bulb_w * math.cos(perp_angle), my + bulb_w * math.sin(perp_angle)
        
        canvas.create_polygon([bx, by, s1x, s1y, p2x, p2y, s2x, s2y], fill=config.color, outline=config.color, smooth=True, tags=(config.tag, "vu_element"))
        
        # Tip
        canvas.create_line(p2x, p2y, tip_x, tip_y, width=config.thick, fill=config.color, capstyle=tk.ROUND, tags=(config.tag, "vu_element"))

    @staticmethod
    def _draw_hollow_diamond(canvas, cx, cy, tip_x, tip_y, angle_rad, length, config):
        d_mid, d_start = length * 0.8, length * 0.6
        perp_angle, width = angle_rad + (math.pi / 2), config.thick * 4
        mx, my = cx + d_mid * math.cos(angle_rad), cy - d_mid * math.sin(angle_rad)
        sx, sy = cx + d_start * math.cos(angle_rad), cy - d_start * math.sin(angle_rad)
        
        p1x, p1y = mx + width * math.cos(perp_angle), my - width * math.sin(perp_angle)
        p2x, p2y = mx - width * math.cos(perp_angle), my + width * math.sin(perp_angle)
        canvas.create_polygon([sx, sy, p1x, p1y, tip_x, tip_y, p2x, p2y], fill=config.color, outline=config.color, tags=(config.tag, "vu_element"))
        
        bg, i_width, i_start, i_tip_dist = canvas.cget("bg"), width * 0.6, d_start + (config.thick * 2), length - (config.thick * 2)
        itx, ity = cx + i_tip_dist * math.cos(angle_rad), cy - i_tip_dist * math.sin(angle_rad)
        ip1x, ip1y = mx + i_width * math.cos(perp_angle), my - i_width * math.sin(perp_angle)
        ip2x, ip2y = mx - i_width * math.cos(perp_angle), my + i_width * math.sin(perp_angle)
        
        cutout_sx = sx + (config.thick*2)*math.cos(angle_rad)
        cutout_sy = sy - (config.thick*2)*math.sin(angle_rad)
        canvas.create_polygon([cutout_sx, cutout_sy, ip1x, ip1y, itx, ity, ip2x, ip2y], fill=bg, outline=bg, tags=(config.tag, "vu_element"))
        canvas.create_line(cx, cy, sx, sy, width=config.thick, fill=config.color, tags=(config.tag, "vu_element"))
