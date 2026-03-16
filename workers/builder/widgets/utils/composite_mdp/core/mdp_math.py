import math

class MDPMath:
    """Helper for coordinate transformations in rotated local spaces."""

    @staticmethod
    def rotate_point(px, py, cx, cy, angle_deg):
        rad = math.radians(angle_deg)
        cos_a, sin_a = math.cos(rad), math.sin(rad)
        nx = cos_a * (px - cx) - sin_a * (py - cy) + cx
        ny = sin_a * (px - cx) + cos_a * (py - cy) + cy
        return nx, ny

    @staticmethod
    def to_local_space(dx, dy, angle_deg):
        """Translates global deltas to local rotated deltas."""
        rad = math.radians(angle_deg)
        ldx = dx * math.cos(-rad) - dy * math.sin(-rad)
        ldy = dx * math.sin(-rad) + dy * math.cos(-rad)
        return ldx, ldy
