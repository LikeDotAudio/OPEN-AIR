import time
import tkinter as tk
from workers.logger.logger import builder_logger
from .scale import ScaleDrawer
from .number import NumberDrawer
from .needle import NeedleDrawer
from .shadow import ShadowDrawer
from .peak import PeakDrawer
from .pivot import PivotDrawer
from ..meter_modifyer import MeterModifier
from ..cosmetics.geometry import BezelGeometry
from ..constants import SCALE_TICK_LENGTH, SCALE_SUB_TICK_LENGTH, SCALE_TEXT_OFFSET, NUMBER_FONT_FAMILY

# --- Standard Debug Logging Setup ---
BUILDER_DEBUG = True

class MeterRenderingEngine:
    """Handles the complex multi-layer rendering of needle-style VU meters."""

    @staticmethod
    def render(canvas, config, val1, val2, peak_on, center_x, center_y, full_redraw=False):
        if BUILDER_DEBUG and full_redraw: builder_logger.trace(f"🔄 Rendering full meter: {config.label}")
        
        if full_redraw:
            for tag in ["vu_static", "nextgen_background", "nextgen_foreground", "industrial_text"]: canvas.delete(tag)

        style_ovr = config.cosmetics.get("style_overrides", {})
        bezel_shape = style_ovr.get("bezel_shape", "").lower()
        bezel_width = int(style_ovr.get("bezel_width", 12))

        # Pivot offsets
        cx1, cy1 = center_x + config.pivot_offset_x, center_y - config.pivot_offset_y
        cx2, cy2 = center_x + config.pivot_offset_x_2, center_y - config.pivot_offset_y_2

        # 1. STATIC: Faceplate
        if full_redraw:
            if hasattr(canvas, 'panel_bg_image') and canvas.panel_bg_image:
                 canvas.tag_lower(canvas.create_image(0, 0, image=canvas.panel_bg_image, anchor="nw", tags="nextgen_background"))
            elif config.intended_bg and not config.is_transparent and "bezel_shape" not in style_ovr:
                from .visual_helpers import MeterVisualHelpers
                w, h = int(canvas.cget("width")), int(canvas.cget("height"))
                canvas.tag_lower(MeterVisualHelpers.draw_rounded_rect_poly(canvas, 0, 0, w, h, 20, config.intended_bg, tags=("vu_static", "nextgen_background")))

            if config.label and config.show_label:
                canvas.create_text(int(canvas.cget("width"))/2, 10, text=config.label, fill=config.widget_label_color, font=(NUMBER_FONT_FAMILY, config.font_size, "bold"), anchor="n", tags=("industrial_text", "vu_static"))

            if config.cosmetics:
                 cw, ch = int(canvas.cget("width")), int(canvas.cget("height"))
                 MeterModifier.draw_background_faceplate(canvas, center_x, center_y, cw, ch, config.cosmetics)
                 MeterModifier.draw_labels(canvas, center_x, center_y, config.cosmetics, current_value=val1)

        # 2. DYNAMIC: Geometry
        base_r = (config.size - config.scale_padding) / 2
        arc_r = base_r + (config.arc_radius_offset or 0)
        tick_r = base_r + (config.tick_radius_offset or 0)
        lab_r = base_r + (config.label_radius_offset or 0)
        
        tl = config.tick_length_override if config.tick_length_override is not None else SCALE_TICK_LENGTH
        stl = config.sub_tick_length_override if config.sub_tick_length_override is not None else SCALE_SUB_TICK_LENGTH
        nsf = config.needle_length_factor_override if config.needle_length_factor_override is not None else config.needle_scale

        ha = config.meter_viewable_angle / 2.0
        sang, eang = config.meter_center_angle + ha, config.meter_center_angle - ha
        ext = sang - eang

        pivots = [(cx1, cy1, val1, config.counter_clockwise)]
        if bezel_shape in ["stereo_diamond", "intersecting_overlay"] or config.meter_mode == "stereo":
            pivots.append((cx2, cy2, val2, not config.counter_clockwise if bezel_shape == "stereo_diamond" else config.counter_clockwise))

        for i, (px, py, val, ccw) in enumerate(pivots):
            if i > 0 and val is None: continue
            
            if full_redraw:
                t_vals = ScaleDrawer.draw_ticks(canvas, px, py, config.min_val, config.max_val, sang, eang, ext, base_r, config.curve_thickness, tl, stl, config.fg_color, config.ticks_visible, config.custom_ticks, config.tick_step, config.anchor_point, config.sub_ticks, config.sub_tick_style, ccw, tick_radius=tick_r)
                for item in canvas.find_withtag("vu_element"):
                    if not any(t.startswith("vu_needle") for t in canvas.gettags(item)): canvas.addtag_withtag("vu_static", item)

                NumberDrawer.draw_labels(canvas, px, py, t_vals, config.min_val, config.max_val, sang, eang, ext, base_r, SCALE_TEXT_OFFSET, config.scale_label_color, config.scale_numbers, config.label_overrides, ccw, label_radius=lab_r)
                for item in canvas.find_withtag("industrial_text"): canvas.addtag_withtag("vu_static", item)

                ScaleDrawer.draw_arcs(canvas, px, py, config.min_val, config.max_val, sang, eang, ext, base_r, config.curve_thickness, config.lower_colour, config.middle_colour, config.upper_colour, config.mid_range_start, config.red_zone_start, ccw, arc_radius=arc_r)
                for item in canvas.find_withtag("vu_element"):
                    if not any(t.startswith("vu_needle") for t in canvas.gettags(item)) and "vu_static" not in canvas.gettags(item): canvas.addtag_withtag("vu_static", item)

            # Peak & Needle
            vr = config.max_val - config.min_val
            norm_p = (config.red_zone_start - config.min_val) / vr if vr != 0 else 0
            p_ang = (eang + (norm_p * ext)) if ccw else (sang - (norm_p * ext))
            PeakDrawer.draw_peak_dot(canvas, px, py, p_ang, base_r, config.curve_thickness, peak_on, config.peak_flag, arc_radius=arc_r)

            ShadowDrawer.draw_shadow(canvas, px, py, val, config.min_val, config.max_val, sang, eang, ext, base_r, SCALE_TEXT_OFFSET, config.pointer_style if i==0 else config.pointer_style_2, config.needle_thickness if i==0 else config.needle_thickness_2, ccw, config.pivot_size, needle_scale=nsf, tag=f"vu_shadow_{i}")
            NeedleDrawer.draw_needle(canvas, px, py, val, config.min_val, config.max_val, sang, eang, ext, base_r, SCALE_TEXT_OFFSET, config.pointer_colour if i==0 else config.pointer_colour_2, config.pointer_style if i==0 else config.pointer_style_2, config.needle_thickness if i==0 else config.needle_thickness_2, ccw, config.pivot_size, needle_scale=nsf, tag=f"vu_needle_{i}")

            if full_redraw:
                PivotDrawer.draw_pivot(canvas, px, py, config.pivot_size, config.pivot_colour, config.secondary_color, config.fg_color)
                for item in canvas.find_withtag("vu_element"):
                    if not any(t.startswith("vu_needle") for t in canvas.gettags(item)) and "vu_static" not in canvas.gettags(item): canvas.addtag_withtag("vu_static", item)

        # 3. STATIC: Chassis
        if full_redraw:
            R, g_y, sk = BezelGeometry.get_scaling_params(int(canvas.cget("width")), int(canvas.cget("height")), bezel_shape, bezel_width)
            from ..constants import GEM_BEZEL_EXPANSION, GEM_BASE_HEIGHT, GEM_PEAK_HEIGHT
            if sk == "gem": by = center_y - ((GEM_BASE_HEIGHT * R * GEM_BEZEL_EXPANSION) + g_y)
            elif sk == "super_gem": by = center_y - (-(GEM_PEAK_HEIGHT * R * GEM_BEZEL_EXPANSION) + g_y)
            elif sk == "octagon": by = center_y - ((-0.923 * R * 1.4) + g_y)
            else: by = center_y - g_y
            
            if sk != "super_gem" and not (hasattr(canvas, 'panel_bg_image') and canvas.panel_bg_image) and not config.is_transparent:
                bg = canvas.cget("bg"); canvas.create_rectangle(0, by+1, int(canvas.cget("width")), int(canvas.cget("height")), fill=bg, outline=bg, tags="vu_static")
            
            if config.cosmetics:
                 cw, ch = int(canvas.cget("width")), int(canvas.cget("height"))
                 MeterModifier.draw_glass_layer(canvas, center_x, center_y, cw, ch, config.cosmetics)
                 MeterModifier.draw_foreground_overlay(canvas, center_x, center_y, cw, ch, config.cosmetics)

        # 4. Z-ORDER
        if full_redraw or not getattr(canvas, "_z_order_settled", False):
            for t in ["panel_bg_slice", "nextgen_background", "vu_shadow", "vu_element", "nextgen_foreground", "industrial_text"]:
                try: 
                    if t == "panel_bg_slice": canvas.tag_lower(t)
                    else: 
                        prev = ["panel_bg_slice", "nextgen_background", "vu_shadow", "vu_element", "nextgen_foreground"][ ["nextgen_background", "vu_shadow", "vu_element", "nextgen_foreground", "industrial_text"].index(t) ]
                        canvas.tag_raise(t, prev)
                except: pass
            canvas._z_order_settled = True
