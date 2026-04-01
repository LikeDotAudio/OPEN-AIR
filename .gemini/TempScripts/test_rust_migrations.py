# .gemini/TempScripts/test_rust_migrations.py
import sys
import os

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

def test_needle_geometry():
    print("Testing oaneedlegeometry_rs...")
    try:
        from oaneedlegeometry_rs import NeedleGeometry
        geo = NeedleGeometry()
        pts, smooth = geo.get_bezel_points(100, 100, 200, 200, "gem", 10, 0)
        print(f"✅ oaneedlegeometry_rs imported. Gem points count: {len(pts)}")
        
        config = {
            "val": 50, "min_val": 0, "max_val": 100,
            "start_angle_deg": 135, "end_angle_deg": 45, "extent_deg": 90,
            "main_arc_radius": 80, "text_offset_from_arc": 10,
            "style": "teardrop", "thick": 2, "counter_clockwise": False,
            "pivot_size": 10, "needle_scale": 1.0, "tag": "test"
        }
        shadow_geo = geo.calculate_shadow_geometry(100, 100, config)
        print(f"✅ calculate_shadow_geometry successful. Type: {shadow_geo.get('type')}")
    except Exception as e:
        print(f"❌ oaneedlegeometry_rs failed: {e}")

def test_cmdp_math():
    print("\nTesting oacmdpmath_rs...")
    try:
        from oacmdpmath_rs import CMDPMath
        math_rs = CMDPMath()
        config = {
            "center_x": 100, "center_y": 100, "track_length": 100,
            "angle": 0, "val_curr": 50, "val_min": 0, "val_max": 100,
            "rot_curr": 50, "hitbox_width": 40, "hitbox_padding": 10,
            "tick_count": 11, "tick_inner_offset": 10, "tick_outer_offset": 20,
            "cap_radius": 15, "global_center_x": 500, "global_center_y": 500,
            "far_radius": 200, "label_offset_base": 20, "label_offset_step": 10,
            "widget_id": 1
        }
        fader_geo = math_rs.calculate_fader_geometry(config)
        print(f"✅ oacmdpmath_rs imported. Hitbox points: {len(fader_geo['hitbox'])}")
    except Exception as e:
        print(f"❌ oacmdpmath_rs failed: {e}")

def test_disk_flusher():
    print("\nTesting oadiskflusher_rs...")
    try:
        from oadiskflusher_rs import DiskFlusher
        flusher = DiskFlusher()
        data = {"test_key": "test_val", "nested": {"a": 1, "b": [1, 2, 3]}}
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            tmp_path = tmp.name
        
        flusher.flush_async(data, tmp_path)
        print(f"✅ oadiskflusher_rs imported and flush_async called for {tmp_path}")
        # Give it a moment for the thread to write
        import time
        time.sleep(0.5)
        if os.path.exists(tmp_path):
            with open(tmp_path, "r") as f:
                content = f.read()
                print(f"✅ File written: {content[:50]}...")
            os.remove(tmp_path)
        else:
            print(f"❌ File NOT written: {tmp_path}")
    except Exception as e:
        print(f"❌ oadiskflusher_rs failed: {e}")

if __name__ == "__main__":
    test_needle_geometry()
    test_cmdp_math()
    test_disk_flusher()
