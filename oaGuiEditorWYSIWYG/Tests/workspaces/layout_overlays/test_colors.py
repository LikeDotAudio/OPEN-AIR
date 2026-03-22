import unittest
import tkinter as tk
from unittest.mock import MagicMock
from oaGuiEditorWYSIWYG.workspaces.layout_overlays.colors import ColorsOverlay

class TestColorsOverlay(unittest.TestCase):

    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.canvas = MagicMock(spec=tk.Canvas)
        self.overlay = ColorsOverlay(self.canvas)

    def tearDown(self):
        self.root.destroy()
        
    def test_draw_color_swatches(self):
        """Test drawing color swatches next to widgets."""
        widget_tree = {
            "id": "root", "bbox": (0, 0, 400, 400), "background": "#ffffff",
            "children": [
                {"id": "child1", "bbox": (10, 10, 190, 50), "background": "#ff0000"},
                {"id": "child2", "bbox": (210, 10, 390, 50), "foreground": "#00ff00"}
            ]
        }
        
        self.overlay.draw(widget_tree)
        
        # Should draw a rectangle for each color property found
        self.assertEqual(self.canvas.create_rectangle.call_count, 3)
        
        # Check that the fill color was set correctly
        args, kwargs = self.canvas.create_rectangle.call_args_list[1] # child1
        self.assertEqual(kwargs['fill'], '#ff0000')
        self.assertEqual(kwargs['tags'], 'color_overlay')

    def test_clear_colors(self):
        """Test clearing the color swatches."""
        self.overlay.clear()
        self.canvas.delete.assert_called_once_with('color_overlay')

if __name__ == '__main__':
    unittest.main()
