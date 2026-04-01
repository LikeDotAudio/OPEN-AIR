# oaGuiElements/Tests/metering/test_rust_ballistics.py
#
# Tests for the BallisticsEngine (Python vs Rust).
#
# Author: Anthony Peter Kuzub
# Version: 20260331.1710.1

import unittest
from unittest.mock import MagicMock, patch
from oaGuiElements.Core.metering.meter_bar.Core.ballistics import BallisticsEngine

class MockMeterConfig:
    def __init__(self):
        self.min_val = -60.0
        self.max_val = 12.0
        self.value_default = -60.0
        self.hold_time = 500.0
        self.dwell_time = 100.0
        self.attack_ms = 5.0
        self.release_ms = 300.0
        self.fall_time = 1000.0
        self.peak_display = True
        self.peak_hold_time = 1500.0
        self.peak_display_fall_time = 3000.0
        self.show_peak_hold = True
        self.upper_range = 0.0
        self.overload_fade_time = 1000.0

class TestRustBallistics(unittest.TestCase):
    def setUp(self):
        self.config = MockMeterConfig()

    @patch("oaConfiguration.Entry.Config.get_boolean")
    def test_compare_python_vs_rust_ballistics(self, mock_get_boolean):
        # 1. Test Python
        mock_get_boolean.return_value = False
        engine_py = BallisticsEngine(self.config)
        self.assertIsNone(engine_py.rust_engine)
        
        # 2. Test Rust
        mock_get_boolean.return_value = True
        try:
            import oameteringengine_rs
            engine_rs = BallisticsEngine(self.config)
            self.assertIsNotNone(engine_rs.rust_engine)
        except ImportError:
            self.skipTest("Rust oameteringengine_rs not installed.")

        # 3. Simulate movement
        target = 6.0
        engine_py.set_target(target)
        engine_rs.set_target(target)
        
        # Step through time
        dt = 20.0 # 20ms steps
        for _ in range(10):
            res_py = engine_py.update(dt)
            res_rs = engine_rs.update(dt)
            
            # Compare (current_val, peak_val, overload_fade_factor, is_running, reached_min)
            # Use delta for floats due to potential timing/precision differences
            self.assertAlmostEqual(res_py[0], res_rs[0], places=5)
            self.assertAlmostEqual(res_py[1], res_rs[1], places=5)
            self.assertAlmostEqual(res_py[2], res_rs[2], places=5)
            self.assertEqual(res_py[3], res_rs[3])
            self.assertEqual(res_py[4], res_rs[4])

if __name__ == "__main__":
    unittest.main()
