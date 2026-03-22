# cosmetics/lens.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import tkinter as tk
from oaGuiElements.Core.metering.meter_needle.cosmetics.geometry import BezelGeometry
from oaGuiElements.Core.metering.meter_needle.constants import (
    LENS_GLOW_STEPS, LENS_GLOW_SHRINK_MAX, LENS_SHADOW_STEPS, LENS_SHADOW_DEPTH
)

class BezelLens:
    @staticmethod
    def draw(canvas, cx, cy, w, h, cosmetics):
        style_overrides = cosmetics.get("style_overrides", {})
        bezel_shape = style_overrides.get("bezel_shape", None)
        
        # Check if lighting is enabled (default to True)
        if not style_overrides.get("enable_lighting", True):
            return
        
        if not bezel_shape:
            return

        colors = cosmetics.get("colors", {})
        faceplate_hex = colors.get("faceplate", "#e0d4b4")
        glow_hex = "#fffcd1" 
        shadow_hex = "#a09070" 
        line_width = int(style_overrides.get("bezel_width", 12))
        
        # 1. Shape-Matched Glow
        glow_steps = LENS_GLOW_STEPS
        for i in range(glow_steps):
            frac = i / float(glow_steps)
            fade = frac * frac
            step_color = BezelLens._blend_colors(glow_hex, faceplate_hex, fade)
            
            shrink_px = (1.0 - frac) * LENS_GLOW_SHRINK_MAX 
            
            points, is_smooth = BezelGeometry.get_bezel_points(
                cx, cy, w, h, bezel_shape, line_width, shrink_px=shrink_px
            )
            
            if points:
                canvas.create_polygon(points, fill=step_color, outline="", tags="nextgen_background", smooth=is_smooth)

        # 2. Inner Shadow (Contained)
        shadow_steps = LENS_SHADOW_STEPS
        shadow_depth = LENS_SHADOW_DEPTH
        for i in range(shadow_steps):
            frac = i / float(shadow_steps)
            step_color = BezelLens._blend_colors(shadow_hex, faceplate_hex, frac)
            shrink_px = i * (shadow_depth / shadow_steps)
            
            points, is_smooth = BezelGeometry.get_bezel_points(
                cx, cy, w, h, bezel_shape, line_width, shrink_px=shrink_px
            )
            
            if points:
                canvas.create_polygon(points, fill=step_color, outline="", tags="nextgen_background", smooth=is_smooth)

    @staticmethod
    def _blend_colors(c1, c2, f):
        def h2rgb(h): return tuple(int(h.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        def rgb2h(r): return "#{:02x}{:02x}{:02x}".format(*[int(x) for x in r])
        try:
            r1, g1, b1 = h2rgb(c1)
            r2, g2, b2 = h2rgb(c2)
            return rgb2h((r1 + (r2-r1)*f, g1 + (g2-g1)*f, b1 + (b2-b1)*f))
        except: return c1
