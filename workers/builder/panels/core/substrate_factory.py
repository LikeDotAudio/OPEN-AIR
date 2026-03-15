from PIL import Image, ImageChops
import random

class SubstrateFactory:
    @staticmethod
    def generate_streaks(width, height, vertical=True, sigma=40):
        source = Image.effect_noise((width, max(5, height // 100)) if vertical else (max(5, width // 100), height), sigma=sigma)
        return source.resize((width, height), resample=Image.LANCZOS)

    @staticmethod
    def generate_hammered(width, height, intensity):
        base = Image.effect_noise((width, height), sigma=30)
        dimples = Image.effect_noise((width // 20, height // 20), sigma=50).resize((width, height), resample=Image.BICUBIC)
        return ImageChops.multiply(base, dimples)
