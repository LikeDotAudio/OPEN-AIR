# Core/shadow.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import math
import tkinter as tk

from .needle import NeedleConfig

try:
    from oaRustCore.oa_needle_geometry_rs import NeedleGeometry
    needle_geo_rs = NeedleGeometry()
except ImportError:
    needle_geo_rs = None

class ShadowDrawer:
    """
    Draws a cast shadow for the needle with perspective.
    Simulates the needle rising off the faceplate (0 offset at pivot, max offset at tip).
    """
    MAX_SHADOW_X = 6
    MAX_SHADOW_Y = 6
    FILL_COLOR = "#222222"
    STIPPLE_PATTERN = "gray25"

    @staticmethod
    def draw_shadow(canvas, center_x, center_y,
                    value, min_val, max_val,
                    start_angle_deg, end_angle_deg, extent_deg,
                    main_arc_radius, text_offset_from_arc,
                    style, thick, counter_clockwise, pivot_size,
                    needle_scale=1.0, tag="vu_shadow"):
        """Legacy wrapper for draw_with_config."""
        config = NeedleConfig(
            value=value, min_val=min_val, max_val=max_val,
            start_angle_deg=start_angle_deg, end_angle_deg=end_angle_deg, extent_deg=extent_deg,
            main_arc_radius=main_arc_radius, text_offset_from_arc=text_offset_from_arc,
            color=ShadowDrawer.FILL_COLOR, style=style, thick=thick,
            counter_clockwise=counter_clockwise, pivot_size=pivot_size,
            needle_scale=needle_scale, tag=tag
        )
        return ShadowDrawer.draw_with_config(canvas, center_x, center_y, config)

    @staticmethod
    def draw_with_config(canvas, cx, cy, config: NeedleConfig):
        """Unified entry point for drawing the shadow."""
        if needle_geo_rs:
            # ⚡ OFF-LOAD to RUST
            geo = needle_geo_rs.calculate_shadow_geometry(cx, cy, config.__dict__)

            # 2. Try Optimization (Update existing)
            existing = canvas.find_withtag(config.tag)
            if existing:
                g_type = geo.get("type")
                if g_type == "teardrop":
                    # Teardrop has 3 parts in Python, but we use a single tag
                    # If we find 3 items with this tag, we can update them
                    if len(existing) == 3:
                        canvas.coords(existing[0], *geo["line1"])
                        canvas.coords(existing[1], *geo["poly"])
                        canvas.coords(existing[2], *geo["line2"])
                        return
                elif g_type in ["polygon", "line"] and len(existing) == 1:
                    canvas.coords(existing[0], *geo["coords"])
                    return

            # 3. Full redraw
            if existing:
                canvas.delete(config.tag)

            g_type = geo.get("type")
            if g_type == "teardrop":
                canvas.create_line(*geo["line1"], width=config.thick, fill=ShadowDrawer.FILL_COLOR,
                                   capstyle=tk.ROUND, tags=(config.tag, "vu_shadow"), stipple=ShadowDrawer.STIPPLE_PATTERN)
                canvas.create_polygon(geo["poly"], fill=ShadowDrawer.FILL_COLOR,
                                       outline="", smooth=True, tags=(config.tag, "vu_shadow"), stipple=ShadowDrawer.STIPPLE_PATTERN)
                canvas.create_line(*geo["line2"], width=config.thick, fill=ShadowDrawer.FILL_COLOR,
                                   capstyle=tk.ROUND, tags=(config.tag, "vu_shadow"), stipple=ShadowDrawer.STIPPLE_PATTERN)
            elif g_type == "polygon":
                canvas.create_polygon(geo["coords"], fill=ShadowDrawer.FILL_COLOR,
                                       outline="", tags=(config.tag, "vu_shadow"), stipple=ShadowDrawer.STIPPLE_PATTERN)
            else: # line
                canvas.create_line(*geo["coords"], width=config.thick, fill=ShadowDrawer.FILL_COLOR,
                                   capstyle=tk.ROUND, tags=(config.tag, "vu_shadow"), stipple=ShadowDrawer.STIPPLE_PATTERN)
            return

        # 1. Prepare values
        value = max(min(config.value, config.max_val), config.min_val)
        range_val = config.max_val - config.min_val
        norm_val = (value - config.min_val) / range_val if range_val != 0 else 0

        angle_deg = config.end_angle_deg + (norm_val * config.extent_deg) if config.counter_clockwise \
                    else config.start_angle_deg - (norm_val * config.extent_deg)

        angle_rad = math.radians(angle_deg)
        length = (config.main_arc_radius + config.text_offset_from_arc - 2) * config.needle_scale
        tip_x, tip_y = cx + length * math.cos(angle_rad), cy - length * math.sin(angle_rad)

        # 2. Try Optimization
        if ShadowDrawer._try_update_existing(canvas, cx, cy, tip_x, tip_y, angle_rad, length, config):
            return

        # 3. Full redraw
        existing = canvas.find_withtag(config.tag)
        if existing:
            canvas.delete(config.tag)

        handlers = {
            "teardrop": ShadowDrawer._draw_teardrop,
            "spade": ShadowDrawer._draw_teardrop,
            "knife-edge": ShadowDrawer._draw_knife_edge,
            "baton": ShadowDrawer._draw_baton,
            "taper": ShadowDrawer._draw_taper,
        }

        handler = handlers.get(config.style, ShadowDrawer._draw_line)
        handler(canvas, cx, cy, tip_x, tip_y, angle_rad, length, config)

    @staticmethod
    def _get_shadow_pt(px, py, cx, cy, length):
        """Calculates shadow projection with distance-based offset."""
        dist = math.sqrt((px - cx)**2 + (py - cy)**2)
        factor = min(1.0, max(0.0, dist / length)) if length != 0 else 0
        sx = px + (ShadowDrawer.MAX_SHADOW_X * factor)
        sy = py + (ShadowDrawer.MAX_SHADOW_Y * factor)
        return sx, sy

    @staticmethod
    def _try_update_existing(canvas, cx, cy, tip_x, tip_y, angle_rad, length, config):
        """Attempts to update existing shadow coordinates."""
        existing = canvas.find_withtag(config.tag)
        if not existing or config.style not in ["line", "baton", "taper", "knife-edge"]:
            return False

        if config.style == "line":
            scx, scy = ShadowDrawer._get_shadow_pt(cx, cy, cx, cy, length)
            stip_x, stip_y = ShadowDrawer._get_shadow_pt(tip_x, tip_y, cx, cy, length)
            canvas.coords(config.tag, scx, scy, stip_x, stip_y)
        elif config.style in ["taper", "knife-edge"]:
            perp_angle = angle_rad + (math.pi / 2)
            base_rad = (config.pivot_size / 2.0) if config.style == "taper" else (config.thick * 1.5)
            bx1, by1 = cx + base_rad * math.cos(perp_angle), cy - base_rad * math.sin(perp_angle)
            bx2, by2 = cx - base_rad * math.cos(perp_angle), cy + base_rad * math.sin(perp_angle)
            sbx1, sby1 = ShadowDrawer._get_shadow_pt(bx1, by1, cx, cy, length)
            sbx2, sby2 = ShadowDrawer._get_shadow_pt(bx2, by2, cx, cy, length)
            stip_x, stip_y = ShadowDrawer._get_shadow_pt(tip_x, tip_y, cx, cy, length)
            canvas.coords(config.tag, sbx1, sby1, stip_x, stip_y, sbx2, sby2)
        elif config.style == "baton":
            perp_angle = angle_rad + (math.pi / 2)
            ox, oy = (config.thick / 2.0) * math.cos(perp_angle), (config.thick / 2.0) * math.sin(perp_angle)
            sc1 = ShadowDrawer._get_shadow_pt(cx + ox, cy - oy, cx, cy, length)
            sc2 = ShadowDrawer._get_shadow_pt(tip_x + ox, tip_y - oy, cx, cy, length)
            sc3 = ShadowDrawer._get_shadow_pt(tip_x - ox, tip_y + oy, cx, cy, length)
            sc4 = ShadowDrawer._get_shadow_pt(cx - ox, cy + oy, cx, cy, length)
            canvas.coords(config.tag, sc1[0], sc1[1], sc2[0], sc2[1], sc3[0], sc3[1], sc4[0], sc4[1])
        return True

    @staticmethod
    def _draw_line(canvas, cx, cy, tip_x, tip_y, angle_rad, length, config):
        scx, scy = ShadowDrawer._get_shadow_pt(cx, cy, cx, cy, length)
        stip_x, stip_y = ShadowDrawer._get_shadow_pt(tip_x, tip_y, cx, cy, length)
        canvas.create_line(scx, scy, stip_x, stip_y, width=config.thick, fill=ShadowDrawer.FILL_COLOR,
                           capstyle=tk.ROUND, tags=(config.tag, "vu_shadow"), stipple=ShadowDrawer.STIPPLE_PATTERN)

    @staticmethod
    def _draw_taper(canvas, cx, cy, tip_x, tip_y, angle_rad, length, config):
        perp_angle = angle_rad + (math.pi / 2)
        base_rad = config.pivot_size / 2.0
        bx1, by1 = cx + base_rad * math.cos(perp_angle), cy - base_rad * math.sin(perp_angle)
        bx2, by2 = cx - base_rad * math.cos(perp_angle), cy + base_rad * math.sin(perp_angle)
        sbx1, sby1 = ShadowDrawer._get_shadow_pt(bx1, by1, cx, cy, length)
        sbx2, sby2 = ShadowDrawer._get_shadow_pt(bx2, by2, cx, cy, length)
        stip_x, stip_y = ShadowDrawer._get_shadow_pt(tip_x, tip_y, cx, cy, length)
        canvas.create_polygon([sbx1, sby1, stip_x, stip_y, sbx2, sby2], fill=ShadowDrawer.FILL_COLOR,
                               outline="", tags=(config.tag, "vu_shadow"), stipple=ShadowDrawer.STIPPLE_PATTERN)

    @staticmethod
    def _draw_knife_edge(canvas, cx, cy, tip_x, tip_y, angle_rad, length, config):
        perp_angle = angle_rad + (math.pi / 2)
        base_rad = config.thick * 1.5
        bx1, by1 = cx + base_rad * math.cos(perp_angle), cy - base_rad * math.sin(perp_angle)
        bx2, by2 = cx - base_rad * math.cos(perp_angle), cy + base_rad * math.sin(perp_angle)
        sbx1, sby1 = ShadowDrawer._get_shadow_pt(bx1, by1, cx, cy, length)
        sbx2, sby2 = ShadowDrawer._get_shadow_pt(bx2, by2, cx, cy, length)
        stip_x, stip_y = ShadowDrawer._get_shadow_pt(tip_x, tip_y, cx, cy, length)
        canvas.create_polygon([sbx1, sby1, stip_x, stip_y, sbx2, sby2], fill=ShadowDrawer.FILL_COLOR,
                               outline="", tags=(config.tag, "vu_shadow"), stipple=ShadowDrawer.STIPPLE_PATTERN)

    @staticmethod
    def _draw_baton(canvas, cx, cy, tip_x, tip_y, angle_rad, length, config):
        perp_angle = angle_rad + (math.pi / 2)
        ox, oy = (config.thick / 2.0) * math.cos(perp_angle), (config.thick / 2.0) * math.sin(perp_angle)
        sc1 = ShadowDrawer._get_shadow_pt(cx + ox, cy - oy, cx, cy, length)
        sc2 = ShadowDrawer._get_shadow_pt(tip_x + ox, tip_y - oy, cx, cy, length)
        sc3 = ShadowDrawer._get_shadow_pt(tip_x - ox, tip_y + oy, cx, cy, length)
        sc4 = ShadowDrawer._get_shadow_pt(cx - ox, cy + oy, cx, cy, length)
        canvas.create_polygon([sc1[0], sc1[1], sc2[0], sc2[1], sc3[0], sc3[1], sc4[0], sc4[1]],
                               fill=ShadowDrawer.FILL_COLOR, outline="", tags=(config.tag, "vu_shadow"), stipple=ShadowDrawer.STIPPLE_PATTERN)

    @staticmethod
    def _draw_teardrop(canvas, cx, cy, tip_x, tip_y, angle_rad, length, config):
        d1, d2 = length * 0.75, length * 0.875
        p1x, p1y = cx + d1 * math.cos(angle_rad), cy - d1 * math.sin(angle_rad)
        p2x, p2y = cx + d2 * math.cos(angle_rad), cy - d2 * math.sin(angle_rad)
        bulb_w, perp_angle = config.thick * 2.5, angle_rad + (math.pi / 2)
        bx, by = cx + (d1 - config.thick) * math.cos(angle_rad), cy - (d1 - config.thick) * math.sin(angle_rad)
        mid_dist = (d1 + d2) / 2
        mx, my = cx + mid_dist * math.cos(angle_rad), cy - mid_dist * math.sin(angle_rad)
        s1x, s1y = mx + bulb_w * math.cos(perp_angle), my - bulb_w * math.sin(perp_angle)
        s2x, s2y = mx - bulb_w * math.cos(perp_angle), my + bulb_w * math.sin(perp_angle)

        scx, scy = ShadowDrawer._get_shadow_pt(cx, cy, cx, cy, length)
        sp1x, sp1y = ShadowDrawer._get_shadow_pt(p1x, p1y, cx, cy, length)
        sbx, sby = ShadowDrawer._get_shadow_pt(bx, by, cx, cy, length)
        ss1x, ss1y = ShadowDrawer._get_shadow_pt(s1x, s1y, cx, cy, length)
        sp2x, sp2y = ShadowDrawer._get_shadow_pt(p2x, p2y, cx, cy, length)
        ss2x, ss2y = ShadowDrawer._get_shadow_pt(s2x, s2y, cx, cy, length)
        stip_x, stip_y = ShadowDrawer._get_shadow_pt(tip_x, tip_y, cx, cy, length)

        canvas.create_line(scx, scy, sp1x, sp1y, width=config.thick, fill=ShadowDrawer.FILL_COLOR,
                           capstyle=tk.ROUND, tags=(config.tag, "vu_shadow"), stipple=ShadowDrawer.STIPPLE_PATTERN)
        canvas.create_polygon([sbx, sby, ss1x, ss1y, sp2x, sp2y, ss2x, ss2y], fill=ShadowDrawer.FILL_COLOR,
                               outline="", smooth=True, tags=(config.tag, "vu_shadow"), stipple=ShadowDrawer.STIPPLE_PATTERN)
        canvas.create_line(sp2x, sp2y, stip_x, stip_y, width=config.thick, fill=ShadowDrawer.FILL_COLOR,
                           capstyle=tk.ROUND, tags=(config.tag, "vu_shadow"), stipple=ShadowDrawer.STIPPLE_PATTERN)
