# oaGuiElements/Methods/needle_engine.py
# Author: Anthony Peter Kuzub
# Version: 20260331.2355.1
#
# Description: Python wrapper for the Rust Needle Engine.

import logging
from .oaNeedleEngine_rs.compiler_hook import ensure_compiled

try:
    ensure_compiled()
    from .oaNeedleEngine_rs.oaneedleengine_rs import NeedleEngine as RustNeedleEngine
    HAS_RUST = True
except Exception as e:
    logging.error(f"oaGuiElements: Failed to load Rust Needle Engine: {e}")
    HAS_RUST = False

class NeedleEngine:
    """
    High-performance trigonometric geometry calculator using Rust.
    MANDATORY Rust implementation for smooth rendering.
    """
    def __init__(self):
        if HAS_RUST:
            print("🏗️🛠️🔗 [NEEDLE] Using PURE RUST geometry engine.")
            self._engine = RustNeedleEngine()
        else:
            self._engine = None
            logging.error("oaGuiElements: Missing mandatory Rust needle engine.")

    def calculate_geometry(self, cx: float, cy: float, config_dict: dict):
        if self._engine:
            return self._engine.calculate_geometry(cx, cy, config_dict)
        return {}
