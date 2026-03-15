import tkinter as tk
import math

class NeedleDrawer:
    @staticmethod
    def draw_needle(canvas, center_x, center_y, 
                    val, min_val, max_val,
                    start_angle_deg, end_angle_deg, extent_deg,
                    main_arc_radius, text_offset_from_arc,
                    color, style, thick, counter_clockwise, pivot_size,
                    needle_scale=1.0, tag="vu_needle"):
        """
        Draws or updates the needle. Uses coords() if the tag already exists for performance.
        """
        if val < min_val: val = min_val
        if val > max_val: val = max_val

        range_val = max_val - min_val
        norm_val = (val - min_val) / range_val if range_val != 0 else 0

        if counter_clockwise:
            needle_angle_deg = end_angle_deg + (norm_val * extent_deg)
        else:
            needle_angle_deg = start_angle_deg - (norm_val * extent_deg)
            
        needle_angle_rad = math.radians(needle_angle_deg)
        needle_total_len = (main_arc_radius + text_offset_from_arc - 2) * needle_scale

        tip_x = center_x + needle_total_len * math.cos(needle_angle_rad)
        tip_y = center_y - needle_total_len * math.sin(needle_angle_rad)

        # ⚡ OPTIMIZATION: Check if we can just update coordinates
        existing = canvas.find_withtag(tag)
        
        # Helper to decide if we can use simple coords update
        # Complex styles like teardrop or hollow-diamond use multiple items and are harder to 'coords' update
        # without significant refactoring. We'll optimize 'line', 'baton', 'taper', 'knife-edge' first.
        
        if style in ["line", "baton", "taper", "knife-edge"] and existing:
            if style == "line":
                canvas.coords(tag, center_x, center_y, tip_x, tip_y)
            elif style == "taper" or style == "knife-edge":
                perp_angle_rad = needle_angle_rad + (math.pi / 2)
                base_radius = (pivot_size / 2.0) if style == "taper" else (thick * 1.5)
                bx1 = center_x + base_radius * math.cos(perp_angle_rad)
                by1 = center_y - base_radius * math.sin(perp_angle_rad)
                bx2 = center_x - base_radius * math.cos(perp_angle_rad)
                by2 = center_y + base_radius * math.sin(perp_angle_rad)
                canvas.coords(tag, bx1, by1, tip_x, tip_y, bx2, by2)
            elif style == "baton":
                perp_angle_rad = needle_angle_rad + (math.pi / 2)
                off_x = (thick / 2.0) * math.cos(perp_angle_rad)
                off_y = (thick / 2.0) * math.sin(perp_angle_rad)
                canvas.coords(tag, center_x + off_x, center_y - off_y, tip_x + off_x, tip_y - off_y,
                                   tip_x - off_x, tip_y + off_y, center_x - off_x, center_y + off_y)
            return

        # If not simple update or doesn't exist, delete old and create new
        if existing:
            canvas.delete(tag)

        if style in ["teardrop", "spade"]:
            d1, d2 = needle_total_len * 0.75, needle_total_len * 0.875
            p1x, p1y = center_x + d1 * math.cos(needle_angle_rad), center_y - d1 * math.sin(needle_angle_rad)
            p2x, p2y = center_x + d2 * math.cos(needle_angle_rad), center_y - d2 * math.sin(needle_angle_rad)
            
            # Line 1
            canvas.create_line(center_x, center_y, p1x, p1y, width=thick, fill=color, capstyle=tk.ROUND, tags=(tag, "vu_element"))
            
            # Bulb
            bulb_w = thick * 2.5
            perp_angle = needle_angle_rad + (math.pi / 2)
            bx, by = center_x + (d1 - thick) * math.cos(needle_angle_rad), center_y - (d1 - thick) * math.sin(needle_angle_rad)
            mid_dist = (d1 + d2) / 2
            mx, my = center_x + mid_dist * math.cos(needle_angle_rad), center_y - mid_dist * math.sin(needle_angle_rad)
            s1x, s1y = mx + bulb_w * math.cos(perp_angle), my - bulb_w * math.sin(perp_angle)
            s2x, s2y = mx - bulb_w * math.cos(perp_angle), my + bulb_w * math.sin(perp_angle)
            
            canvas.create_polygon([bx, by, s1x, s1y, p2x, p2y, s2x, s2y], fill=color, outline=color, smooth=True, tags=(tag, "vu_element"))
            
            # Tip
            canvas.create_line(p2x, p2y, tip_x, tip_y, width=thick, fill=color, capstyle=tk.ROUND, tags=(tag, "vu_element"))

        elif style == "knife-edge":
            perp_angle_rad = needle_angle_rad + (math.pi / 2)
            base_radius = thick * 1.5
            bx1, by1 = center_x + base_radius * math.cos(perp_angle_rad), center_y - base_radius * math.sin(perp_angle_rad)
            bx2, by2 = center_x - base_radius * math.cos(perp_angle_rad), center_y + base_radius * math.sin(perp_angle_rad)
            canvas.create_polygon([bx1, by1, tip_x, tip_y, bx2, by2], fill=color, outline=color, tags=(tag, "vu_element"))

        elif style == "baton":
            perp_angle_rad = needle_angle_rad + (math.pi / 2)
            off_x, off_y = (thick / 2.0) * math.cos(perp_angle_rad), (thick / 2.0) * math.sin(perp_angle_rad)
            canvas.create_polygon([center_x + off_x, center_y - off_y, tip_x + off_x, tip_y - off_y,
                                   tip_x - off_x, tip_y + off_y, center_x - off_x, center_y + off_y], 
                                   fill=color, outline=color, tags=(tag, "vu_element"))

        elif style == "hollow-diamond":
            d_mid, d_start = needle_total_len * 0.8, needle_total_len * 0.6
            perp_angle, width = needle_angle_rad + (math.pi / 2), thick * 4
            mx, my = center_x + d_mid * math.cos(needle_angle_rad), center_y - d_mid * math.sin(needle_angle_rad)
            sx, sy = center_x + d_start * math.cos(needle_angle_rad), center_y - d_start * math.sin(needle_angle_rad)
            
            p1x, p1y = mx + width * math.cos(perp_angle), my - width * math.sin(perp_angle)
            p2x, p2y = mx - width * math.cos(perp_angle), my + width * math.sin(perp_angle)
            canvas.create_polygon([sx, sy, p1x, p1y, tip_x, tip_y, p2x, p2y], fill=color, outline=color, tags=(tag, "vu_element"))
            
            bg, i_width, i_start, i_tip_dist = canvas.cget("bg"), width * 0.6, d_start + (thick * 2), needle_total_len - (thick * 2)
            itx, ity = center_x + i_tip_dist * math.cos(needle_angle_rad), center_y - i_tip_dist * math.sin(needle_angle_rad)
            ip1x, ip1y = mx + i_width * math.cos(perp_angle), my - i_width * math.sin(perp_angle)
            ip2x, ip2y = mx - i_width * math.cos(perp_angle), my + i_width * math.sin(perp_angle)
            # Use 'vu_element' for cutout so it clears correctly
            canvas.create_polygon([sx + (thick*2)*math.cos(needle_angle_rad), sy - (thick*2)*math.sin(needle_angle_rad), 
                                   ip1x, ip1y, itx, ity, ip2x, ip2y], fill=bg, outline=bg, tags=(tag, "vu_element"))
            canvas.create_line(center_x, center_y, sx, sy, width=thick, fill=color, tags=(tag, "vu_element"))

        elif style == "taper":
            perp_angle_rad = needle_angle_rad + (math.pi / 2)
            base_radius = pivot_size / 2.0
            bx1, by1 = center_x + base_radius * math.cos(perp_angle_rad), center_y - base_radius * math.sin(perp_angle_rad)
            bx2, by2 = center_x - base_radius * math.cos(perp_angle_rad), center_y + base_radius * math.sin(perp_angle_rad)
            canvas.create_polygon([bx1, by1, tip_x, tip_y, bx2, by2], fill=color, outline=color, tags=(tag, "vu_element"))
            
        else:
            canvas.create_line(center_x, center_y, tip_x, tip_y, width=thick, fill=color, capstyle=tk.ROUND, tags=(tag, "vu_element"))
