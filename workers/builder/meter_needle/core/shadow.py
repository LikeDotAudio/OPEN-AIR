import tkinter as tk
import math

class ShadowDrawer:
    """
    Draws a cast shadow for the needle with perspective.
    Simulates the needle rising off the faceplate (0 offset at pivot, max offset at tip).
    """
    @staticmethod
    def draw_shadow(canvas, center_x, center_y, 
                    val, min_val, max_val,
                    start_angle_deg, end_angle_deg, extent_deg,
                    main_arc_radius, text_offset_from_arc,
                    style, thick, counter_clockwise, pivot_size,
                    needle_scale=1.0, tag="vu_shadow"):
        """
        Draws or updates the shadow. Uses coords() if the tag already exists for performance.
        """
        # Light Source: Top-Left
        # Shadow Direction: Bottom-Right
        MAX_SHADOW_X = 6
        MAX_SHADOW_Y = 6
        fill_color = "#222222"
        stipple_pattern = "gray25" 

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

        def get_shadow_pt(px, py):
            dist = math.sqrt((px - center_x)**2 + (py - center_y)**2)
            factor = min(1.0, max(0.0, dist / needle_total_len))
            sx = px + (MAX_SHADOW_X * factor)
            sy = py + (MAX_SHADOW_Y * factor)
            return sx, sy

        tip_x = center_x + needle_total_len * math.cos(needle_angle_rad)
        tip_y = center_y - needle_total_len * math.sin(needle_angle_rad)
        
        existing = canvas.find_withtag(tag)
        
        # ⚡ OPTIMIZATION: Update coords if tag exists for simple styles
        if style in ["line", "baton", "taper", "knife-edge"] and existing:
            if style == "line":
                scx, scy = get_shadow_pt(center_x, center_y)
                stip_x, stip_y = get_shadow_pt(tip_x, tip_y)
                canvas.coords(tag, scx, scy, stip_x, stip_y)
            elif style == "taper" or style == "knife-edge":
                perp_angle_rad = needle_angle_rad + (math.pi / 2)
                base_radius = (pivot_size / 2.0) if style == "taper" else (thick * 1.5)
                bx1 = center_x + base_radius * math.cos(perp_angle_rad)
                by1 = center_y - base_radius * math.sin(perp_angle_rad)
                bx2 = center_x - base_radius * math.cos(perp_angle_rad)
                by2 = center_y + base_radius * math.sin(perp_angle_rad)
                sbx1, sby1 = get_shadow_pt(bx1, by1)
                sbx2, sby2 = get_shadow_pt(bx2, by2)
                stip_x, stip_y = get_shadow_pt(tip_x, tip_y)
                canvas.coords(tag, sbx1, sby1, stip_x, stip_y, sbx2, sby2)
            elif style == "baton":
                perp_angle_rad = needle_angle_rad + (math.pi / 2)
                ox, oy = (thick / 2.0) * math.cos(perp_angle_rad), (thick / 2.0) * math.sin(perp_angle_rad)
                sc1 = get_shadow_pt(center_x + ox, center_y - oy)
                sc2 = get_shadow_pt(tip_x + ox, tip_y - oy)
                sc3 = get_shadow_pt(tip_x - ox, tip_y + oy)
                sc4 = get_shadow_pt(center_x - ox, center_y + oy)
                canvas.coords(tag, sc1[0], sc1[1], sc2[0], sc2[1], sc3[0], sc3[1], sc4[0], sc4[1])
            return

        if existing:
            canvas.delete(tag)

        if style in ["teardrop", "spade"]:
            d1, d2 = needle_total_len * 0.75, needle_total_len * 0.875
            p1x, p1y = center_x + d1 * math.cos(needle_angle_rad), center_y - d1 * math.sin(needle_angle_rad)
            p2x, p2y = center_x + d2 * math.cos(needle_angle_rad), center_y - d2 * math.sin(needle_angle_rad)
            bulb_w, perp_angle = thick * 2.5, needle_angle_rad + (math.pi / 2)
            bx, by = center_x + (d1 - thick) * math.cos(needle_angle_rad), center_y - (d1 - thick) * math.sin(needle_angle_rad)
            mid_dist = (d1 + d2) / 2
            mx, my = center_x + mid_dist * math.cos(needle_angle_rad), center_y - mid_dist * math.sin(needle_angle_rad)
            s1x, s1y = mx + bulb_w * math.cos(perp_angle), my - bulb_w * math.sin(perp_angle)
            s2x, s2y = mx - bulb_w * math.cos(perp_angle), my + bulb_w * math.sin(perp_angle)
            
            scx, scy = get_shadow_pt(center_x, center_y)
            sp1x, sp1y = get_shadow_pt(p1x, p1y)
            sbx, sby = get_shadow_pt(bx, by)
            ss1x, ss1y = get_shadow_pt(s1x, s1y)
            sp2x, sp2y = get_shadow_pt(p2x, p2y)
            ss2x, ss2y = get_shadow_pt(s2x, s2y)
            stip_x, stip_y = get_shadow_pt(tip_x, tip_y)

            canvas.create_line(scx, scy, sp1x, sp1y, width=thick, fill=fill_color, capstyle=tk.ROUND, tags=(tag, "vu_shadow"), stipple=stipple_pattern)
            canvas.create_polygon([sbx, sby, ss1x, ss1y, sp2x, sp2y, ss2x, ss2y], fill=fill_color, outline="", smooth=True, tags=(tag, "vu_shadow"), stipple=stipple_pattern)
            canvas.create_line(sp2x, sp2y, stip_x, stip_y, width=thick, fill=fill_color, capstyle=tk.ROUND, tags=(tag, "vu_shadow"), stipple=stipple_pattern)

        elif style == "knife-edge":
            perp_angle_rad = needle_angle_rad + (math.pi / 2)
            base_radius = thick * 1.5
            bx1, by1 = center_x + base_radius * math.cos(perp_angle_rad), center_y - base_radius * math.sin(perp_angle_rad)
            bx2, by2 = center_x - base_radius * math.cos(perp_angle_rad), center_y + base_radius * math.sin(perp_angle_rad)
            sbx1, sby1 = get_shadow_pt(bx1, by1)
            sbx2, sby2 = get_shadow_pt(bx2, by2)
            stip_x, stip_y = get_shadow_pt(tip_x, tip_y)
            canvas.create_polygon([sbx1, sby1, stip_x, stip_y, sbx2, sby2], fill=fill_color, outline="", smooth=False, tags=(tag, "vu_shadow"), stipple=stipple_pattern)

        elif style == "baton":
            perp_angle_rad = needle_angle_rad + (math.pi / 2)
            ox, oy = (thick / 2.0) * math.cos(perp_angle_rad), (thick / 2.0) * math.sin(perp_angle_rad)
            sc1 = get_shadow_pt(center_x + ox, center_y - oy)
            sc2 = get_shadow_pt(tip_x + ox, tip_y - oy)
            sc3 = get_shadow_pt(tip_x - ox, tip_y + oy)
            sc4 = get_shadow_pt(center_x - ox, center_y + oy)
            canvas.create_polygon([sc1[0], sc1[1], sc2[0], sc2[1], sc3[0], sc3[1], sc4[0], sc4[1]], fill=fill_color, outline="", tags=(tag, "vu_shadow"), stipple=stipple_pattern)

        elif style == "taper":
            perp_angle_rad = needle_angle_rad + (math.pi / 2)
            base_radius = pivot_size / 2.0
            bx1, by1 = center_x + base_radius * math.cos(perp_angle_rad), center_y - base_radius * math.sin(perp_angle_rad)
            bx2, by2 = center_x - base_radius * math.cos(perp_angle_rad), center_y + base_radius * math.sin(perp_angle_rad)
            sbx1, sby1 = get_shadow_pt(bx1, by1)
            sbx2, sby2 = get_shadow_pt(bx2, by2)
            stip_x, stip_y = get_shadow_pt(tip_x, tip_y)
            canvas.create_polygon([sbx1, sby1, stip_x, stip_y, sbx2, sby2], fill=fill_color, outline="", smooth=False, tags=(tag, "vu_shadow"), stipple=stipple_pattern)
            
        else:
            scx, scy = get_shadow_pt(center_x, center_y)
            stip_x, stip_y = get_shadow_pt(tip_x, tip_y)
            canvas.create_line(scx, scy, stip_x, stip_y, width=thick, fill=fill_color, capstyle=tk.ROUND, tags=(tag, "vu_shadow"), stipple=stipple_pattern)
