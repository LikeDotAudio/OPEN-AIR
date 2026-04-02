# oaGuiElements/Methods/rotary_core.py
# Author: Anthony Peter Kuzub
# Version: 20260331.2355.1
#
# Description: Python wrapper for the Rust Rotary Core engine.

import logging
from .oaRotaryCore_rs.compiler_hook import ensure_compiled

try:
    ensure_compiled()
    from .oaRotaryCore_rs.oarotarycore_rs import RotaryCore as RustRotaryCore
    HAS_RUST = True
except Exception as e:
    logging.error(f"oaGuiElements: Failed to load Rust Rotary Core: {e}")
    HAS_RUST = False

LOCAL_DEBUG = False

class RotaryCore:
    """
    High-performance rotary calculation engine using Rust.
    MANDATORY Rust implementation for accurate, fast GUI interaction.
    """
    def __init__(self):
        if HAS_RUST:
            if LOCAL_DEBUG:
                print("🎡🛠️🔗 [ROTARY] Using PURE RUST rotary core.")
            self._engine = RustRotaryCore()
        else:
            self._engine = None
            logging.error("oaGuiElements: Missing mandatory Rust rotary core.")

    def calculate_angle(self, value: float, min_val: float, max_val: float, knob_style: str) -> float:
        if self._engine:
            return self._engine.calculate_angle(value, min_val, max_val, knob_style)
        return 0.0

    def get_poly_points(self, center_x: float, center_y: float, radius: float, sides: int, start_angle: float) -> list:
        if self._engine:
            return self._engine.get_poly_points(center_x, center_y, radius, sides, start_angle)
        return []

    def get_gear_points(self, center_x: float, center_y: float, radius: float, teeth: int, notch_depth: float, start_angle: float) -> list:
        if self._engine:
            return self._engine.get_gear_points(center_x, center_y, radius, teeth, notch_depth, start_angle)
        return []
