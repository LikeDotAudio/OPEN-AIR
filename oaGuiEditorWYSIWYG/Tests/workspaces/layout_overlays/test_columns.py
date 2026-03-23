# -----------------------------------------------------------------
#
# THIS TEST IS DISABLED.
#
# The tests in this file are for a previous version of the code
# and are no longer compatible with the current implementation.
# They need to be rewritten.
#
# -----------------------------------------------------------------
#import unittest
#import tkinter as tk
#from unittest.mock import MagicMock
#from oaGuiEditorWYSIWYG.workspaces.layout_overlays.columns import ColumnsOverlay
#
#class TestColumnsOverlay(unittest.TestCase):
#
#    def setUp(self):
#        self.canvas = MagicMock(spec=tk.Canvas)
#        self.overlay = ColumnsOverlay(self.canvas)
#
#    def test_draw_column_guides(self):
#        """Test drawing column guides based on widget tree."""
#        widget_tree = {
#            "id": "root", "bbox": (0, 0, 400, 400),
#            "grid_columns": [0, 200, 400] # Example column definition
#        }
#        
#        self.overlay.draw(widget_tree)
#        
#        # Expect a line for each column boundary
#        self.assertEqual(self.canvas.create_line.call_count, 3)
#        args, kwargs = self.canvas.create_line.call_args_list[1]
#        self.assertEqual(args[0], 200) # x-coordinate of the second line
#        self.assertEqual(kwargs['tags'], 'column_guide')
#        
#    def test_clear_columns(self):
#        self.overlay.clear()
#        self.canvas.delete.assert_called_once_with('column_guide')
#
#if __name__ == '__main__':
#    unittest.main()
