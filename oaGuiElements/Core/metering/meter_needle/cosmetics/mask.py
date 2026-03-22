# cosmetics/mask.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import tkinter as tk
import math
from dataclasses import dataclass

from oaGuiElements.Core.metering.meter_needle.cosmetics.geometry import BezelGeometry
from oaGuiElements.Core.metering.meter_needle.constants import (
    GEM_BEZEL_EXPANSION, GEM_BASE_HEIGHT, SHAPE_Y_SHIFTS, HILL_CONFIGS
)

@dataclass
class MaskParams:
    cx: float
    cy: float
    w: float
    h: float
    cosmetics: dict

class BezelMask:
    @staticmethod
    def draw(canvas, cx, cy, w, h, cosmetics):
        params = MaskParams(cx, cy, w, h, cosmetics)
        return BezelMask._draw_with_params(canvas, params)

    @staticmethod
    def _draw_with_params(canvas, p: MaskParams):
        # 1. Guard Clauses
        style_ovr = p.cosmetics.get("style_overrides", {})
        overlay_style = style_ovr.get("overlay_style", None)
        if not overlay_style or overlay_style.lower() != "aperture_mask":
            return

        colors = p.cosmetics.get("colors", {})
        mask_color = colors.get("mask", colors.get("bezel", colors.get("faceplate", "#e0d4b4")))
        if not mask_color or mask_color.lower() in ["transparent", "none", ""]:
            return

        # 2. Setup
        bezel_shape = style_ovr.get("bezel_shape", "").lower()
        line_width = int(style_ovr.get("bezel_width", 12))
        radius, global_y_shift, shape_key = BezelGeometry.get_scaling_params(p.w, p.h, bezel_shape, line_width)
        
        # 3. Draw Hill
        BezelMask._draw_hill(canvas, p.cx, p.cy, radius, global_y_shift, shape_key, mask_color)

    @staticmethod
    def _draw_hill(canvas, cx, cy, radius, global_y_shift, shape_key, color):
        w_factor, h_factor = HILL_CONFIGS.get(shape_key, HILL_CONFIGS["default"])
        hill_w, hill_h = radius * w_factor, radius * h_factor
        
        base_y = BezelMask._get_base_y(cy, radius, global_y_shift, shape_key)
        
        steps = 20
        poly_points = []
        for i in range(steps + 1):
            x_norm = 1.0 - (2.0 * i / steps)
            x = cx + (x_norm * hill_w)
            y = base_y - (math.cos(x_norm * math.pi / 2) * hill_h)
            poly_points.extend([x, y])
        
        # Close at the baseline of the bezel
        poly_points.extend([cx - hill_w, base_y])
        poly_points.extend([cx + hill_w, base_y])
        
        canvas.create_polygon(poly_points, fill=color, outline=color, tags="nextgen_foreground")

    @staticmethod
    def _get_base_y(cy, radius, global_y_shift, shape_key):
        if shape_key == "gem":
            gem_rad = radius * GEM_BEZEL_EXPANSION
            return cy - ((GEM_BASE_HEIGHT * gem_rad) + global_y_shift)
        
        if shape_key == "super_gem":
            return cy
            
        if shape_key == "octagon":
            oct_rad = radius * 1.4 # OCTAGON_BEZEL_EXPANSION
            return cy - ((-0.923 * oct_rad) + global_y_shift)
            
        return cy - global_y_shift
