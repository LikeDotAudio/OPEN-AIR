import tkinter as tk
from oaGuiElements.metering.meter_needle.cosmetics.geometry import BezelGeometry

class BezelOverlay:
    @staticmethod
    def draw(canvas, cx, cy, w, h, cosmetics):
        style_overrides = cosmetics.get("style_overrides", {})
        bezel_shape = style_overrides.get("bezel_shape", None)
        
        if not bezel_shape:
            return

        colors = cosmetics.get("colors", {})
        bezel_color = colors.get("bezel", "silver")
        
        if not bezel_color or bezel_color.lower() in ["transparent", "none", ""]:
            return

        line_width = int(style_overrides.get("bezel_width", 12))

        points, is_smooth = BezelGeometry.get_bezel_points(
            cx, cy, w, h, bezel_shape, line_width
        )
        
        if points:
            join = tk.ROUND if is_smooth else tk.MITER
            canvas.create_polygon(points, fill="", outline=bezel_color, width=line_width, tags="nextgen_foreground", smooth=is_smooth, joinstyle=join)
