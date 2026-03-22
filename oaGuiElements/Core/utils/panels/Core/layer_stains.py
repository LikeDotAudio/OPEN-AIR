# Core/layer_stains.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

from PIL import Image, ImageDraw, ImageFilter
import random
from oaGuiElements.Methods.utils import PanelUtils

class StainsLayer:
    @staticmethod
    def generate_stains(width, height, config):
        layer = Image.new('RGBA', (width, height), (0,0,0,0))
        draw = ImageDraw.Draw(layer)
        color = PanelUtils.hex_to_rgb(config.get("color", "#0d0d0d"))
        opacity, spread, count = float(config.get("opacity", 0.4)), int(config.get("stain_spread", 40)), int(config.get("stain_count", 5))
        for _ in range(count):
            sx, sy = random.randint(0, width - 1), random.randint(0, height - 1)
            sr = random.randint(spread // 2, spread)
            draw.ellipse((sx-sr, sy-sr, sx+sr, sy+sr), fill=color + (int(255 * opacity),))
        return layer.filter(ImageFilter.GaussianBlur(radius=spread/2))
