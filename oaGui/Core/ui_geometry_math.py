# oaGui/Core/ui_geometry_math.py
# Author: Anthony Peter Kuzub
# Version: 20260416.Modular.1
#
# Description: Centralized UI coordinate and value transformation utilities.
# Provides high-performance Rust bindings with robust Python fallbacks.

import importlib
import logging
import math

# 🛡️ RUST NATIVE ACCELERATION
try:
    from oaRustCore import oa_geometry_math_rs as oageometrymath_rs
    HAS_RUST = True
except ImportError:
    logging.warning("⚠️ [GUI_BUILDER] oageometrymath_rs not found. Falling back to slow Python geometry math.")
    HAS_RUST = False
except Exception as e:
    logging.error(f"❌ [GUI_BUILDER] Failed to initialize Rust Geometry Math: {e}")
    HAS_RUST = False

importlib.invalidate_caches()

class UIGeometryMath:
    """Mathematical engine for UI transformations."""

    @staticmethod
    def normalize_value(value: float, min_val: float, max_val: float) -> float:
        """Normalizes a value to a 0.0 - 1.0 range."""
        if HAS_RUST:
            try:
                return oageometrymath_rs.normalize_value(float(value), float(min_val), float(max_val))
            except (TypeError, ValueError):
                pass

        try:
            if max_val == min_val:
                return 0.0
            return (float(value) - float(min_val)) / (float(max_val) - float(min_val))
        except (TypeError, ValueError, ZeroDivisionError):
            return 0.0

    @staticmethod
    def value_to_pixel(value: float, min_val: float, max_val: float, pixel_length: float, reverse: bool = False) -> float:
        """Maps a value to a pixel position within a given length."""
        if HAS_RUST:
            try:
                return oageometrymath_rs.value_to_pixel(float(value), float(min_val), float(max_val), float(pixel_length), bool(reverse))
            except (TypeError, ValueError):
                pass

        norm = UIGeometryMath.normalize_value(value, min_val, max_val)
        if reverse:
            norm = 1.0 - norm
        return norm * float(pixel_length)

    @staticmethod
    def rotate_point(px: float, py: float, cx: float, cy: float, angle_deg: float) -> tuple:
        """Rotates a point (px, py) around a center (cx, cy) by angle_deg."""
        if HAS_RUST:
            try:
                return oageometrymath_rs.rotate_point(float(px), float(py), float(cx), float(cy), float(angle_deg))
            except (TypeError, ValueError):
                pass

        angle_rad = math.radians(angle_deg)
        sin_a = math.sin(angle_rad)
        cos_a = math.cos(angle_rad)

        # Translate to origin
        dx, dy = px - cx, py - cy

        # Rotate and translate back
        nx = (dx * cos_a - dy * sin_a) + cx
        ny = (dx * sin_a + dy * cos_a) + cy
        return nx, ny

    @staticmethod
    def get_position(angle_deg: float, distance: float, center_x: float = 0.0, center_y: float = 0.0) -> tuple:
        """Calculates X, Y coordinates from polar parameters."""
        if HAS_RUST:
            try:
                return oageometrymath_rs.get_position(float(angle_deg), float(distance), float(center_x), float(center_y))
            except (TypeError, ValueError):
                pass

        angle_rad = math.radians(angle_deg)
        x = center_x + distance * math.cos(angle_rad)
        y = center_y + distance * math.sin(angle_rad)
        return x, y

    @staticmethod
    def get_angle(px: float, py: float, cx: float = 0.0, cy: float = 0.0) -> float:
        """Calculates the angle in degrees from center (cx, cy) to point (px, py)."""
        if HAS_RUST:
            try:
                return oageometrymath_rs.get_angle(float(px), float(py), float(cx), float(cy))
            except (TypeError, ValueError):
                pass

        return math.degrees(math.atan2(py - cy, px - cx))
