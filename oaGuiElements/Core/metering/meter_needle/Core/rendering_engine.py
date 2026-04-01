# Core/rendering_engine.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import time
from oaLogging.Methods.matrix_gate import matrix_log
import inspect
import tkinter as tk
from dataclasses import dataclass
from typing import Optional, List, Tuple

from oaLogging.Core.logger import builder_logger
from oaLogging.Methods.matrix_gate import is_debug_allowed
BUILDER_DEBUG = is_debug_allowed(system="UI", element="GUI_BUILDER")

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

@dataclass
class RenderContext:
    """Encapsulates geometric and configuration data for the rendering pipeline."""
    config: any
    cx: float
    cy: float
    base_r: float
    arc_r: float
    tick_r: float
    lab_r: float
    sang: float
    eang: float
    ext: float
    tl: float
    stl: float
    nsf: float
    style_ovr: dict
    bezel_shape: str
    bezel_width: int

    @classmethod
    def from_config(cls, config, center_x, center_y):
        style_ovr = config.cosmetics.get("style_overrides", {})
        bezel_shape = style_ovr.get("bezel_shape", "").lower()
        bezel_width = int(style_ovr.get("bezel_width", 12))

        base_r = (config.size - config.scale_padding) / 2
        ha = config.meter_viewable_angle / 2.0
        sang, eang = config.meter_center_angle + ha, config.meter_center_angle - ha

        return cls(
            config=config, cx=center_x, cy=center_y,
            base_r=base_r,
            arc_r=base_r + (config.arc_radius_offset or 0),
            tick_r=base_r + (config.tick_radius_offset or 0),
            lab_r=base_r + (config.label_radius_offset or 0),
            sang=sang, eang=eang, ext=sang - eang,
            tl=config.tick_length_override if config.tick_length_override is not None else SCALE_TICK_LENGTH,
            stl=config.sub_tick_length_override if config.sub_tick_length_override is not None else SCALE_SUB_TICK_LENGTH,
            nsf=config.needle_length_factor_override if config.needle_length_factor_override is not None else config.needle_scale,
            style_ovr=style_ovr, bezel_shape=bezel_shape, bezel_width=bezel_width
        )

