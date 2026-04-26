import sys

sys.path.insert(0, '/home/anthony/Documents/OPEN-AIR')
from oaGuiElements.Methods.rotary_core import RotaryCore

core = RotaryCore()
points = core.get_gear_points(100, 100, 50, 8, 0.15, 0)
print(f"Points type: {type(points)}")
print(f"Points length: {len(points)}")
print(f"Points sample: {points[:10] if points else points}")
