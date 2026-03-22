import unittest
import tkinter as tk
from unittest.mock import MagicMock
from oaGuiEditorWYSIWYG.workspaces.layout_overlays.sizing import SizingOverlay

class TestSizingOverlay(unittest.TestCase):

    def setUp(self):
        self.canvas = MagicMock(spec=tk.Canvas)
        self.overlay = SizingOverlay(self.canvas)
        self.canvas.winfo_width.return_value = 500
        self.canvas.winfo_height.return_value = 500

    def test_draw_sizing_info(self):
        """Test drawing sizing information (width/height) for a widget."""
        widget_info = {
            "id": "w1",
            "bbox": (10, 20, 110, 70) # width=100, height=50
        }
        
        self.overlay.draw(widget_info)
        
        # Expects to draw text labels for width and height
        self.assertEqual(self.canvas.create_text.call_count, 2)
        
        # Check the width label
        args, kwargs = self.canvas.create_text.call_args_list[0]
        self.assertIn("100px", args)
        self.assertEqual(kwargs['tags'], 'sizing_info')
        
    def test_clear_sizing(self):
        self.overlay.clear()
        self.canvas.delete.assert_called_once_with('sizing_info')

if __name__ == '__main__':
    unittest.main()
