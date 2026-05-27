# graphing/test_flux_plotter.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import tkinter as tk
import unittest
from unittest.mock import MagicMock, patch

import matplotlib

matplotlib.use('Agg')
from oaGuiElements.Core.graphing.Methods.dynamic_graph import GraphPlotter


class TestGraphPlotter(unittest.TestCase):

    def setUp(self):
        self.patchers = []
        try:
            self.root = tk.Tk()
            self.root.withdraw()
        except:
            self.root = MagicMock()
            self.root.winfo_exists.return_value = True
            self.root.winfo_width.return_value = 400
            self.root.winfo_height.return_value = 300
            self.root.cget.return_value = '#2b2b2b'
            mock_var = MagicMock()
            self.patchers.append(patch('tkinter.StringVar', return_value=mock_var))
            self.patchers.append(patch('tkinter.DoubleVar', return_value=mock_var))
            self.patchers.append(patch('tkinter.BooleanVar', return_value=mock_var))
            mock_frame = MagicMock()
            mock_frame.winfo_exists.return_value = True
            self.patchers.append(patch('tkinter.Frame', return_value=mock_frame))
            mock_canvas_agg = MagicMock()
            self.patchers.append(patch('oaGuiElements.Core.graphing.graph.FigureCanvasTkAgg', return_value=mock_canvas_agg))
            for p in self.patchers:
                p.start()
        if isinstance(self.root, MagicMock):
            self.parent = MagicMock()
            self.parent.winfo_exists.return_value = True
        else:
            self.parent = tk.Frame(self.root)
            self.parent.pack()
        self.mock_context = MagicMock()
        self.mock_context.state_mirror_engine = MagicMock()
        self.mock_context.subscriber_router = MagicMock()
        self.mock_context.base_mqtt_topic_from_path = 'OpenAir/test'
        self.mock_context.builder_instance = MagicMock()
        self.config = {'path': 'test/graph', 'datasets': [{'id': 'ds1', 'label': 'Dataset 1', 'style': {'line_color': 'red'}}], 'layout': {'width': 400, 'height': 300}}

    def test_creation(self):
        try:
            'Verify that GraphPlotter initializes without error.'
            plotter = GraphPlotter(self.parent, self.config, 'OpenAir/test', 'test/graph', context=self.mock_context, state_mirror_engine=self.mock_context.state_mirror_engine, subscriber_router=self.mock_context.subscriber_router)
            self.assertIsInstance(plotter, GraphPlotter, f'Expected instance of GraphPlotter, got {type(plotter)}')
            self.assertIsNotNone(plotter.fig, 'Expected plotter.fig to be not None')
            self.assertIsNotNone(plotter.ax, 'Expected plotter.ax to be not None')
            self.assertIsNotNone(plotter.canvas, 'Expected plotter.canvas to be not None')
            self.assertIn('ds1', plotter.lines)
        except Exception as e:
            self.fail(f'Test creation crashed. Error: {str(e)}')

    def tearDown(self):
        if hasattr(self, 'patchers'):
            for p in self.patchers:
                p.stop()
        if hasattr(self.root, 'destroy'):
            self.root.destroy()
if __name__ == '__main__':
    unittest.main()
