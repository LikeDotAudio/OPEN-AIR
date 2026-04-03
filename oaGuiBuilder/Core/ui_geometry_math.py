# Core/ui_geometry_math.py
# Author: Anthony Peter Kuzub
# Version: 20260401.1200.1
#
# Description: Wrapper for High-Performance Rust Geometry Math

import logging
from .oaGeometryMath_rs import compiler_hook

try:
    compiler_hook.ensure_compiled()
    import oageometrymath_rs
    HAS_RUST = True
except ImportError:
    logging.warning("⚠️ [GUI_BUILDER] oageometrymath_rs not found. Falling back to (missing) slow Python geometry math.")
    HAS_RUST = False
except Exception as e:
    logging.error(f"❌ [GUI_BUILDER] Failed to initialize Rust Geometry Math: {e}")
    HAS_RUST = False

import importlib
importlib.invalidate_caches()

class UIGeometryMath:
    """Centralized math utilities for UI coordinate and value transformations using Rust."""

    @staticmethod
    def normalize_value(val, min_val, max_val):
        """Normalizes a value to a 0.0 - 1.0 range via Rust."""
        if not HAS_RUST:
            try:
                if max_val == min_val: return 0.0
                return (float(val) - float(min_val)) / (float(max_val) - float(min_val))
            except (TypeError, ValueError, ZeroDivisionError):
                return 0.0

        try:
            return oageometrymath_rs.normalize_value(float(val), float(min_val), float(max_val))
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def value_to_pixel(val, min_val, max_val, pixel_length, reverse=False):
        """Maps a value to a pixel position within a given length via Rust."""
        if not HAS_RUST:
            # Simple Python fallback
            norm = UIGeometryMath.normalize_value(val, min_val, max_val)
            if reverse: norm = 1.0 - norm
            return norm * float(pixel_length)

        try:
            return oageometrymath_rs.value_to_pixel(float(val), float(min_val), float(max_val), float(pixel_length), bool(reverse))
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def rotate_point(px, py, cx, cy, angle_deg):
        """Rotates a point around a center by a given angle in degrees via Rust."""
        if not HAS_RUST:
            import math
            angle_rad = math.radians(angle_deg)
            s = math.sin(angle_rad)
            c = math.cos(angle_rad)
            px -= cx; py -= cy
            xnew = px * c - py * s
            ynew = px * s + py * c
            return xnew + cx, ynew + cy

        try:
            return oageometrymath_rs.rotate_point(float(px), float(py), float(cx), float(cy), float(angle_deg))
        except (TypeError, ValueError):
            return px, py

    @staticmethod
    def get_position(angle_deg, distance, center_x=0, center_y=0):
        """Calculates X, Y coordinates for a given angle and distance from a center via Rust."""
        if not HAS_RUST:
            import math
            angle_rad = math.radians(angle_deg)
            x = center_x + distance * math.cos(angle_rad)
            y = center_y + distance * math.sin(angle_rad)
            return x, y

        try:
            return oageometrymath_rs.get_position(float(angle_deg), float(distance), float(center_x), float(center_y))
        except (TypeError, ValueError):
            return center_x, center_y

    @staticmethod
    def get_angle(px, py, cx=0, cy=0):
        """Calculates the angle in degrees from a center to a point via Rust."""
        if not HAS_RUST:
            import math
            return math.degrees(math.atan2(py - cy, px - cx))

        try:
            return oageometrymath_rs.get_angle(float(px), float(py), float(cx), float(cy))
        except (TypeError, ValueError):
            return 0.0