class MeterRenderingEngine:
    """Handles the complex multi-layer rendering of needle-style VU meters."""

    @staticmethod
    def render(canvas, config, val1, val2, peak_on, center_x, center_y, full_redraw=False):
        if BUILDER_DEBUG and full_redraw: 
            matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🔄 Rendering full meter: {config.label}", level="TRACE")
        
        ctx = RenderContext.from_config(config, center_x, center_y)

        if full_redraw:
            MeterRenderingEngine._clear_layers(canvas)
            MeterRenderingEngine._draw_static_faceplate(canvas, ctx, val1)

        MeterRenderingEngine._draw_meter_geometry(canvas, ctx, val1, val2, peak_on, full_redraw)

        if full_redraw:
            MeterRenderingEngine._draw_static_chassis(canvas, ctx)

        if full_redraw or not getattr(canvas, "_z_order_settled", False):
            MeterRenderingEngine._finalize_z_order(canvas)

    @staticmethod
    def _clear_layers(canvas):
        """Removes existing layers before a full redraw."""
        for tag in ["vu_static", "nextgen_background", "nextgen_foreground", "industrial_text"]:
            canvas.delete(tag)

    @staticmethod
    def _draw_static_faceplate(canvas, ctx, val1):
        """Draws the background faceplate and labels."""
        config = ctx.config
        cw, ch = int(canvas.cget("width")), int(canvas.cget("height"))

        # Background Image or Rounded Rect
        if hasattr(canvas, 'panel_bg_image') and canvas.panel_bg_image:
             canvas.tag_lower(canvas.create_image(0, 0, image=canvas.panel_bg_image, anchor="nw", tags="nextgen_background"))
        elif config.intended_bg and not config.is_transparent and "bezel_shape" not in ctx.style_ovr:
            from .visual_helpers import MeterVisualHelpers
            canvas.tag_lower(MeterVisualHelpers.draw_rounded_rect_poly(canvas, 0, 0, cw, ch, 20, config.intended_bg, tags=("vu_static", "nextgen_background")))

        # Main Label
        if config.label and config.show_label:
            canvas.create_text(cw/2, 10, text=config.label, fill=config.widget_label_color, 
                               font=(NUMBER_FONT_FAMILY, config.font_size, "bold"), anchor="n", tags=("industrial_text", "vu_static"))

        # Modifier faceplate elements
        if config.cosmetics:
             MeterModifier.draw_background_faceplate(canvas, ctx.cx, ctx.cy, cw, ch, config.cosmetics)
             MeterModifier.draw_labels(canvas, ctx.cx, ctx.cy, config.cosmetics, current_value=val1)

    @staticmethod
    def _draw_meter_geometry(canvas, ctx, val1, val2, peak_on, full_redraw):
        """Draws ticks, arcs, peaks, and needles for all pivots."""
        config = ctx.config
        pivots = MeterRenderingEngine._get_pivots(ctx, val1, val2)

        for i, (px, py, val, ccw) in enumerate(pivots):
            if i > 0 and val is None: continue
            
            if full_redraw:
                # 1. Ticks & Numbers
                t_vals = ScaleDrawer.draw_ticks(canvas, px, py, config.min_val, config.max_val, ctx.sang, ctx.eang, ctx.ext, ctx.base_r, config.curve_thickness, ctx.tl, ctx.stl, config.fg_color, config.ticks_visible, config.custom_ticks, config.tick_step, config.anchor_point, config.sub_ticks, config.sub_tick_style, ccw, tick_radius=ctx.tick_r)
                MeterRenderingEngine._tag_as_static(canvas, "vu_element")

                NumberDrawer.draw_labels(canvas, px, py, t_vals, config.min_val, config.max_val, ctx.sang, ctx.eang, ctx.ext, ctx.base_r, SCALE_TEXT_OFFSET, config.scale_label_color, config.scale_numbers, config.label_overrides, ccw, label_radius=ctx.lab_r)
                MeterRenderingEngine._tag_as_static(canvas, "industrial_text")

                # 2. Arcs
                ScaleDrawer.draw_arcs(canvas, px, py, config.min_val, config.max_val, ctx.sang, ctx.eang, ctx.ext, ctx.base_r, config.curve_thickness, config.lower_colour, config.middle_colour, config.upper_colour, config.mid_range_start, config.red_zone_start, ccw, arc_radius=ctx.arc_r)
                MeterRenderingEngine._tag_as_static(canvas, "vu_element")

            # 3. Peak & Dynamic Needle elements
            MeterRenderingEngine._update_dynamic_elements(canvas, ctx, px, py, val, i, ccw, peak_on)

            if full_redraw:
                PivotDrawer.draw_pivot(canvas, px, py, config.pivot_size, config.pivot_colour, config.secondary_color, config.fg_color)
                MeterRenderingEngine._tag_as_static(canvas, "vu_element")

    @staticmethod
    def _get_pivots(ctx, val1, val2) -> List[Tuple[float, float, float, bool]]:
        """Determines pivot points based on meter mode and bezel shape."""
        cx1 = ctx.cx + ctx.config.pivot_offset_x
        cy1 = ctx.cy - ctx.config.pivot_offset_y
        cx2 = ctx.cx + ctx.config.pivot_offset_x_2
        cy2 = ctx.cy - ctx.config.pivot_offset_y_2

        pivots = [(cx1, cy1, val1, ctx.config.counter_clockwise)]
        is_stereo = ctx.bezel_shape in ["stereo_diamond", "intersecting_overlay"] or ctx.config.meter_mode == "stereo"
        
        if is_stereo:
            ccw2 = not ctx.config.counter_clockwise if ctx.bezel_shape == "stereo_diamond" else ctx.config.counter_clockwise
            pivots.append((cx2, cy2, val2, ccw2))
        return pivots

    @staticmethod
    def _update_dynamic_elements(canvas, ctx, px, py, val, index, ccw, peak_on):
        """Updates peak dot, shadow, and needle."""
        config = ctx.config
        vr = config.max_val - config.min_val
        norm_p = (config.red_zone_start - config.min_val) / vr if vr != 0 else 0
        p_ang = (ctx.eang + (norm_p * ctx.ext)) if ccw else (ctx.sang - (norm_p * ctx.ext))
        
        PeakDrawer.draw_peak_dot(canvas, px, py, p_ang, ctx.base_r, config.curve_thickness, peak_on, config.peak_flag, arc_radius=ctx.arc_r)

        style = config.pointer_style if index == 0 else config.pointer_style_2
        thick = config.needle_thickness if index == 0 else config.needle_thickness_2
        color = config.pointer_colour if index == 0 else config.pointer_colour_2

        ShadowDrawer.draw_shadow(canvas, px, py, val, config.min_val, config.max_val, ctx.sang, ctx.eang, ctx.ext, ctx.base_r, SCALE_TEXT_OFFSET, style, thick, ccw, config.pivot_size, needle_scale=ctx.nsf, tag=f"vu_shadow_{index}")
        NeedleDrawer.draw_needle(canvas, px, py, val, config.min_val, config.max_val, ctx.sang, ctx.eang, ctx.ext, ctx.base_r, SCALE_TEXT_OFFSET, color, style, thick, ccw, config.pivot_size, needle_scale=ctx.nsf, tag=f"vu_needle_{index}")

    @staticmethod
    def _tag_as_static(canvas, tag):
        """Tags elements matching 'tag' as 'vu_static' if they aren't needles."""
        for item in canvas.find_withtag(tag):
            tags = canvas.gettags(item)
            if not any(t.startswith("vu_needle") for t in tags) and "vu_static" not in tags:
                canvas.addtag_withtag("vu_static", item)

    @staticmethod
    def _draw_static_chassis(canvas, ctx):
        """Draws the bezel/chassis and glass effects."""
        config = ctx.config
        cw, ch = int(canvas.cget("width")), int(canvas.cget("height"))
        R, g_y, sk = BezelGeometry.get_scaling_params(cw, ch, ctx.bezel_shape, ctx.bezel_width)
        
        # Draw background fill behind bezel if not transparent
        if sk != "super_gem" and not (hasattr(canvas, 'panel_bg_image') and canvas.panel_bg_image) and not config.is_transparent:
            from ..constants import GEM_BEZEL_EXPANSION, GEM_BASE_HEIGHT, GEM_PEAK_HEIGHT
            if sk == "gem": by = ctx.cy - ((GEM_BASE_HEIGHT * R * GEM_BEZEL_EXPANSION) + g_y)
            elif sk == "super_gem": by = ctx.cy - (-(GEM_PEAK_HEIGHT * R * GEM_BEZEL_EXPANSION) + g_y)
            elif sk == "octagon": by = ctx.cy - ((-0.923 * R * 1.4) + g_y)
            else: by = ctx.cy - g_y
            
            bg = canvas.cget("bg")
            canvas.create_rectangle(0, by+1, cw, ch, fill=bg, outline=bg, tags="vu_static")
        
        if config.cosmetics:
             MeterModifier.draw_glass_layer(canvas, ctx.cx, ctx.cy, cw, ch, config.cosmetics)
             MeterModifier.draw_foreground_overlay(canvas, ctx.cx, ctx.cy, cw, ch, config.cosmetics)

    @staticmethod
    def _finalize_z_order(canvas):
        """Settles the Z-order of all layers."""
        order = ["panel_bg_slice", "nextgen_background", "vu_shadow", "vu_element", "nextgen_foreground", "industrial_text"]
        for i, t in enumerate(order):
            try: 
                if i == 0:
                    canvas.tag_lower(t)
                else:
                    prev = order[i-1]
                    canvas.tag_raise(t, prev)
            except: 
                pass
        canvas._z_order_settled = True
