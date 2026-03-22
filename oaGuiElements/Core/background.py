# Core/background.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import tkinter as tk
from oaGuiElements.Core.metering.meter_needle.cosmetics.geometry import BezelGeometry

class BezelBackground:
    @staticmethod
    def draw(canvas, cx, cy, w, h, cosmetics):
        style_overrides = cosmetics.get("style_overrides", {})
        bezel_shape = style_overrides.get("bezel_shape", None)
        
        if not bezel_shape:
            return

        colors = cosmetics.get("colors", {})
        # Use new standard 'meter_face_colour'
        face_color = colors.get("meter_face_colour", colors.get("faceplate", "#e0d4b4"))
        
        # If face is transparent, do not draw the card.
        # This allows the underlying procedural panel to show through.
        if not face_color or face_color.lower() in ["transparent", "none", "", "#00000000"]:
            return

        line_width = int(style_overrides.get("bezel_width", 12))

        # Shrink by half the bezel width to ensure the fill is perfectly covered
        # by the bezel frame (which is centered on the path).
        shrink_px = line_width / 2.0
        points, is_smooth = BezelGeometry.get_bezel_points(
            cx, cy, w, h, bezel_shape, line_width, shrink_px=shrink_px
        )
        
        if points:
            canvas.create_polygon(points, fill=face_color, outline="", tags="nextgen_background", smooth=is_smooth)
