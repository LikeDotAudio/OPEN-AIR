# oaGuiBackground/Methods/pattern_engine.py
# Author: Anthony Peter Kuzub
# Version: 20260331.2330.1
#
# Description: Python wrapper for the Rust Pattern Engine.

import logging
from PIL import Image

try:
    from oaRustCore.oa_pattern_engine_rs import PatternEngine as RustPatternEngine
    HAS_RUST = True
except Exception as e:
    logging.error(f"oaGuiBackground: Failed to load Rust Pattern Engine: {e}")
    HAS_RUST = False

LOCAL_DEBUG = False

class PatternEngine:
    """
    High-performance procedural asset generator using Rust.
    """
    def __init__(self):
        if HAS_RUST:
            if LOCAL_DEBUG:
                print("🎨🛠️🔗 [PATTERNS] Using PURE RUST engine.")
            self._engine = RustPatternEngine()
        else:
            self._engine = None
            logging.warning("oaGuiBackground: Using legacy/missing pattern engine (No Rust).")

    def generate_streaks(self, width: int, height: int, vertical: bool, sigma: float, seed: int):
        if self._engine:
            raw_bytes = self._engine.generate_streaks(width, height, vertical, sigma, seed)
            return Image.frombytes("RGBA", (width, height), raw_bytes)
        return None

    def generate_hammered(self, width: int, height: int, seed: int):
        if self._engine:
            raw_bytes = self._engine.generate_hammered(width, height, seed)
            return Image.frombytes("RGBA", (width, height), raw_bytes)
        return None

    def generate_screw(self, size: int, config: dict):
        if self._engine:
            raw_bytes = self._engine.generate_screw(size, config)
            # Screw canvas size includes padding
            padding = int(size * 0.4)
            canvas_dim = size + padding * 2
            return Image.frombytes("RGBA", (canvas_dim, canvas_dim), raw_bytes)
        return None

    def generate_metal_fold(self, width: int, height: int, config: dict):
        if self._engine:
            raw_bytes = self._engine.generate_metal_fold(width, height, config)
            return Image.frombytes("RGBA", (width, height), raw_bytes)
        return None

    def generate_vignette(self, width: int, height: int, intensity: float, depth: int):
        if self._engine:
            raw_bytes = self._engine.generate_vignette(width, height, intensity, depth)
            return Image.frombytes("RGBA", (width, height), raw_bytes)
        return None

    def generate_scratches(self, width: int, height: int, config: dict):
        if self._engine:
            raw_bytes = self._engine.generate_scratches(width, height, config)
            return Image.frombytes("RGBA", (width, height), raw_bytes)
        return None
