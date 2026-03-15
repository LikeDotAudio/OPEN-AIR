import tkinter as tk
import math

from workers.builder.meter_needle.cosmetics.geometry import BezelGeometry
from workers.builder.meter_needle.constants import (
    GEM_BEZEL_EXPANSION, GEM_BASE_HEIGHT
)

class BezelMask:
    @staticmethod
    def draw(canvas, cx, cy, w, h, cosmetics):
        style_overrides = cosmetics.get("style_overrides", {})
        overlay_style = style_overrides.get("overlay_style", None)
        bezel_shape = style_overrides.get("bezel_shape", "").lower()
        
        if not overlay_style or overlay_style.lower() != "aperture_mask":
            return

        colors = cosmetics.get("colors", {})
        # Prefer specific mask color, then bezel color, then fallback to faceplate
        mask_color = colors.get("mask", colors.get("bezel", colors.get("faceplate", "#e0d4b4")))
        
        # ⚡ INDUSTRIAL TRANSPARENCY: Check for slicing first
        # If we have a slice, we can use it to 'mask out' the hill or blend it.
        # However, for a TRUE aperture mask (mechanical part), we often WANT a solid color.
        # If mask_color is 'transparent', we skip.
        if not mask_color or mask_color.lower() in ["transparent", "none", ""]:
            return

        line_width = int(style_overrides.get("bezel_width", 12))
        
        # Use BezelGeometry for consistent scaling
        radius, global_y_shift, shape_key = BezelGeometry.get_scaling_params(w, h, bezel_shape, line_width)
        
        tag = "nextgen_foreground"
        
        # Aperture Mask logic (The 'Hill' covering the bottom of the needle)
        # Dynamic width based on shape
        if shape_key == "hotdog":
            hill_w = radius * 2.5
            hill_h = radius * 0.3
        elif shape_key == "gem":
            hill_w = radius * 0.8
            hill_h = radius * 0.3
        elif shape_key == "super_gem":
            hill_w = radius * 0.4
            hill_h = radius * 0.3
        elif shape_key == "hex":
            hill_w = radius * 1.8
            hill_h = radius * 0.3
        elif shape_key == "octagon":
            hill_w = radius * 1.8
            hill_h = radius * 0.3
        elif shape_key in ["triangle", "pyramid", "parking_meter"]:
            hill_w = radius * 0.2
            hill_h = radius * 0.1
        elif shape_key in ["squircle", "squimonde"]:
            hill_w = radius * 0.5
            hill_h = radius * 0.3
        elif shape_key == "crest":
            hill_w = radius * 1.0
            hill_h = radius * 0.3
        elif shape_key == "squectangle":
            hill_w = radius * 0.7
            hill_h = radius * 0.3
        elif shape_key == "trapezoid":
            hill_w = radius * 1.2
            hill_h = radius * 0.3
        else:
            hill_w = radius * 1.5
            hill_h = radius * 0.3
        
        steps = 20
        poly_points = []
        
        # Determine base Y (bottom of the mask)
        if shape_key == "gem":
            gem_rad = radius * GEM_BEZEL_EXPANSION
            y_base_user = (GEM_BASE_HEIGHT * gem_rad) + global_y_shift
            base_y = cy - y_base_user
        elif shape_key == "super_gem":
            base_y = cy
        elif shape_key == "octagon":
            oct_rad = radius * 1.4
            y_base_user = (-0.923 * oct_rad) + global_y_shift
            base_y = cy - y_base_user
        else:
            base_y = cy - global_y_shift
        
        for i in range(steps + 1):
            x_norm = 1.0 - (2.0 * i / steps)
            x = cx + (x_norm * hill_w)
            y = base_y - (math.cos(x_norm * math.pi / 2) * hill_h)
            poly_points.extend([x, y])
        
        # Close at the baseline of the bezel
        poly_points.extend([cx - hill_w, base_y])
        poly_points.extend([cx + hill_w, base_y])
        
        canvas.create_polygon(poly_points, fill=mask_color, outline=mask_color, tags=tag)