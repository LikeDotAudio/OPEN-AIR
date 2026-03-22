import unittest
import tkinter as tk
from unittest.mock import MagicMock
from oaGuiEditorWYSIWYG.workspaces.layout_overlays.selection import SelectionOverlay

class TestSelectionOverlay(unittest.TestCase):

    def setUp(self):
        self.canvas = MagicMock(spec=tk.Canvas)
        self.overlay = SelectionOverlay(self.canvas)

    def test_draw_selection_highlight(self):
        """Test drawing a highlight around a selected widget."""
        selected_widget_info = {
            "id": "w1",
            "bbox": (10, 20, 110, 70)
        }
        
        self.overlay.draw(selected_widget_info)
        
        self.canvas.create_rectangle.assert_called_once_with(
            10, 20, 110, 70, 
            tags='selection_highlight',
            outline='red',
            width=2
        )
        
    def test_clear_selection(self):
        self.overlay.clear()
        self.canvas.delete.assert_called_once_with('selection_highlight')

if __name__ == '__main__':
    unittest.main()
