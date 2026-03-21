import unittest
from unittest.mock import MagicMock, patch
import tkinter as tk
from oaGuiElements.Core.faders.fader_bar_graph.fader_bar_graph import FaderWithBarGraphFrame, BuilderFaderBarGraphCreator

class TestFaderBarGraph(unittest.TestCase):

    def setUp(self):
        self.patchers = []
        try:
            self.root = tk.Tk()
            self.root.withdraw()
        except:
            self.root = MagicMock()
            self.root.winfo_exists.return_value = True
            self.patchers.append(patch('tkinter.DoubleVar', return_value=MagicMock()))
            mock_canvas = MagicMock()
            mock_canvas.winfo_exists.return_value = True
            self.patchers.append(patch('tkinter.Canvas', return_value=mock_canvas))
            for p in self.patchers:
                p.start()
        self.config = {'label_active': 'Test Fader Bar', 'path': 'test/fader_bar', 'value_min': -100, 'value_max': 0, 'layout': {'width': 100, 'height': 300}}
        self.mirror_engine = MagicMock()
        self.router = MagicMock()
        self.context = MagicMock()
        self.context.state_mirror_engine = self.mirror_engine
        self.context.subscriber_router = self.router
        self.context.base_mqtt_topic_from_path = 'test/topic'
        self.context.builder_instance = MagicMock()

    def test_fader_bar_graph_initialization(self):
        try:
            'Goal: Verify that FaderWithBarGraphFrame initializes correctly.'
            fader = FaderWithBarGraphFrame(master=self.root, config=self.config, path='test/fader_bar', state_mirror_engine=self.mirror_engine, subscriber_router=self.router, base_mqtt_topic='test/topic')
            self.assertEqual(fader.path, 'test/fader_bar', f"Expected 'test/fader_bar', got '{fader.path}'")
            self.assertEqual(fader.min_val, -100.0, f"Expected -100.0, got '{fader.min_val}'")
        except Exception as e:
            self.fail(f'Test fader bar graph initialization crashed. Error: {str(e)}')

    def test_builder_creator_make(self):
        try:
            'Goal: Verify that BuilderFaderBarGraphCreator creates a fader bar graph frame.'
            fader = BuilderFaderBarGraphCreator.make(parent_widget=self.root, config_data=self.config, context=self.context)
            self.assertIsNotNone(fader, 'Expected fader to be not None')
        except Exception as e:
            self.fail(f'Test builder creator make crashed. Error: {str(e)}')

    def tearDown(self):
        if hasattr(self, 'patchers'):
            for p in self.patchers:
                p.stop()
        if hasattr(self.root, 'destroy'):
            self.root.destroy()
if __name__ == '__main__':
    unittest.main()