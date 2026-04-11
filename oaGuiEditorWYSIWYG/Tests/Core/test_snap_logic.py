# Tests/Core/test_snap_logic.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Unit tests for snap_logic utility.

import unittest
from oaGuiEditorWYSIWYG.Core.workspaces.Core.layout.snap_logic import snap_to_grid, snap_geometry

class TestSnapLogic(unittest.TestCase):
    def test_snap_to_grid(self):
        # Default grid 100
        self.assertEqual(snap_to_grid(49), 0)
        self.assertEqual(snap_to_grid(51), 100)
        self.assertEqual(snap_to_grid(149), 100)
        self.assertEqual(snap_to_grid(151), 200)
        
        # Custom grid 50
        self.assertEqual(snap_to_grid(24, 50), 0)
        self.assertEqual(snap_to_grid(26, 50), 50)

    def test_snap_geometry(self):
        geo = {"x": 12, "y": 88, "width": 145, "height": 210}
        snapped = snap_geometry(geo, 100)
        
        self.assertEqual(snapped["x"], 0)
        self.assertEqual(snapped["y"], 100)
        self.assertEqual(snapped["width"], 100)
        self.assertEqual(snapped["height"], 200)

        # Min size check
        geo_small = {"width": 10, "height": 10}
        snapped_small = snap_geometry(geo_small, 100)
        self.assertEqual(snapped_small["width"], 100)
        self.assertEqual(snapped_small["height"], 100)

if __name__ == '__main__':
    unittest.main()
