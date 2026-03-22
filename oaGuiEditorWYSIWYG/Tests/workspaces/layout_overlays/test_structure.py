import unittest
import tkinter as tk
from unittest.mock import MagicMock
from oaGuiEditorWYSIWYG.workspaces.layout_overlays.structure import StructureOverlay

class TestStructureOverlay(unittest.TestCase):

    def setUp(self):
        self.canvas = MagicMock(spec=tk.Canvas)
        self.overlay = StructureOverlay(self.canvas)

    def test_draw_parent_child_lines(self):
        """Test drawing lines connecting parents and children."""
        widget_tree = {
            "id": "root", "bbox": (100, 10, 300, 20),
            "children": [
                {"id": "child1", "bbox": (50, 50, 150, 60)},
                {"id": "child2", "bbox": (250, 50, 350, 60)}
            ]
        }
        
        self.overlay.draw(widget_tree)
        
        # Expect two lines, one for each child
        self.assertEqual(self.canvas.create_line.call_count, 2)
        
        # Check the line for the first child
        # from center of parent to center of child
        # parent center: (200, 15), child center: (100, 55)
        args, kwargs = self.canvas.create_line.call_args_list[0]
        self.assertEqual(args, (200.0, 15.0, 100.0, 55.0))
        self.assertEqual(kwargs['tags'], 'structure_overlay')
        
    def test_clear_structure(self):
        self.overlay.clear()
        self.canvas.delete.assert_called_once_with('structure_overlay')

if __name__ == '__main__':
    unittest.main()
