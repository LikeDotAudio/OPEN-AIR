# Core/substrate_factory.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import random

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
        if img and scale_factor > 1.0:
            return img.resize((width, height), resample=Image.LANCZOS)
        return img

    @staticmethod
    def generate_hammered(width, height, intensity, scale_factor=1.0):
        seed = random.randint(0, 1000000)
        # ⚡ RESOLUTION FIX: Leverage Rust engine with scaled dimensions
        scaled_w = int(width * scale_factor)
        scaled_h = int(height * scale_factor)

        img = _engine.generate_hammered(scaled_w, scaled_h, seed)
        if img and scale_factor > 1.0:
            return img.resize((width, height), resample=Image.LANCZOS)
        return img
