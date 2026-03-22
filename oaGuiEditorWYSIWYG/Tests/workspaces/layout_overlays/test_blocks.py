import unittest
import tkinter as tk
from unittest.mock import MagicMock
from oaGuiEditorWYSIWYG.workspaces.layout_overlays.blocks import BlocksOverlay

class TestBlocksOverlay(unittest.TestCase):

    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.canvas = MagicMock(spec=tk.Canvas)
        self.overlay = BlocksOverlay(self.canvas)

    def tearDown(self):
        self.root.destroy()
        
    def test_draw_block_overlays(self):
        """Test drawing block outlines for all widgets in the tree."""
        # A simplified tree structure
        widget_tree = {
            "id": "root", "bbox": (0, 0, 400, 400),
            "children": [
                {"id": "child1", "bbox": (10, 10, 190, 50)},
                {"id": "child2", "bbox": (210, 10, 390, 50)}
            ]
        }
        
        self.overlay.draw(widget_tree)
        
        # Should draw a rectangle for each widget in the tree
        self.assertEqual(self.canvas.create_rectangle.call_count, 3)
        
        # Check the call for the root block
        args, kwargs = self.canvas.create_rectangle.call_args_list[0]
        self.assertEqual(args, (0,0,400,400))
        self.assertEqual(kwargs['tags'], 'block_overlay')
        
    def test_clear_blocks(self):
        """Test clearing the block overlays."""
        self.overlay.clear()
        self.canvas.delete.assert_called_once_with('block_overlay')

if __name__ == '__main__':
    unittest.main()
