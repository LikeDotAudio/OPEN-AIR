# oaGui/Interface/coordinate_transformer.py
# Author: Anthony Peter Kuzub
# Version: 20260416.Modular.1
#
# Description: Transforms data ranges into physical pixel positions and coordinates.
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

class CoordinateTransformer:
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

        norm = CoordinateTransformer.normalize_value(value, min_val, max_val)
        if reverse:
            norm = 1.0 - norm
        return norm * float(pixel_length)

    @staticmethod
    def rotate_point(point_x: float, point_y: float, center_x: float, center_y: float, angle_deg: float) -> tuple:
        """Rotates a point (point_x, point_y) around a center (center_x, center_y) by angle_deg."""
        if HAS_RUST:
            try:
                return oageometrymath_rs.rotate_point(float(point_x), float(point_y), float(center_x), float(center_y), float(angle_deg))
            except (TypeError, ValueError):
                pass

        angle_rad = math.radians(angle_deg)
        sin_a = math.sin(angle_rad)
        cos_a = math.cos(angle_rad)

        # Translate to origin
        delta_x, delta_y = point_x - center_x, point_y - center_y

        # Rotate and translate back
        new_x = (delta_x * cos_a - delta_y * sin_a) + center_x
        new_y = (delta_x * sin_a + delta_y * cos_a) + center_y
        return new_x, new_y

    @staticmethod
    def get_position(angle_deg: float, distance: float, center_x: float = 0.0, center_y: float = 0.0) -> tuple:
        """Calculates position_x, position_y coordinates from polar parameters."""
        if HAS_RUST:
            try:
                return oageometrymath_rs.get_position(float(angle_deg), float(distance), float(center_x), float(center_y))
            except (TypeError, ValueError):
                pass

        angle_rad = math.radians(angle_deg)
        position_x = center_x + distance * math.cos(angle_rad)
        position_y = center_y + distance * math.sin(angle_rad)
        return position_x, position_y

    @staticmethod
    def get_angle(point_x: float, point_y: float, center_x: float = 0.0, center_y: float = 0.0) -> float:
        """Calculates the angle in degrees from center (center_x, center_y) to point (point_x, point_y)."""
        if HAS_RUST:
            try:
                return oageometrymath_rs.get_angle(float(point_x), float(point_y), float(center_x), float(center_y))
            except (TypeError, ValueError):
                pass

        return math.degrees(math.atan2(point_y - center_y, point_x - center_x))
