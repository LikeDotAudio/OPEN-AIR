# Core/cmdp_math.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import math

class CircularMath:
    """Helper for polar and cartesian coordinate transformations."""

    @staticmethod
    def rotate_point(px, py, cx, cy, angle_deg):
        rad = math.radians(angle_deg)
        cos_a, sin_a = math.cos(rad), math.sin(rad)
        nx = cos_a * (px - cx) - sin_a * (py - cy) + cx
        ny = sin_a * (px - cx) + cos_a * (py - cy) + cy
        return nx, ny

    @staticmethod
    def get_position(angle_deg, distance, center_x=600, center_y=450):
        rad = math.radians(angle_deg)
        x = center_x + distance * math.cos(rad)
        y = center_y + distance * math.sin(rad)
        return x, y

    @staticmethod
    def get_angle(px, py, cx=600, cy=450):
        return math.degrees(math.atan2(py - cy, px - cx))
