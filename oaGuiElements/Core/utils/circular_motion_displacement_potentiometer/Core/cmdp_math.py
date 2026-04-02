# Core/cmdp_math.py
# Author: Anthony Peter Kuzub
# Version: 20260402.0001.1
#
# Description: High-performance coordinate transformations using Rust.

import math
import logging
from oaGuiElements.Methods.oaCMDPMath_rs.compiler_hook import ensure_compiled

try:
    ensure_compiled()
    from oaGuiElements.Methods.oaCMDPMath_rs.oacmdpmath_rs import CMDPMath
    _rust_engine = CMDPMath()
    HAS_RUST = True
except Exception as e:
    logging.warning(f"oaGuiElements: Failed to load Rust CMDPMath, falling back to Python: {e}")
    HAS_RUST = False

class CircularMath:
    """Helper for polar and cartesian coordinate transformations."""

    @staticmethod
    def rotate_point(px, py, cx, cy, angle_deg):
        if HAS_RUST:
            # Note: Rust implementation expects cos_t and sin_t for some methods, 
            # but we can use a simpler approach or add it to Rust.
            # Our Rust CMDPMath has calculate_rotated_point which takes cos_t and sin_t.
            rad = math.radians(angle_deg)
            return _rust_engine.calculate_rotated_point(px, py, cx, cy, math.cos(rad), math.sin(rad))
        
        rad = math.radians(angle_deg)
        cos_a, sin_a = math.cos(rad), math.sin(rad)
        nx = cos_a * (px - cx) - sin_a * (py - cy) + cx
        ny = sin_a * (px - cx) + cos_a * (py - cy) + cy
        return nx, ny

    @staticmethod
    def get_position(angle_deg, distance, center_x=600, center_y=450):
        if HAS_RUST:
            return _rust_engine.calculate_position(angle_deg, distance, center_x, center_y)
            
        rad = math.radians(angle_deg)
        x = center_x + distance * math.cos(rad)
        y = center_y + distance * math.sin(rad)
        return x, y

    @staticmethod
    def get_angle(px, py, cx=600, cy=450):
        if HAS_RUST:
            return _rust_engine.calculate_angle(px, py, cx, cy)
            
        return math.degrees(math.atan2(py - cy, px - cx))

    @staticmethod
    def calculate_projection(dx, dy, angle_deg):
        if HAS_RUST:
            return _rust_engine.calculate_projection(dx, dy, angle_deg)
        
        rad = math.radians(angle_deg)
        return dx * math.cos(rad) + dy * math.sin(rad)

    @staticmethod
    def calculate_fader_geometry(config):
        if HAS_RUST:
            return _rust_engine.calculate_fader_geometry(config)
        return None
