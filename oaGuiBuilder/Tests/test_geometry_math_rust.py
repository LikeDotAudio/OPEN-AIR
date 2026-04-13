# oaGuiBuilder/Tests/test_geometry_math_rust.py
#
# Tests for the UI Geometry Math (Rust implementation).
#
# Author: Anthony Peter Kuzub
# Version: 20260401.1000.1

import unittest
from oaGuiBuilder.Core.ui_geometry_math import UIGeometryMath

class TestGeometryMathRust(unittest.TestCase):
    def test_rust_normalize_value(self):
        """Test value normalization via Rust."""
        try:
            from oaRustCore import oa_geometry_math_rs as oageometrymath_rs
        except ImportError:
            self.skipTest("Rust oageometrymath_rs not installed.")

        self.assertEqual(UIGeometryMath.normalize_value(50, 0, 100), 0.5)
        self.assertEqual(UIGeometryMath.normalize_value(0, 0, 100), 0.0)
        self.assertEqual(UIGeometryMath.normalize_value(100, 0, 100), 1.0)
        # Clamping isn't explicitly in the code but division would happen
        self.assertEqual(UIGeometryMath.normalize_value(150, 0, 100), 1.5)

    def test_rust_rotate_point(self):
        """Test point rotation via Rust."""
        try:
            from oaRustCore import oa_geometry_math_rs as oageometrymath_rs
        except ImportError:
            self.skipTest("Rust oageometrymath_rs not installed.")

        # Rotate (100, 0) by 90 degrees around (0, 0)
        # Should be approx (0, 100)
        nx, ny = UIGeometryMath.rotate_point(100, 0, 0, 0, 90)
        self.assertAlmostEqual(nx, 0.0, places=5)
        self.assertAlmostEqual(ny, 100.0, places=5)

    def test_rust_get_position(self):
        """Test polar to cartesian conversion via Rust."""
        try:
            from oaRustCore import oa_geometry_math_rs as oageometrymath_rs
        except ImportError:
            self.skipTest("Rust oageometrymath_rs not installed.")

        # 0 degrees, distance 100 -> (100, 0)
        x, y = UIGeometryMath.get_position(0, 100, 0, 0)
        self.assertAlmostEqual(x, 100.0, places=5)
        self.assertAlmostEqual(y, 0.0, places=5)

    def test_rust_get_angle(self):
        """Test cartesian to polar angle conversion via Rust."""
        try:
            from oaRustCore import oa_geometry_math_rs as oageometrymath_rs
        except ImportError:
            self.skipTest("Rust oageometrymath_rs not installed.")

        # Point (0, 100) from (0, 0) is 90 degrees
        angle = UIGeometryMath.get_angle(0, 100, 0, 0)
        self.assertAlmostEqual(angle, 90.0, places=5)

if __name__ == '__main__':
    unittest.main()
