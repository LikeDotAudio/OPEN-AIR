# text/test_flux_plotter.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import unittest
from unittest.mock import MagicMock, patch
import tkinter as tk
import matplotlib
matplotlib.use('Agg')
from oaGuiElements.Core.graphing.graphing.dynamic_graph import FluxPlotter

class TestFluxPlotter(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.parent = tk.Frame(self.root)
        self.parent.pack()
        
        # Mock Context
        self.mock_context = MagicMock()
        self.mock_context.state_mirror_engine = MagicMock()
        self.mock_context.subscriber_router = MagicMock()
        self.mock_context.base_mqtt_topic_from_path = "OPEN-AIR/test"
        self.mock_context.builder_instance = MagicMock()
        
        self.config = {
            "path": "test/graph",
            "datasets": [
                {"id": "ds1", "label": "Dataset 1", "style": {"line_color": "red"}}
            ],
            "layout": {"width": 400, "height": 300}
        }

    def test_creation(self):
        """Verify that FluxPlotter initializes without error."""
        plotter = FluxPlotter(
            self.parent, 
            self.config, 
            "OPEN-AIR/test", 
            "test/graph",
            context=self.mock_context
        )
        self.assertIsInstance(plotter, FluxPlotter)
        self.assertIsNotNone(plotter.fig)
        self.assertIsNotNone(plotter.ax)
        self.assertIsNotNone(plotter.canvas)
        
        # Check if line was created
        self.assertIn("ds1", plotter.lines)
        
    def tearDown(self):
        self.root.destroy()

if __name__ == "__main__":
    unittest.main()
