# Core/ui_geometry_math.py
# Author: Anthony Peter Kuzub
# Version: 20260401.1200.1
#
# Description: Wrapper for High-Performance Rust Geometry Math

import sys
import os

# Add the hyphenated directory to sys.path temporarily to import compiler_hook
_rs_dir = os.path.join(os.path.dirname(__file__), "oaGeometryMath-rs")
if _rs_dir not in sys.path:
    sys.path.insert(0, _rs_dir)

import compiler_hook
compiler_hook.ensure_compiled()

import importlib
importlib.invalidate_caches()

try:
    import oageometrymath_rs
except ImportError as e:
    from loguru import logger
    logger.critical("🚀❌ [FATAL] Rust Geometry Math module missing. Pure Rust mode is mandatory.")
    raise e

class UIGeometryMath:
    """Centralized math utilities for UI coordinate and value transformations using Rust."""

    @staticmethod
    def normalize_value(val, min_val, max_val):
        """Normalizes a value to a 0.0 - 1.0 range via Rust."""
        try:
            return oageometrymath_rs.normalize_value(float(val), float(min_val), float(max_val))
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def value_to_pixel(val, min_val, max_val, pixel_length, reverse=False):
        """Maps a value to a pixel position within a given length via Rust."""
        try:
            return oageometrymath_rs.value_to_pixel(float(val), float(min_val), float(max_val), float(pixel_length), bool(reverse))
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def rotate_point(px, py, cx, cy, angle_deg):
        """Rotates a point around a center by a given angle in degrees via Rust."""
        try:
            return oageometrymath_rs.rotate_point(float(px), float(py), float(cx), float(cy), float(angle_deg))
        except (TypeError, ValueError):
            return px, py

    @staticmethod
    def get_position(angle_deg, distance, center_x=0, center_y=0):
        """Calculates X, Y coordinates for a given angle and distance from a center via Rust."""
        try:
            return oageometrymath_rs.get_position(float(angle_deg), float(distance), float(center_x), float(center_y))
        except (TypeError, ValueError):
            return center_x, center_y

    @staticmethod
    def get_angle(px, py, cx=0, cy=0):
        """Calculates the angle in degrees from a center to a point via Rust."""
        try:
            return oageometrymath_rs.get_angle(float(px), float(py), float(cx), float(cy))
        except (TypeError, ValueError):
            return 0.0
