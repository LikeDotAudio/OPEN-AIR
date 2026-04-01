# Core/ui_geometry_math.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import math
import sys
import os

# Add the hyphenated directory to sys.path temporarily to import compiler_hook
_rs_dir = os.path.join(os.path.dirname(__file__), "oaGeometryMath-rs")
if _rs_dir not in sys.path:
    sys.path.insert(0, _rs_dir)

import compiler_hook
compiler_hook.ensure_compiled()

try:
    import oageometrymath_rs
except ImportError as e:
    from loguru import logger
    logger.critical("🚀❌ [FATAL] Rust Geometry Math module missing. Pure Rust mode is mandatory.")
    raise e

class UIGeometryMath:
    """Centralized math utilities for UI coordinate and value transformations."""

    @staticmethod
    def normalize_value(val, min_val, max_val):
        """Normalizes a value to a 0.0 - 1.0 range."""
        try:
            if max_val == min_val:
                return 0.0
            return (val - min_val) / (max_val - min_val)
        except (ZeroDivisionError, TypeError, ValueError):
            return 0.0

    @staticmethod
    def value_to_pixel(val, min_val, max_val, pixel_length, reverse=False):
        """Maps a value to a pixel position within a given length."""
        norm = UIGeometryMath.normalize_value(val, min_val, max_val)
        if reverse:
            return (1.0 - norm) * pixel_length
        return norm * pixel_length

    @staticmethod
    def rotate_point(px, py, cx, cy, angle_deg):
        """Rotates a point around a center by a given angle in degrees."""
        rad = math.radians(angle_deg)
        cos_a, sin_a = math.cos(rad), math.sin(rad)
        nx = cos_a * (px - cx) - sin_a * (py - cy) + cx
        ny = sin_a * (px - cx) + cos_a * (py - cy) + cy
        return nx, ny

    @staticmethod
    def get_position(angle_deg, distance, center_x=0, center_y=0):
        """Calculates X, Y coordinates for a given angle and distance from a center."""
        rad = math.radians(angle_deg)
        x = center_x + distance * math.cos(rad)
        y = center_y + distance * math.sin(rad)
        return x, y

    @staticmethod
    def get_angle(px, py, cx=0, cy=0):
        """Calculates the angle in degrees from a center to a point."""
        return math.degrees(math.atan2(py - cy, px - cx))
