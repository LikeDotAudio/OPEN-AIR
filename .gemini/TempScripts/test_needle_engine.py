import sys
sys.path.append("/home/anthony/Documents/OPEN-AIR")

from oaGuiElements.Methods.needle_engine import NeedleEngine

def test_needle_engine():
    engine = NeedleEngine()
    
    config = {
        "val": 50.0,
        "min_val": 0.0,
        "max_val": 100.0,
        "start_angle_deg": 135.0,
        "end_angle_deg": 45.0,
        "extent_deg": 90.0,
        "main_arc_radius": 100.0,
        "text_offset_from_arc": 10.0,
        "color": "red",
        "style": "taper",
        "thick": 2.0,
        "counter_clockwise": False,
        "pivot_size": 10.0,
        "needle_scale": 1.0,
        "tag": "test_needle"
    }

    print("Calculating geometry...")
    geom = engine.calculate_geometry(150.0, 150.0, config)
    print(f"Result: {geom}")
    
    if geom and geom.get("draw_type") == "polygon" and len(geom.get("coords")) == 6:
        print("✅ SUCCESS: Needle Engine geometry calculated correctly.")
    else:
        print("❌ FAILURE: Geometry mismatch.")

if __name__ == "__main__":
    test_needle_engine()
