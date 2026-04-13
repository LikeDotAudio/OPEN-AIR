# /home/anthony/Documents/OPEN-AIR/oaGui/Tests/test_batch_processing.py
# Author: Gemini (Collaborator)
# Version: 20260405.2340.1
#
# Description: Unit tests for BatchProcessingEngine - Verifying Fast Render & Padding

import unittest
from unittest.mock import MagicMock, patch
import tkinter as tk
from oaGui.Core.batch_processing_engine import BatchProcessingEngine

class TestBatchProcessingEngine(unittest.TestCase):

    def setUp(self):
        """Set up Tkinter root and mock builder."""
        self.root = tk.Tk()
        self.parent = tk.Frame(self.root)
        self.parent.pack()
        
        self.mock_logger = MagicMock()
        self.mock_builder = MagicMock()
        self.mock_builder.widget_factory = MagicMock()
        self.mock_builder._render_tier = "high_res"
        self.mock_builder.superficial_pad = 0
        
        self.engine = BatchProcessingEngine(self.mock_builder, self.mock_logger, local_debug=True)

    def tearDown(self):
        """Destroy widgets."""
        self.root.destroy()

    def test_fast_render_placeholders(self):
        """Verify that 'fast' render tier creates sized Frame placeholders instead of full widgets."""
        # BUILD: Set fast mode and define a widget with explicit geometry
        self.mock_builder._render_tier = "fast"
        widgets = [{
            "path": "test.path.button",
            "r": 0, "c": 0, "padx": 5, "pady": 5, "sticky": "nsew",
            "value": {
                "type": "OcaButton",
                "geometry": {"width": 150, "height": 80}
            }
        }]
        
        state = {"pending": 1, "loop_done": False}
        on_done = MagicMock()
        
        # OPERATE: Process the chunk
        # Note: process uses parent.after(1, ...) for remaining chunks, but we only have one item
        self.engine.process(self.parent, widgets, chunk_size=1, context={}, state=state, on_done=on_done)
        
        # CHECK: A child widget should have been created in the parent
        children = self.parent.winfo_children()
        self.assertEqual(len(children), 1)
        
        placeholder = children[0]
        self.assertIsInstance(placeholder, tk.Frame)
        
        # CHECK: Size should match configuration (requires update() to process geometry, or check config)
        # We check the internal config values since we don't have a real X server processing layout in CI usually
        self.assertEqual(int(placeholder.cget("width")), 150)
        self.assertEqual(int(placeholder.cget("height")), 80)
        
        # CHECK: Grid info (internal layout)
        grid_info = placeholder.grid_info()
        self.assertEqual(int(grid_info["row"]), 0)
        self.assertEqual(int(grid_info["column"]), 0)
        self.assertEqual(placeholder._oca_path, "test.path.button")

    def test_superficial_padding(self):
        """Verify that superficial_pad is added to the grid padx/pady."""
        self.mock_builder._render_tier = "fast"
        self.mock_builder.superficial_pad = 10 # Add 10px padding
        
        widgets = [{
            "path": "test.pad",
            "r": 1, "c": 1, "padx": 5, "pady": 2, "sticky": "",
            "value": {"type": "OcaLabel"}
        }]
        
        state = {"pending": 1, "loop_done": False}
        self.engine.process(self.parent, widgets, chunk_size=1, context={}, state=state, on_done=MagicMock())
        
        placeholder = self.parent.winfo_children()[0]
        grid_info = placeholder.grid_info()
        
        # CHECK: padx = 5 (original) + 10 (superficial) = 15
        # CHECK: pady = 2 (original) + 10 (superficial) = 12
        # Note: grid_info returns values as strings or objects depending on version
        self.assertEqual(int(grid_info["padx"]), 15)
        self.assertEqual(int(grid_info["pady"]), 12)

    def test_high_res_render_calls_factory(self):
        """Verify that 'high_res' render tier uses the widget factory."""
        self.mock_builder._render_tier = "high_res"
        
        mock_widget = tk.Frame(self.parent)
        self.mock_builder.widget_factory.get.return_value = MagicMock(return_value=mock_widget)
        
        widgets = [{
            "path": "test.real",
            "r": 0, "c": 0, "padx": 0, "pady": 0, "sticky": "",
            "value": {"type": "FunctionalWidget"}
        }]
        
        state = {"pending": 1, "loop_done": False}
        self.engine.process(self.parent, widgets, chunk_size=1, context={}, state=state, on_done=MagicMock())
        
        # CHECK: Factory was queried and creator was called
        self.mock_builder.widget_factory.get.assert_called_with("FunctionalWidget")
        self.assertTrue(self.mock_builder.widget_factory.get.return_value.called)

if __name__ == '__main__':
    unittest.main()
