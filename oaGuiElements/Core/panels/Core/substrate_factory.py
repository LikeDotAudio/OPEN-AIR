# Core/substrate_factory.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import random

from PIL import Image, ImageChops

from oaGuiElements.Methods.pattern_engine import PatternEngine

_engine = PatternEngine()


class SubstrateFactory:
    @staticmethod
    def generate_streaks(width, height, vertical=True, sigma=40, scale_factor=1.0):
        seed = random.randint(0, 1000000)
        # ⚡ RESOLUTION FIX: Leverage Rust engine with scaled dimensions
        scaled_w = int(width * scale_factor)
        scaled_h = int(height * scale_factor)

        img = _engine.generate_streaks(scaled_w, scaled_h, vertical, float(sigma), seed)
        if img:
            if scale_factor > 1.0:
                return img.resize((width, height), resample=Image.LANCZOS)
            return img

        # --- Python Fallback ---
        # ⚡ RESOLUTION FIX: Adjust downsampling based on scale_factor
        # Using a much smaller base divisor (10 instead of 100) for higher fidelity.
        base_divisor = 10 / scale_factor
        source_w = width if not vertical else max(5, int(width // base_divisor))
        source_h = height if vertical else max(5, int(height // base_divisor))

        source = Image.effect_noise((source_w, source_h), sigma=sigma)
        return source.resize((width, height), resample=Image.LANCZOS)

    @staticmethod
    def generate_hammered(width, height, intensity, scale_factor=1.0):
        seed = random.randint(0, 1000000)
        # ⚡ RESOLUTION FIX: Leverage Rust engine with scaled dimensions
        scaled_w = int(width * scale_factor)
        scaled_h = int(height * scale_factor)

        img = _engine.generate_hammered(scaled_w, scaled_h, seed)
        if img:
            if scale_factor > 1.0:
                return img.resize((width, height), resample=Image.LANCZOS)
            return img

        # --- Python Fallback ---
        # ⚡ RESOLUTION FIX: Generate noise at higher resolution if scale_factor > 1.0
        noise_w = int(width * scale_factor)
        noise_h = int(height * scale_factor)

        base = Image.effect_noise((noise_w, noise_h), sigma=30)

        # Dimple frequency should also respect scale
        dimple_divisor = 20 / scale_factor
        dimples = Image.effect_noise((max(5, int(width // dimple_divisor)), max(5, int(height // dimple_divisor))), sigma=50)

        dimples = dimples.resize((noise_w, noise_h), resample=Image.BICUBIC)
        combined = ImageChops.multiply(base, dimples)

        # If we generated at higher res, downsample smoothly to target size
        if scale_factor > 1.0:
            return combined.resize((width, height), resample=Image.LANCZOS)
        return combined
