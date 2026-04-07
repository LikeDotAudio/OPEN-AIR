# Core/layout_calculator.py
from oaGui.Methods.i18n_utils import get_text
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import math
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Any

@dataclass
class LayoutResult:
    total_width: int
    total_height: int
    bar_x: float
    bar_y: float
    base_len: float
    bar_thick: float
    
    # Pixel coordinates for shapes
    bar_track: List[float]
    zone1: List[float]
    zone2: List[float]
    zone3: List[float]
    indicator: List[float]
    peak_led: Tuple[float, float, float, float]
    
    # Tick data: list of (x1, y1, x2, y2, is_subtick)
    ticks: List[Tuple[float, float, float, float, bool]]
    # Grid data: list of (x1, y1, x2, y2, is_subtick)
    grid_lines: List[Tuple[float, float, float, float, bool]]
    # Label data: list of (x, y, text, anchor)
    scale_labels: List[Tuple[float, float, str, str]]
    
    # For dynamic updates
    peak_flag_points: List[float] = field(default_factory=list)

class MeterLayoutCalculator:
    """Calculates all pixel coordinates for the meter elements based on configuration and available size."""
    
    def __init__(self):
        self.last_w = 0
        self.last_h = 0

    def calculate(self, w: int, h: int, cfg) -> LayoutResult:
        """Computes the full coordinate set for the current widget dimensions."""
        
        # 1. Pappings & Buffers
        scale_text_padding = 15 # Horizontal buffer for numbers
        
        tick_height_val = cfg.tick_size if (cfg.show_ticks or cfg.tick_both_sides) else 0
        if cfg.is_vertical:
            label_thickness = (cfg.font_size * 3) if (cfg.scale_position != "none" and cfg.show_scale_labels) else 0
        else:
            label_thickness = (cfg.font_size + 4) if (cfg.scale_position != "none" and cfg.show_scale_labels) else 0
            
        side_a_pad = tick_height_val + label_thickness
        if cfg.peak_display: side_a_pad += 6
        
        side_b_pad = tick_height_val if cfg.tick_both_sides else 0
        
        # 2. Base Bar Geometry
        if not cfg.is_vertical:
            eff_h = cfg.height
            b_thick = eff_h
            
            peak_led_size = cfg.peak_size if cfg.peak_size > 0 else b_thick
            peak_led_gap = 5 if cfg.peak_display else 0
            led_offset = peak_led_gap + peak_led_size if cfg.peak_display else 0
            
            eff_w = min(w, cfg.width + (scale_text_padding * 2))
            center_x_off = max(0, (w - eff_w) / 2)
            
            b_len = max(1, eff_w - led_offset - (scale_text_padding * 2))
            bar_x = center_x_off + scale_text_padding
            
            base_y = side_a_pad if cfg.scale_position == "top" else side_b_pad
            bar_y = base_y + max(0, (h - (eff_h + side_a_pad + side_b_pad)) / 2)
            
            peak_y_off = (b_thick - peak_led_size) / 2
            peak_led_coords = (
                bar_x + b_len + peak_led_gap, bar_y + peak_y_off,
                bar_x + b_len + peak_led_gap + peak_led_size, bar_y + peak_y_off + peak_led_size
            )
            tick_start = bar_y + b_thick if cfg.scale_position == "bottom" else bar_y
            tick_dir = 1 if cfg.scale_position == "bottom" else -1
            
        else:
            eff_w = cfg.width
            b_thick = eff_w
            
            peak_led_size = cfg.peak_size if cfg.peak_size > 0 else b_thick
            peak_led_gap = 5 if cfg.peak_display else 0
            led_offset = peak_led_gap + peak_led_size if cfg.peak_display else 0
            
            eff_h = min(h, cfg.height + (scale_text_padding * 2))
            center_y_off = max(0, (h - eff_h) / 2)
            
            b_len = max(1, eff_h - led_offset - (scale_text_padding * 2))
            
            base_x = side_a_pad if cfg.scale_position in ["top", "left"] else side_b_pad
            bar_x = base_x + max(0, (w - (eff_w + side_a_pad + side_b_pad)) / 2)
            bar_y = center_y_off + led_offset + scale_text_padding
            
            peak_x_off = (b_thick - peak_led_size) / 2
            peak_led_coords = (
                bar_x + peak_x_off, bar_y - led_offset - scale_text_padding,
                bar_x + peak_x_off + peak_led_size, bar_y - led_offset - scale_text_padding + peak_led_size
            )
            tick_start = bar_x + b_thick if cfg.scale_position in ["bottom", "right"] else bar_x
            tick_dir = 1 if cfg.scale_position in ["bottom", "right"] else -1

        # 3. Helper for Poly Coordinates (Rotation)
        def get_poly(v_start, v_end, t_start, t_end):
            x1 = bar_x + v_start
            x2 = bar_x + v_end
            y1 = bar_y + t_start
            y2 = bar_y + t_end
            
            if cfg.rotation_angle == 0.0: return [x1, y1, x2, y2]
            if cfg.rotation_angle == 90.0:
                vx1 = bar_x + t_start
                vy1 = bar_y + (b_len - v_end)
                vx2 = bar_x + t_end
                vy2 = bar_y + (b_len - v_start)
                return [vx1, vy1, vx2, vy2]
            
            # Arbitrary Rotation
            cx, cy = bar_x + (b_len / 2), bar_y + (b_thick / 2)
            points = [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]
            rad = math.radians(cfg.rotation_angle)
            cos_a, sin_a = math.cos(rad), math.sin(rad)
            coords = []
            for px, py in points:
                tx, ty = px - cx, py - cy
                rx = tx * cos_a - ty * sin_a
                ry = tx * sin_a + ty * cos_a
                coords.extend([cx + rx, cy + ry])
            return coords

        # 4. Zones
        z1_norm = (cfg.middle_range - cfg.min_val) / (cfg.max_val - cfg.min_val)
        z2_norm = (cfg.upper_range - cfg.min_val) / (cfg.max_val - cfg.min_val)
        z1_pix = max(0, min(b_len, z1_norm * b_len))
        z2_pix = max(0, min(b_len, z2_norm * b_len))
        
        # 5. Ticks & Grid
        ticks = []
        grid_lines = []
        scale_labels = []
        
        num_main = 5
        for i in range(num_main + 1):
            norm = i / num_main
            val = cfg.min_val + norm * (cfg.max_val - cfg.min_val)
            pos = norm * b_len
            
            if not cfg.is_vertical:
                tx1, ty1 = bar_x + pos, tick_start
                tx2, ty2 = bar_x + pos, tick_start + (tick_height_val * tick_dir)
                gx1, gy1, gx2, gy2 = bar_x + pos, bar_y, bar_x + pos, bar_y + b_thick
                label_x, label_y = tx2, ty2 + (5 * tick_dir)
                anchor = "n" if cfg.scale_position == "bottom" else "s"
            else:
                tx1, ty1 = tick_start, bar_y + (b_len - pos)
                tx2, ty2 = tick_start + (tick_height_val * tick_dir), bar_y + (b_len - pos)
                gx1, gy1, gx2, gy2 = bar_x, bar_y + (b_len - pos), bar_x + b_thick, bar_y + (b_len - pos)
                label_x, label_y = tx2 + (5 * tick_dir), ty2
                anchor = "w" if cfg.scale_position in ["bottom", "right"] else "e"
            
            if cfg.show_ticks: ticks.append((tx1, ty1, tx2, ty2, False))
            if cfg.tick_grid_overlay: grid_lines.append((gx1, gy1, gx2, gy2, False))
            if cfg.scale_position != "none" and cfg.show_scale_labels:
                scale_labels.append((label_x, label_y, f"{int(val)}", anchor))
                
            if cfg.tick_both_sides:
                opp_dir = -tick_dir
                if not cfg.is_vertical:
                    opp_start = bar_y if tick_dir == 1 else bar_y + b_thick
                    ticks.append((bar_x + pos, opp_start, bar_x + pos, opp_start + (tick_height_val * opp_dir), False))
                else:
                    opp_start = bar_x if tick_dir == 1 else bar_x + b_thick
                    ticks.append((opp_start, bar_y + (b_len - pos), opp_start + (tick_height_val * opp_dir), bar_y + (b_len - pos), False))

            # Subticks
            if i < num_main and cfg.sub_ticks > 0:
                step = b_len / num_main
                sub_step = step / (cfg.sub_ticks + 1)
                for j in range(1, cfg.sub_ticks + 1):
                    spos = pos + (j * sub_step)
                    if not cfg.is_vertical:
                        stx1, sty1 = bar_x + spos, tick_start
                        stx2, sty2 = bar_x + spos, tick_start + ((tick_height_val * 0.5) * tick_dir)
                        sgx1, sgy1, sgx2, sgy2 = bar_x + spos, bar_y, bar_x + spos, bar_y + b_thick
                    else:
                        stx1, sty1 = tick_start, bar_y + (b_len - spos)
                        stx2, sty2 = tick_start + ((tick_height_val * 0.5) * tick_dir), bar_y + (b_len - spos)
                        sgx1, sgy1, sgx2, sgy2 = bar_x, bar_y + (b_len - spos), bar_x + b_thick, bar_y + (b_len - spos)
                    
                    if cfg.show_ticks: ticks.append((stx1, sty1, stx2, sty2, True))
                    if cfg.tick_sub_grid_overlay: grid_lines.append((sgx1, sgy1, sgx2, sgy2, True))
                    
                    if cfg.tick_both_sides:
                        opp_dir = -tick_dir
                        if not cfg.is_vertical:
                            opp_start = bar_y if tick_dir == 1 else bar_y + b_thick
                            ticks.append((bar_x + spos, opp_start, bar_x + spos, opp_start + ((tick_height_val * 0.5) * opp_dir), True))
                        else:
                            opp_start = bar_x if tick_dir == 1 else bar_x + b_thick
                            ticks.append((opp_start, bar_y + (b_len - spos), opp_start + ((tick_height_val * 0.5) * opp_dir), bar_y + (b_len - spos), True))

        # Add "Rails" to grid if grid is enabled
        if cfg.tick_grid_overlay:
            if not cfg.is_vertical:
                grid_lines.append((bar_x, bar_y, bar_x + b_len, bar_y, False))
                grid_lines.append((bar_x, bar_y + b_thick, bar_x + b_len, bar_y + b_thick, False))
            else:
                grid_lines.append((bar_x, bar_y, bar_x, bar_y + b_len, False))
                grid_lines.append((bar_x + b_thick, bar_y, bar_x + b_thick, bar_y + b_len, False))

        return LayoutResult(
            total_width=w, total_height=h,
            bar_x=bar_x, bar_y=bar_y, base_len=b_len, bar_thick=b_thick,
            bar_track=get_poly(0, b_len, 0, b_thick),
            zone1=get_poly(0, z1_pix, 0, b_thick),
            zone2=get_poly(z1_pix, z2_pix, 0, b_thick),
            zone3=get_poly(z2_pix, b_len, 0, b_thick),
            indicator=get_poly(0, 5, 0, b_thick), # placeholder
            peak_led=peak_led_coords,
            ticks=ticks, grid_lines=grid_lines, scale_labels=scale_labels
        )

    def get_dynamic_coords(self, current_val, peak_val, overload_factor, cfg, layout: LayoutResult):
        """Calculates coordinates for elements that change every frame."""
        def norm(v): return (v - cfg.min_val) / (cfg.max_val - cfg.min_val)
        
        pos = max(0, min(layout.base_len, norm(current_val) * layout.base_len))
        px_pos = max(0, min(layout.base_len, norm(peak_val) * layout.base_len))
        
        # Recalculate poly helper locally
        def get_poly(v_start, v_end, t_start, t_end):
            x1 = layout.bar_x + v_start
            x2 = layout.bar_x + v_end
            y1 = layout.bar_y + t_start
            y2 = layout.bar_y + t_end
            if cfg.rotation_angle == 0.0: return [x1, y1, x2, y2]
            if cfg.rotation_angle == 90.0:
                return [layout.bar_x + t_start, layout.bar_y + (layout.base_len - v_end),
                        layout.bar_x + t_end, layout.bar_y + (layout.base_len - v_start)]
            # Arbitrary
            cx, cy = layout.bar_x + (layout.base_len / 2), layout.bar_y + (layout.bar_thick / 2)
            points = [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]
            rad = math.radians(cfg.rotation_angle)
            c, s = math.cos(rad), math.sin(rad)
            res = []
            for px, py in points:
                tx, ty = px - cx, py - cy
                res.extend([cx + tx*c - ty*s, cy + tx*s + ty*c])
            return res

        # 1. Update Fills
        z1_end = min(pos, (cfg.middle_range - cfg.min_val) / (cfg.max_val - cfg.min_val) * layout.base_len)
        if cfg.fill_with_value:
            z1_end = pos
        
        z2_start = (cfg.middle_range - cfg.min_val) / (cfg.max_val - cfg.min_val) * layout.base_len
        z2_end = max(z2_start, min(pos, (cfg.upper_range - cfg.min_val) / (cfg.max_val - cfg.min_val) * layout.base_len))
        z3_start = (cfg.upper_range - cfg.min_val) / (cfg.max_val - cfg.min_val) * layout.base_len
        z3_end = max(z3_start, min(pos, layout.base_len))

        
        if not cfg.fill_with_value:
            z1_end, z2_end, z3_end = z2_start, z3_start, layout.base_len # full zones

        # 2. Indicator
        thick1, thick2 = 0, layout.bar_thick
        ext = layout.bar_thick * 0.15
        if cfg.scale_position in ["top", "left"]: thick1 -= ext
        if cfg.scale_position in ["bottom", "right"]: thick2 += ext
        
        # 3. Peak Flag
        flag_points = []
        if cfg.peak_flag:
            fs = 5
            if not cfg.is_vertical:
                tip_y = layout.bar_y + layout.bar_thick if cfg.scale_position == "bottom" else layout.bar_y
                tip_x = layout.bar_x + px_pos
                if cfg.scale_position == "bottom":
                    flag_points = [tip_x, tip_y, tip_x - fs/2, tip_y + fs, tip_x + fs/2, tip_y + fs]
                else:
                    flag_points = [tip_x, tip_y, tip_x - fs/2, tip_y - fs, tip_x + fs/2, tip_y - fs]
            else:
                tip_y = layout.bar_y + layout.base_len - px_pos
                if cfg.scale_position in ["bottom", "right"]:
                    tip_x = layout.bar_x + layout.bar_thick
                    flag_points = [tip_x, tip_y, tip_x + fs, tip_y - fs/2, tip_x + fs, tip_y + fs/2]
                else:
                    tip_x = layout.bar_x
                    flag_points = [tip_x, tip_y, tip_x - fs, tip_y - fs/2, tip_x - fs, tip_y + fs/2]

        return {
            "z1": get_poly(0, z1_end, 0, layout.bar_thick),
            "z2": get_poly(z2_start, z2_end, 0, layout.bar_thick),
            "z3": get_poly(z3_start, z3_end, 0, layout.bar_thick),
            "indicator": get_poly(pos - 2.5, pos + 2.5, thick1, thick2),
            "peak": get_poly(px_pos, px_pos, 0, layout.bar_thick),
            "peak_flag": flag_points
        }