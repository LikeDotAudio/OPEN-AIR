import unittest
from unittest.mock import MagicMock, patch
import tkinter as tk
from oaGuiElements.Core.faders.fader.fader import CustomFaderFrame, BuilderFaderCreator

class TestFader(unittest.TestCase):

    def setUp(self):
        try:
            self.root = tk.Tk()
            self.root.withdraw()
        except:
            self.root = MagicMock()
        self.variable = tk.DoubleVar(master=self.root, value=50.0)
        self.config = {'label_active': 'Test Fader', 'path': 'test/fader', 'value_min': 0, 'value_max': 100}
        self.mirror_engine = MagicMock()
        self.context = MagicMock()
        self.context.state_mirror_engine = self.mirror_engine
        self.context.base_mqtt_topic_from_path = 'test/topic'

    def test_fader_initialization(self):
        try:
            'Goal: Verify that CustomFaderFrame initializes correctly.'
            fader = CustomFaderFrame(master=self.root, variable=self.variable, config=self.config, path='test/fader', state_mirror_engine=self.mirror_engine, sync_callback=None)
            self.assertEqual(fader.path, 'test/fader', f"Expected 'test/fader', got '{fader.path}'")
            self.assertEqual(fader.min_val, 0.0, f"Expected 0.0, got '{fader.min_val}'")
            self.assertEqual(fader.max_val, 100.0, f"Expected 100.0, got '{fader.max_val}'")
        except Exception as e:
            self.fail(f'Test fader initialization crashed. Error: {str(e)}')

    def test_builder_creator_make(self):
        try:
            'Goal: Verify that BuilderFaderCreator creates a fader frame.'
            fader = BuilderFaderCreator.make(parent_widget=self.root, config_data=self.config, context=self.context)
            self.assertIsInstance(fader, CustomFaderFrame, f'Expected instance of CustomFaderFrame, got {type(fader)}')
        except Exception as e:
            self.fail(f'Test builder creator make crashed. Error: {str(e)}')

    def tearDown(self):
        if hasattr(self.root, 'destroy'):
            self.root.destroy()
if __name__ == '__main__':
    unittest.main()