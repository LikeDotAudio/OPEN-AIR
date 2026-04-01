import sys
import os
from PIL import Image

# Ensure the project root is in sys.path
sys.path.append("/home/anthony/Documents/OPEN-AIR")

from oaGuiBackground.Methods.pattern_engine import PatternEngine

def test_pattern_engine():
    engine = PatternEngine()
    
    print("Testing generate_streaks...")
    streaks = engine.generate_streaks(200, 200, True, 40.0, 1234)
    streaks.save(".gemini/test_streaks.png")
    print(f"Streaks saved to .gemini/test_streaks.png (Size: {streaks.size})")
    
    print("Testing generate_hammered...")
    hammered = engine.generate_hammered(200, 200, 1234)
    hammered.save(".gemini/test_hammered.png")
    print(f"Hammered saved to .gemini/test_hammered.png (Size: {hammered.size})")
    
    print("Testing generate_screw...")
    config = {"type": "fillister", "angle": 45.0, "damage": 0.5, "rust": 0.2}
    screw = engine.generate_screw(64, config)
    screw.save(".gemini/test_screw.png")
    print(f"Screw saved to .gemini/test_screw.png (Size: {screw.size})")
    
    print("✅ SUCCESS: Pattern Engine tests complete.")

if __name__ == "__main__":
    test_pattern_engine()
