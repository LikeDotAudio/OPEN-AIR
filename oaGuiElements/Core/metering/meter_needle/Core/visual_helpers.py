class MeterVisualHelpers:
    """Utility functions for drawing common meter visual components."""

    @staticmethod
    def draw_rounded_rect_poly(canvas, x1, y1, x2, y2, radius, color, tags=None):
        """Draws a rounded rectangle using a polygon for better anti-aliasing and fill control."""
        points = [
            x1 + radius, y1, x1 + radius, y1, x2 - radius, y1, x2 - radius, y1,
            x2, y1, x2, y1 + radius, x2, y2 - radius,
            x2, y2 - radius, x2, y2, x2 - radius, y2, x2 - radius, y2,
            x1 + radius, y2, x1 + radius, y2, x1, y2, x1, y2 - radius,
            x1, y2 - radius, x1, y1 + radius, x1, y1 + radius, x1, y1,
        ]
        return canvas.create_polygon(points, fill=color, outline=color, smooth=True, tags=tags or "vu_element")
