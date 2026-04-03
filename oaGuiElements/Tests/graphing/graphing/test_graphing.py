# graphing/test_graphing.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import unittest
from unittest.mock import MagicMock, patch
import tkinter as tk
import matplotlib
matplotlib.use('Agg')
import os
from oaGuiElements.Core.graphing.graphing.dynamic_graph import GraphPlotter
from oaGuiElements.Tests.utils.test_utils import load_sample_config

class TestGraphPlotter(unittest.TestCase):

    def setUp(self):
        self.patchers = []
        try:
            self.root = tk.Tk()
            self.root.withdraw()
        except:
            self.root = MagicMock()
            self.root.winfo_exists.return_value = True
            self.patchers.append(patch('tkinter.StringVar', return_value=MagicMock()))
            self.patchers.append(patch('tkinter.Canvas', return_value=MagicMock()))
            self.patchers.append(patch('tkinter.Frame', return_value=MagicMock()))
            mock_canvas_agg = MagicMock()
            self.patchers.append(patch('oaGuiElements.Core.graphing.graphing.graph.FigureCanvasTkAgg', return_value=mock_canvas_agg))
            for p in self.patchers:
                p.start()
        component_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'Core', 'graphing', 'graphing')
        full_sample = load_sample_config(component_dir)
        self.config = full_sample.get('blocks', {}).get('multi_dataset_graph', {})
        self.config['path'] = 'test/graph'
        self.mock_context = MagicMock()
        self.mock_context.state_mirror_engine = MagicMock()
        self.mock_context.subscriber_router = MagicMock()
        self.mock_context.base_mqtt_topic_from_path = 'OPEN-AIR/test'
        self.mock_context.builder_instance = MagicMock()

    def test_creation(self):
        try:
            'Verify that GraphPlotter initializes correctly from sample.json.'
            plotter = GraphPlotter(self.root, self.config, 'OPEN-AIR/test', 'test/graph', context=self.mock_context, state_mirror_engine=self.mock_context.state_mirror_engine, subscriber_router=self.mock_context.subscriber_router)
            
            # ⚡ FORCE SYNC: Ensure scheduled updates (which create lines) run immediately
            plotter._perform_scheduled_update()
            
            self.assertIsInstance(plotter, GraphPlotter, f'Expected instance of GraphPlotter, got {type(plotter)}')
            self.assertIsNotNone(plotter.fig, 'Expected plotter.fig to be not None')
            self.assertIsNotNone(plotter.ax, 'Expected plotter.ax to be not None')
            self.assertIsNotNone(plotter.canvas, 'Expected plotter.canvas to be not None')
            self.assertIn('ref_linear', plotter.lines)
            self.assertIn('sig_a', plotter.lines)
            self.assertIn('sig_b', plotter.lines)
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
