# Core/substrate_factory.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

from oaGuiBackground.Methods.pattern_engine import PatternEngine
import random

_engine = PatternEngine()

class SubstrateFactory:
    @staticmethod
    def generate_streaks(width, height, vertical=True, sigma=40):
        seed = random.randint(0, 1000000)
        return _engine.generate_streaks(width, height, vertical, float(sigma), seed)

    @staticmethod
    def generate_hammered(width, height, intensity):
        seed = random.randint(0, 1000000)
        return _engine.generate_hammered(width, height, seed)
