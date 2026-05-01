# Core/layer_scratches.py
# Author: Anthony Peter Kuzub
# Version: 20260402.0015.1
#
# Description: High-performance scratches using Rust.

import math
import random

from PIL import Image, ImageDraw

from oaGuiElements.Methods.pattern_engine import PatternEngine

_engine = PatternEngine()

class ScratchLayer:
    @staticmethod
    def generate_scratches(width, height, config):
        img = _engine.generate_scratches(width, height, config)
        if img:
            return img

        # --- Python Fallback ---
        layer = Image.new('RGBA', (width, height), (0,0,0,0))
        draw = ImageDraw.Draw(layer)
        s_int, s_width, count = float(config.get("intensity", 0.4)), int(config.get("width_px", 1)), int(config.get("count", 25))
        for _ in range(count):
            x1, y1 = random.randint(0, width - 1), random.randint(0, height - 1)
            length = random.randint(int(config.get("min_length_px", 20)), int(config.get("max_length_px", 150)))
            angle = random.uniform(0, 2 * math.pi)
            x2, y2 = x1 + length * math.cos(angle), y1 + length * math.sin(angle)
            draw.line((x1, y1, x2, y2), fill=(0, 0, 0, int(255 * s_int)), width=s_width)
            draw.line((x1+1, y1+1, x2+1, y2+1), fill=(255, 255, 255, int(255 * s_int * float(config.get("depth_highlight", 0.5)))), width=s_width)
        return layer
