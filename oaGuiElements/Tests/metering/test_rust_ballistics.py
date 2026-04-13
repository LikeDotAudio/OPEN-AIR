# oaGuiElements/Tests/metering/test_rust_ballistics.py
#
# Tests for the BallisticsEngine (Rust implementation).
#
# Author: Anthony Peter Kuzub
# Version: 20260401.1000.1

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

    def test_rust_ballistics_initialization(self):
        """Test that BallisticsEngine initializes the Rust core."""
        try:
            from oaRustCore import oa_metering_engine_rs as oameteringengine_rs
        except ImportError:
            self.skipTest("Rust oameteringengine_rs not installed.")

        engine = BallisticsEngine(self.config)
        self.assertIsNotNone(engine.rust_engine)

    def test_rust_ballistics_movement(self):
        """Test movement through the Rust-backed BallisticsEngine."""
        try:
            from oaRustCore import oa_metering_engine_rs as oameteringengine_rs
        except ImportError:
            self.skipTest("Rust oameteringengine_rs not installed.")

        engine = BallisticsEngine(self.config)
        
        target = 6.0
        engine.set_target(target)
        
        # Step through time
        dt = 20.0 # 20ms steps
        for _ in range(10):
            engine.update(dt)
            self.assertIsInstance(engine.current_value, float)
            self.assertIsInstance(engine.peak_value, float)
            self.assertIsInstance(engine.overload_fade, float)

if __name__ == "__main__":
    unittest.main()
