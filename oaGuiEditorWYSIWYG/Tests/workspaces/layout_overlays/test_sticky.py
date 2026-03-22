import unittest
import tkinter as tk
from unittest.mock import MagicMock
from oaGuiEditorWYSIWYG.workspaces.layout_overlays.sticky import StickyOverlay

class TestStickyOverlay(unittest.TestCase):

    def setUp(self):
        self.canvas = MagicMock(spec=tk.Canvas)
        self.overlay = StickyOverlay(self.canvas)

    def test_draw_sticky_arrows(self):
        """Test drawing arrows for sticky settings."""
        widget_info = {
            "id": "w1",
            "bbox": (10, 20, 110, 70),
            "grid_sticky": "nsew" # Sticky in all directions
        }
        
        self.overlay.draw(widget_info)
        
        # Expect 4 arrows (lines with arrowheads)
        self.assertEqual(self.canvas.create_line.call_count, 4)
        
        # Check one of the arrows, e.g., north
        args, kwargs = self.canvas.create_line.call_args_list[0]
        self.assertEqual(kwargs['arrow'], 'last')
        self.assertEqual(kwargs['tags'], 'sticky_overlay')
        
    def test_draw_for_no_sticky(self):
        widget_info = {
            "id": "w1",
            "bbox": (10, 20, 110, 70),
            "grid_sticky": "" # Not sticky
        }
        self.overlay.draw(widget_info)
        self.canvas.create_line.assert_not_called()

    def test_clear_sticky(self):
        self.overlay.clear()
        self.canvas.delete.assert_called_once_with('sticky_overlay')

if __name__ == '__main__':
    unittest.main()
