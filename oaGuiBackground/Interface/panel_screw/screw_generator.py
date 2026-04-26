# panel_screw/screw_generator.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Procedural generator for high-fidelity Robertson screws (RUST OPTIMIZED).

import random

from oaGuiManager.Core.factory.asset_cache import AssetCacheManager
from oaLogging.Core.logger import builder_logger
from oaLogging.Methods.matrix_gate import is_debug_allowed

BUILDER_DEBUG = is_debug_allowed(system="UI", element="GUI_BUILDER")
ROTATION_RANGE_MAX = 90

class ScrewGenerator:
    """
    Procedural generator for high-fidelity Robertson screws.
    MANDATORY Rust implementation for high-performance rendering.
    """

    @staticmethod
    def generate_screw(size_pixels, configuration_data={}):
        """
        Generates a single screw image (RGBA) via the Rust Pattern Engine.
        Includes disk caching.
        """
        # --- 0. Check Cache First ---
        cached_image = AssetCacheManager.load_from_cache("screw", size_pixels, size_pixels, configuration_data)
        if cached_image:
            return cached_image

        # --- 1. Procedural Generation (RUST) ---
        if BUILDER_DEBUG: builder_logger.info(f"🔩🏗️🌀 [BUILDER] Generating NEW Procedural Screw ({size_pixels}px) via RUST")

        from oaGuiBackground.Methods.pattern_engine import PatternEngine
        _engine = PatternEngine()

        config = configuration_data.copy()
        if "angle" not in config:
            config["angle"] = random.randint(0, ROTATION_RANGE_MAX)

        screw_image = _engine.generate_screw(size_pixels, config)

        # --- 2. Save to Cache ---
        if BUILDER_DEBUG: builder_logger.success("🎨🆗💾 [SUCCESS] Procedural screw generation complete. Saving to cache.")
        AssetCacheManager.save_to_cache("screw", size_pixels, size_pixels, configuration_data, screw_image)

        return screw_image

    @staticmethod
    def convert_hex_to_rgb(hex_string):
        """Converts a hexadecimal color string to an RGB tuple."""
        if not isinstance(hex_string, str):
            return (128, 128, 128)
        color_hex = hex_string.lstrip('#')
        return tuple(int(color_hex[i:i+2], 16) for i in (0, 2, 4))
